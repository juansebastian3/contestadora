"""Webhooks de Twilio para manejo de llamadas de voz.

3 MODOS DE ASISTENTE (alineados con planes):
─────────────────────────────────────────────────────────────────
  ASISTENTE_BASICO (Free):
    Polly saluda: "Hola, soy la asistente de {nombre}..."
    IA solo ESCUCHA y transcribe. No conversa.
    Post-llamada: análisis + resumen WhatsApp.

  CONTESTADORA (Pro):
    Tu voz grabada como saludo.
    Para desconocidos: Polly saluda (como Free).
    Para conocidos en modo Luna: tu voz saluda.
    IA solo ESCUCHA. No conversa.

  SECRETARIA_IA (Premium):
    Tu voz grabada como saludo + IA conversa como secretaria.
    Consulta calendario, agenda reuniones, gestiona horarios.
    Conversación completa con GPT-4o-mini.
─────────────────────────────────────────────────────────────────
"""
import logging
from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather

from app.core.config import settings
from app.services.call_manager import call_manager
from app.services.llm_service import analizar_llamada
from app.services.whatsapp_service import enviar_resumen_llamada, enviar_alerta_llamada_entrante
from app.services.filtrado_service import decidir_filtrado
from app.models.database import (
    SessionLocal, Llamada, Usuario, EstadoLlamada, ModoAsistente, PlanTipo
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/voice", tags=["Twilio Webhooks"])


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _obtener_usuario_por_numero_twilio(numero_destino: str) -> Usuario | None:
    db = SessionLocal()
    try:
        return db.query(Usuario).filter(
            Usuario.telefono_twilio == numero_destino
        ).first()
    finally:
        db.close()


def _get_voice_params(usuario: Usuario | None) -> dict:
    """Retorna parámetros de voz Polly para TTS."""
    if usuario and usuario.voz_polly_id:
        return {"language": "es-CL", "voice": usuario.voz_polly_id}
    return {"language": "es-CL", "voice": "Polly.Mia"}


def _construir_saludo_basico(usuario: Usuario | None) -> str:
    """Saludo estándar para modo Free (Polly habla)."""
    nombre_owner = (usuario.nombre if usuario else None) or settings.OWNER_NAME
    return (
        f"Hola, soy la asistente de {nombre_owner}. "
        f"Por favor, dime tu nombre y cuál es el recado que quieres dejar. "
        f"Le haré llegar tu mensaje."
    )


def _construir_system_prompt_secretaria(usuario: Usuario | None, evento_calendario: dict = None) -> str:
    """System prompt para modo Premium (secretaria IA que conversa)."""
    nombre_asistente = (usuario.nombre_asistente if usuario else None) or "Sofía"
    nombre_owner = (usuario.nombre if usuario else None) or settings.OWNER_NAME

    base = (
        f"Eres {nombre_asistente}, la secretaria personal de {nombre_owner}.\n\n"
        "TU ROL: Secretaria telefónica profesional que CONVERSA con el llamante.\n\n"
        "CAPACIDADES:\n"
        "- Tomar recados completos (nombre, motivo, urgencia)\n"
        "- Informar disponibilidad basada en el calendario\n"
        "- Ofrecer agendar una reunión o devolución de llamada\n"
        "- Filtrar spam con cortesía\n\n"
        "REGLAS:\n"
        f"- NUNCA digas 'contacta a {nombre_owner} directamente' — ESO ES LO QUE YA ESTÁN HACIENDO.\n"
        "- Si es spam/marketing: 'Gracias, pero no nos interesa. Que le vaya bien.'\n"
        f"- Si es importante: 'Le paso tu mensaje a {nombre_owner}. ¿Quieres que agende una llamada de vuelta?'\n"
        "- Máximo 2-3 oraciones por respuesta. Tono profesional y cercano."
    )

    if evento_calendario:
        titulo = evento_calendario.get("titulo", "una reunión")
        base += (
            f"\n\nCALENDARIO: {nombre_owner} está en '{titulo}' ahora. "
            f"Puedes mencionarlo: '{nombre_owner} está en una reunión, pero apenas termine le paso tu mensaje.'"
        )

    if usuario and usuario.prompt_personalizado:
        base += f"\n\nINSTRUCCIONES DEL DUEÑO:\n{usuario.prompt_personalizado}"

    return base


def _determinar_modo_asistente(usuario: Usuario | None, numero_conocido: bool) -> str:
    """Determina el modo de asistente según el plan y contexto.

    Free → siempre ASISTENTE_BASICO (Polly saluda, IA escucha)
    Pro  → desconocidos: ASISTENTE_BASICO | conocidos/luna: CONTESTADORA (tu voz)
    Premium → siempre SECRETARIA_IA (tu voz + IA conversa)
    """
    if not usuario:
        return ModoAsistente.ASISTENTE_BASICO.value

    plan = usuario.plan or PlanTipo.FREE.value

    if plan == PlanTipo.PREMIUM.value:
        return ModoAsistente.SECRETARIA_IA.value
    elif plan == PlanTipo.PRO.value:
        # Pro: si tiene audio grabado y es conocido o modo luna → su voz
        if usuario.audio_saludo_url and numero_conocido:
            return ModoAsistente.CONTESTADORA.value
        # Pro desconocidos o sin audio → Polly básico
        return ModoAsistente.ASISTENTE_BASICO.value
    else:
        # Free: siempre básico
        return ModoAsistente.ASISTENTE_BASICO.value


# ═══════════════════════════════════════════════════════════
# WEBHOOK PRINCIPAL: INCOMING
# ═══════════════════════════════════════════════════════════

@router.api_route("/incoming", methods=["GET", "POST"])
async def contestar_llamada(request: Request):
    """Webhook principal. Identifica usuario, decide filtrado y modo."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    numero_origen = form_data.get("From", "Desconocido")
    numero_destino = form_data.get("To", "")
    base_url = str(request.base_url).rstrip("/")

    logger.info(f"Llamada: {call_sid} | {numero_origen} -> {numero_destino}")

    # 1. IDENTIFICAR USUARIO por su número Twilio
    usuario = _obtener_usuario_por_numero_twilio(numero_destino)

    # 2. DECIDIR FILTRADO
    debe_filtrar = True
    modo_activo = "desconocidos"
    numero_conocido = False
    evento_calendario = None

    if usuario:
        resultado = decidir_filtrado(usuario, numero_origen)
        debe_filtrar = resultado.debe_filtrar
        modo_activo = resultado.modo_activo
        numero_conocido = resultado.numero_conocido
        evento_calendario = resultado.evento_calendario
        logger.info(f"Filtrado: {resultado.motivo}")

        if not debe_filtrar:
            respuesta = VoiceResponse()
            respuesta.dial(usuario.telefono)
            return Response(content=str(respuesta), media_type="application/xml")

    # 3. REGISTRAR LLAMADA
    call_manager.iniciar_llamada(call_sid, numero_origen)

    db = SessionLocal()
    try:
        llamada_db = Llamada(
            call_sid=call_sid,
            numero_origen=numero_origen,
            usuario_id=usuario.id if usuario else None,
            estado=EstadoLlamada.EN_CURSO.value,
            fue_filtrada=True,
            numero_conocido=numero_conocido,
            modo_activo=modo_activo,
        )
        db.add(llamada_db)
        db.commit()
    except Exception as e:
        logger.error(f"Error guardando llamada: {e}")
        db.rollback()
    finally:
        db.close()

    enviar_alerta_llamada_entrante(numero_origen)

    # 4. ELEGIR MODO SEGÚN PLAN Y CONTEXTO
    modo = _determinar_modo_asistente(usuario, numero_conocido)
    logger.info(f"Modo: {modo} | Plan: {usuario.plan if usuario else 'ninguno'}")

    if modo == ModoAsistente.SECRETARIA_IA.value:
        return _responder_secretaria_ia(usuario, base_url, evento_calendario)
    elif modo == ModoAsistente.CONTESTADORA.value:
        return _responder_contestadora(usuario, base_url, evento_calendario)
    else:
        return _responder_asistente_basico(usuario, base_url)


# ═══════════════════════════════════════════════════════════
# MODO 1: ASISTENTE BÁSICO (Free + Pro desconocidos)
# Polly saluda, IA solo escucha
# ═══════════════════════════════════════════════════════════

def _responder_asistente_basico(usuario: Usuario | None, base_url: str) -> Response:
    """Polly dice el saludo estándar, luego solo escucha el recado."""
    respuesta = VoiceResponse()
    respuesta.pause(length=1)

    saludo = _construir_saludo_basico(usuario)
    voice_params = _get_voice_params(usuario)

    # Saludo con Polly
    gather = Gather(
        input="speech",
        action="/webhooks/voice/escuchar-recado",
        language="es-CL",
        speech_timeout=5,
        timeout=10,
    )
    gather.say(saludo, **voice_params)
    respuesta.append(gather)

    # Si no hablan
    respuesta.say("No se recibio mensaje. Adios.", **voice_params)

    return Response(content=str(respuesta), media_type="application/xml")


# ═══════════════════════════════════════════════════════════
# MODO 2: CONTESTADORA (Pro conocidos / modo luna)
# Tu voz grabada, IA solo escucha
# ═══════════════════════════════════════════════════════════

def _responder_contestadora(usuario: Usuario | None, base_url: str, evento_calendario: dict = None) -> Response:
    """Reproduce el audio grabado del usuario, luego solo escucha."""
    respuesta = VoiceResponse()
    respuesta.pause(length=1)

    if usuario and usuario.audio_saludo_url:
        audio_url = usuario.audio_saludo_url
        if not audio_url.startswith("http"):
            audio_url = f"{base_url}{audio_url}"
        respuesta.play(audio_url)
    else:
        # Fallback a Polly si no hay audio grabado
        nombre = (usuario.nombre if usuario else None) or settings.OWNER_NAME
        voice_params = _get_voice_params(usuario)
        saludo = (
            f"Hola, soy {nombre}. No puedo atender en este momento. "
            "Por favor, deja tu nombre y el motivo de tu llamada. "
            "Te devuelvo el llamado apenas pueda. Gracias."
        )
        respuesta.say(saludo, **voice_params)

    # Solo escuchar el recado (IA no habla)
    gather = Gather(
        input="speech",
        action="/webhooks/voice/escuchar-recado",
        language="es-CL",
        speech_timeout=5,
        timeout=10,
    )
    respuesta.append(gather)

    respuesta.say("No se recibio mensaje. Adios.", language="es-CL", voice="Polly.Mia")

    return Response(content=str(respuesta), media_type="application/xml")


# ═══════════════════════════════════════════════════════════
# MODO 3: SECRETARIA IA (Premium)
# Tu voz saluda + IA conversa como secretaria
# ═══════════════════════════════════════════════════════════

def _responder_secretaria_ia(usuario: Usuario | None, base_url: str, evento_calendario: dict = None) -> Response:
    """Tu voz saluda, luego la IA conversa como secretaria."""
    respuesta = VoiceResponse()
    respuesta.pause(length=1)

    if usuario and usuario.audio_saludo_url:
        audio_url = usuario.audio_saludo_url
        if not audio_url.startswith("http"):
            audio_url = f"{base_url}{audio_url}"
        respuesta.play(audio_url)
    else:
        # Si no tiene audio, la IA saluda directamente
        nombre_asistente = (usuario.nombre_asistente if usuario else None) or "Sofia"
        nombre_owner = (usuario.nombre if usuario else None) or settings.OWNER_NAME
        voice_params = _get_voice_params(usuario)

        if evento_calendario:
            saludo = (
                f"Hola, soy {nombre_asistente}, secretaria de {nombre_owner}. "
                f"En este momento esta en una reunion. "
                "¿Con quien hablo y en que puedo ayudarte?"
            )
        else:
            saludo = (
                f"Hola, soy {nombre_asistente}, secretaria de {nombre_owner}. "
                f"En este momento no puede atender. "
                "¿Con quien hablo y en que puedo ayudarte?"
            )
        respuesta.say(saludo, **voice_params)

    # La IA conversa
    gather = Gather(
        input="speech",
        action="/webhooks/voice/secretaria-procesar",
        language="es-CL",
        speech_timeout="auto",
        timeout=5,
    )
    respuesta.append(gather)

    respuesta.say(
        "No pude escuchar nada. Que tengas buen dia, adios.",
        **_get_voice_params(usuario),
    )

    return Response(content=str(respuesta), media_type="application/xml")


# ═══════════════════════════════════════════════════════════
# ESCUCHAR RECADO (Free + Pro: IA no habla)
# ═══════════════════════════════════════════════════════════

@router.api_route("/escuchar-recado", methods=["GET", "POST"])
async def escuchar_recado(request: Request, SpeechResult: str = Form("")):
    """Recibe lo que dijo el llamante. IA NO responde. Solo transcribe.

    Sigue escuchando por si quieren agregar algo más.
    Usado por ASISTENTE_BASICO y CONTESTADORA.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")

    logger.info(f"[{call_sid}] Recado: {SpeechResult}")

    conv = call_manager.obtener_llamada(call_sid)
    if not conv:
        conv = call_manager.iniciar_llamada(call_sid)

    conv.agregar_mensaje_usuario(SpeechResult)

    respuesta = VoiceResponse()
    respuesta.pause(length=1)

    # Seguir escuchando por si agregan más
    gather = Gather(
        input="speech",
        action="/webhooks/voice/escuchar-recado",
        language="es-CL",
        speech_timeout=3,
        timeout=5,
    )
    respuesta.append(gather)

    # Si no hablan más, despedirse
    respuesta.say(
        "Mensaje recibido. Gracias por llamar.",
        language="es-CL",
        voice="Polly.Mia",
    )

    return Response(content=str(respuesta), media_type="application/xml")


# ═══════════════════════════════════════════════════════════
# SECRETARIA PROCESAR (Premium: IA conversa)
# ═══════════════════════════════════════════════════════════

@router.api_route("/secretaria-procesar", methods=["GET", "POST"])
async def secretaria_procesar(request: Request, SpeechResult: str = Form("")):
    """Procesa turnos de conversación de la secretaria IA (Premium).

    La IA escucha, responde, y sigue conversando hasta que cuelguen.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    numero_destino = form_data.get("To", "")

    logger.info(f"[{call_sid}] Secretaria recibe: {SpeechResult}")

    usuario = _obtener_usuario_por_numero_twilio(numero_destino)

    conv = call_manager.obtener_llamada(call_sid)
    if not conv:
        conv = call_manager.iniciar_llamada(call_sid)

    conv.agregar_mensaje_usuario(SpeechResult)

    # Generar respuesta IA
    system_prompt = _construir_system_prompt_secretaria(usuario)
    from app.services.llm_service import openai_client
    from app.core.config import settings as app_settings

    mensajes = [{"role": "system", "content": system_prompt}]
    mensajes.extend(conv.historial)

    try:
        completion = openai_client.chat.completions.create(
            model=app_settings.OPENAI_MODEL,
            messages=mensajes,
            max_tokens=200,
            temperature=0.7,
        )
        texto_ia = completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error LLM: {e}")
        texto_ia = "Disculpa, tuve un problema tecnico. ¿Podrias repetir?"

    conv.agregar_mensaje_asistente(texto_ia)
    logger.info(f"[{call_sid}] Secretaria: {texto_ia}")

    # Responder con Polly
    respuesta = VoiceResponse()
    respuesta.say(texto_ia, **_get_voice_params(usuario))

    # Seguir escuchando
    gather = Gather(
        input="speech",
        action="/webhooks/voice/secretaria-procesar",
        language="es-CL",
        speech_timeout="auto",
        timeout=5,
    )
    respuesta.append(gather)

    respuesta.say(
        "Parece que se corto. Que tengas buen dia, adios.",
        **_get_voice_params(usuario),
    )

    return Response(content=str(respuesta), media_type="application/xml")


# ═══════════════════════════════════════════════════════════
# STATUS: ANÁLISIS POST-LLAMADA (igual para los 3 modos)
# ═══════════════════════════════════════════════════════════

@router.api_route("/status", methods=["POST"])
async def estado_llamada(request: Request):
    """Análisis post-llamada + WhatsApp. Funciona igual para los 3 modos."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    call_status = form_data.get("CallStatus", "unknown")
    call_duration = form_data.get("CallDuration", "0")

    logger.info(f"Estado {call_sid}: {call_status} ({call_duration}s)")

    if call_status in ("completed", "busy", "no-answer", "failed", "canceled"):
        conv = call_manager.finalizar_llamada(call_sid)

        db = SessionLocal()
        try:
            llamada_db = db.query(Llamada).filter(Llamada.call_sid == call_sid).first()

            if conv and conv.transcripcion_completa.strip():
                logger.info(f"Analizando llamada {call_sid}...")
                analisis = analizar_llamada(conv.transcripcion_completa)
                logger.info(f"Analisis: {analisis}")

                if llamada_db:
                    llamada_db.estado = EstadoLlamada.FINALIZADA.value
                    llamada_db.duracion_segundos = float(call_duration)
                    llamada_db.transcripcion = conv.transcripcion_completa
                    llamada_db.categoria = analisis.get("categoria")
                    llamada_db.prioridad = analisis.get("prioridad")
                    llamada_db.resumen = analisis.get("resumen")
                    llamada_db.nombre_contacto = analisis.get("nombre_contacto")

                whatsapp_sid = enviar_resumen_llamada(analisis, conv.numero_origen)
                if whatsapp_sid and llamada_db:
                    llamada_db.whatsapp_enviado = 1
                    llamada_db.whatsapp_sid = whatsapp_sid
            else:
                if llamada_db:
                    llamada_db.estado = call_status
                    llamada_db.duracion_segundos = float(call_duration)

            db.commit()
        except Exception as e:
            logger.error(f"Error procesando fin de llamada: {e}")
            db.rollback()
        finally:
            db.close()

    return Response(content="OK", media_type="text/plain")
