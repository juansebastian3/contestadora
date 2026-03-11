"""Webhooks de Twilio para manejo de llamadas de voz.

3 MODOS DE ASISTENTE:
─────────────────────────────────────────────────────────────────
  IA_CONVERSACIONAL (default):
    Sofía saluda con la voz elegida, conversa con el llamante,
    analiza y resume al final. El saludo se genera desde el
    prompt_personalizado del usuario (o el default).

  CONTESTADORA:
    Se reproduce el audio grabado por el usuario (su voz real).
    Después, la IA NO habla: solo escucha lo que dice el llamante.
    Al finalizar, analiza todo y envía resumen por WhatsApp.
    → Experiencia tipo contestadora clásica pero con IA detrás.

  HIBRIDO:
    Se reproduce el audio grabado como saludo inicial.
    Después, la IA toma el control y conversa normalmente.
    → Lo mejor de ambos mundos: tu voz real + IA inteligente.
─────────────────────────────────────────────────────────────────
"""
import logging
from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather

from app.core.config import settings
from app.services.call_manager import call_manager
from app.services.llm_service import generar_respuesta_conversacion, analizar_llamada
from app.services.whatsapp_service import enviar_resumen_llamada, enviar_alerta_llamada_entrante
from app.services.filtrado_service import decidir_filtrado
from app.services.tts_service import generar_twiml_con_voz
from app.models.database import (
    SessionLocal, Llamada, Usuario, EstadoLlamada, TipoVoz, ModoAsistente
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
    if usuario and usuario.voz_polly_id:
        return {"language": "es-CL", "voice": usuario.voz_polly_id}
    return {"language": "es-CL", "voice": "Polly.Mia"}


def _construir_saludo_ia(usuario: Usuario | None, evento_calendario: dict = None) -> str:
    """Construye el saludo tipo contestadora."""
    nombre_asistente = (usuario.nombre_asistente if usuario else None) or "Sofía"
    nombre_owner = (usuario.nombre if usuario else None) or settings.OWNER_NAME

    if evento_calendario:
        return (
            f"Hola, soy {nombre_asistente}, asistente de {nombre_owner}. "
            f"En este momento {nombre_owner} está en una reunión y no puede contestar. "
            "¿Con quién hablo y cuál es el motivo de tu llamada? "
            "Apenas termine le paso tu mensaje."
        )

    return (
        f"Hola, soy {nombre_asistente}, asistente de {nombre_owner}. "
        f"En este momento {nombre_owner} no puede atender. "
        "¿Con quién hablo y cuál es el motivo de tu llamada? "
        "Le haré llegar tu mensaje."
    )


def _construir_system_prompt(usuario: Usuario | None, evento_calendario: dict = None) -> str:
    """Construye el system prompt del LLM: contestadora que toma recados."""
    nombre_asistente = (usuario.nombre_asistente if usuario else None) or "Sofía"
    nombre_owner = (usuario.nombre if usuario else None) or settings.OWNER_NAME

    base = (
        f"Eres {nombre_asistente}, la asistente telefónica de {nombre_owner}.\n\n"
        "TU OBJETIVO: Que el llamante DEJE UN RECADO completo. Eres una contestadora inteligente.\n\n"
        "REGLAS CRÍTICAS:\n"
        f"- NUNCA digas 'contacta a {nombre_owner} directamente' ni 'intenta llamarlo' — ESO ES LO QUE YA ESTÁN HACIENDO.\n"
        "- NUNCA digas 'no tengo información sobre su agenda' — no la necesitas, solo toma el recado.\n"
        "- Tu trabajo es: escuchar el motivo, confirmar que entendiste, y despedirte.\n"
        "- Si es spam/marketing: 'Gracias, pero no le interesa. Que le vaya bien.'\n"
        f"- Si es importante: 'Perfecto, le aviso a {nombre_owner} que llamaste por [motivo]. ¿Algo más?'\n"
        f"- Despedida: '{nombre_owner} va a recibir tu mensaje. ¡Que te vaya bien!'\n"
        "- Máximo 2-3 oraciones por respuesta. Tono chileno cercano y profesional."
    )

    # Contexto de calendario: si está en reunión, la IA lo sabe
    if evento_calendario:
        titulo_evento = evento_calendario.get("titulo", "una reunión")
        base += (
            f"\n\nCONTEXTO ACTUAL: {nombre_owner} está en '{titulo_evento}' y no puede contestar. "
            f"Puedes mencionar que está en una reunión (sin dar detalles del evento). "
            f"Ejemplo: '{nombre_owner} está en una reunión en este momento, pero apenas termine le paso tu mensaje.'"
        )

    if usuario and usuario.prompt_personalizado:
        base += f"\n\nINSTRUCCIONES ADICIONALES DEL DUEÑO:\n{usuario.prompt_personalizado}"

    return base


# ═══════════════════════════════════════════════════════════
# WEBHOOK PRINCIPAL: INCOMING
# ═══════════════════════════════════════════════════════════

@router.api_route("/incoming", methods=["GET", "POST"])
async def contestar_llamada(request: Request):
    """Webhook principal. Decide qué modo usar y responde acorde."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    numero_origen = form_data.get("From", "Desconocido")
    numero_destino = form_data.get("To", "")
    base_url = str(request.base_url).rstrip("/")

    logger.info(f"📞 Llamada: {call_sid} | {numero_origen} → {numero_destino}")

    # ═══ 1. IDENTIFICAR USUARIO ═══
    usuario = _obtener_usuario_por_numero_twilio(numero_destino)

    # ═══ 2. DECIDIR FILTRADO ═══
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
        logger.info(f"🔍 Filtrado: {resultado.motivo}")

        if not debe_filtrar:
            respuesta = VoiceResponse()
            respuesta.dial(usuario.telefono)
            return Response(content=str(respuesta), media_type="application/xml")

    # ═══ 3. REGISTRAR LLAMADA ═══
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

    # ═══ 4. ELEGIR MODO DE ASISTENTE ═══
    modo_asistente = ModoAsistente.IA_CONVERSACIONAL.value
    if usuario:
        modo_asistente = usuario.modo_asistente or ModoAsistente.IA_CONVERSACIONAL.value

    logger.info(f"🤖 Modo asistente: {modo_asistente}")

    if modo_asistente == ModoAsistente.CONTESTADORA.value:
        return _responder_modo_contestadora(usuario, base_url, evento_calendario)
    elif modo_asistente == ModoAsistente.HIBRIDO.value:
        return _responder_modo_hibrido(usuario, base_url, evento_calendario)
    else:
        return _responder_modo_ia(usuario, base_url, evento_calendario)


# ═══════════════════════════════════════════════════════════
# MODO 1: IA CONVERSACIONAL (default)
# ═══════════════════════════════════════════════════════════

def _responder_modo_ia(usuario: Usuario | None, base_url: str, evento_calendario: dict = None) -> Response:
    """La IA saluda y conversa con el llamante."""
    respuesta = VoiceResponse()
    respuesta.pause(length=1)

    saludo = _construir_saludo_ia(usuario, evento_calendario)
    voice_params = _get_voice_params(usuario)

    gather = Gather(
        input="speech",
        action="/webhooks/voice/procesar",
        language="es-CL",
        speech_timeout="auto",
        timeout=5,
    )
    gather.say(saludo, **voice_params)
    respuesta.append(gather)

    nombre_owner = (usuario.nombre if usuario else None) or settings.OWNER_NAME
    respuesta.say(
        f"No pude escuchar nada. Intenta llamar a {nombre_owner} más tarde. Adiós.",
        **voice_params,
    )

    return Response(content=str(respuesta), media_type="application/xml")


# ═══════════════════════════════════════════════════════════
# MODO 2: CONTESTADORA (audio grabado + IA solo escucha)
# ═══════════════════════════════════════════════════════════

def _responder_modo_contestadora(usuario: Usuario | None, base_url: str, evento_calendario: dict = None) -> Response:
    """Reproduce el audio grabado del usuario. La IA NO habla, solo escucha.

    Flujo:
    1. <Play> → Audio grabado por el usuario ("Hola, soy Juan, dejame tu mensaje...")
    2. <Record> → Graba lo que dice el llamante (como contestadora clásica)
    3. Al colgar → /status analiza la grabación y envía resumen WhatsApp

    Alternativa si no hay audio: genera saludo con TTS y escucha.
    """
    respuesta = VoiceResponse()
    respuesta.pause(length=1)

    if usuario and usuario.audio_saludo_url:
        # Reproducir el audio grabado del usuario (su voz real → genera confianza)
        audio_url = f"{base_url}{usuario.audio_saludo_url}"
        respuesta.play(audio_url)
    else:
        # Fallback: generar saludo personalizado con TTS
        nombre = (usuario.nombre if usuario else None) or settings.OWNER_NAME
        voice_params = _get_voice_params(usuario)
        if evento_calendario:
            saludo_fallback = (
                f"Hola, soy {nombre}. Estoy en una reunión y no puedo contestar. "
                "Deja tu nombre, el motivo de tu llamada, "
                "y te devuelvo el llamado apenas termine. Gracias."
            )
        else:
            saludo_fallback = (
                f"Hola, soy {nombre}. No puedo atender en este momento. "
                "Por favor, deja tu nombre, el motivo de tu llamada "
                "y te devolveré el llamado. Gracias."
            )
        respuesta.say(saludo_fallback, **voice_params)

    # Escuchar lo que dice el llamante (no IA, solo grabar)
    # Usamos Gather en vez de Record para obtener transcripción
    gather = Gather(
        input="speech",
        action="/webhooks/voice/contestadora-escuchar",
        language="es-CL",
        speech_timeout=5,
        timeout=10,
    )
    respuesta.append(gather)

    # Si no hablan, despedirse
    respuesta.say("No se recibió mensaje. Adiós.", language="es-CL", voice="Polly.Mia")

    return Response(content=str(respuesta), media_type="application/xml")


# ═══════════════════════════════════════════════════════════
# MODO 3: HÍBRIDO (audio grabado + IA conversa después)
# ═══════════════════════════════════════════════════════════

def _responder_modo_hibrido(usuario: Usuario | None, base_url: str, evento_calendario: dict = None) -> Response:
    """Reproduce el audio del usuario como saludo, luego la IA toma el control.

    Flujo:
    1. <Play> → Audio grabado del usuario
    2. <Gather> → Escucha respuesta del llamante
    3. → /webhooks/voice/procesar → La IA conversa normalmente desde aquí
    """
    respuesta = VoiceResponse()
    respuesta.pause(length=1)

    if usuario and usuario.audio_saludo_url:
        audio_url = f"{base_url}{usuario.audio_saludo_url}"
        respuesta.play(audio_url)
    else:
        nombre = (usuario.nombre if usuario else None) or settings.OWNER_NAME
        voice_params = _get_voice_params(usuario)
        respuesta.say(
            f"Hola, te comunicas con {nombre}. ¿Con quién hablo y en qué te puedo ayudar?",
            **voice_params,
        )

    # Después del audio, la IA toma el control
    gather = Gather(
        input="speech",
        action="/webhooks/voice/procesar",
        language="es-CL",
        speech_timeout="auto",
        timeout=5,
    )
    respuesta.append(gather)

    respuesta.say(
        "No pude escuchar nada. Intenta más tarde. Adiós.",
        language="es-CL",
        voice="Polly.Mia",
    )

    return Response(content=str(respuesta), media_type="application/xml")


# ═══════════════════════════════════════════════════════════
# PROCESAMIENTO DE TURNOS
# ═══════════════════════════════════════════════════════════

@router.api_route("/procesar", methods=["GET", "POST"])
async def procesar_llamada(request: Request, SpeechResult: str = Form("")):
    """Procesa cada turno de la conversación (modo IA e híbrido).

    Usa el prompt_personalizado del usuario para guiar las respuestas.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    numero_destino = form_data.get("To", "")
    base_url = str(request.base_url).rstrip("/")

    logger.info(f"🎤 [{call_sid}] Llamante: {SpeechResult}")

    usuario = _obtener_usuario_por_numero_twilio(numero_destino)

    conv = call_manager.obtener_llamada(call_sid)
    if not conv:
        conv = call_manager.iniciar_llamada(call_sid)

    conv.agregar_mensaje_usuario(SpeechResult)

    # Generar respuesta con prompt personalizado (incluye contexto calendario si aplica)
    system_prompt = _construir_system_prompt(usuario)
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
        texto_ia = "Disculpa, tuve un problema técnico. ¿Podrías repetir?"

    conv.agregar_mensaje_asistente(texto_ia)
    logger.info(f"🤖 [{call_sid}] Respuesta: {texto_ia}")

    # Responder con la voz correcta
    respuesta = VoiceResponse()

    if usuario and usuario.voz_tipo == TipoVoz.ELEVENLABS.value and usuario.voz_elevenlabs_id:
        from app.services.tts_service import _generar_audio_elevenlabs
        audio_url = _generar_audio_elevenlabs(texto_ia, usuario.voz_elevenlabs_id, base_url)
        if audio_url:
            respuesta.play(audio_url)
        else:
            respuesta.say(texto_ia, **_get_voice_params(usuario))
    else:
        respuesta.say(texto_ia, **_get_voice_params(usuario))

    # Seguir escuchando
    gather = Gather(
        input="speech",
        action="/webhooks/voice/procesar",
        language="es-CL",
        speech_timeout="auto",
        timeout=5,
    )
    respuesta.append(gather)

    respuesta.say(
        "Parece que se cortó. Que tengas buen día, adiós.",
        **_get_voice_params(usuario),
    )

    return Response(content=str(respuesta), media_type="application/xml")


@router.api_route("/contestadora-escuchar", methods=["GET", "POST"])
async def contestadora_escuchar(request: Request, SpeechResult: str = Form("")):
    """Recibe lo que dijo el llamante en modo contestadora.

    La IA NO responde. Solo guarda la transcripción.
    Opcionalmente, sigue escuchando por si quieren decir más.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")

    logger.info(f"📝 [{call_sid}] Contestadora recibió: {SpeechResult}")

    conv = call_manager.obtener_llamada(call_sid)
    if not conv:
        conv = call_manager.iniciar_llamada(call_sid)

    conv.agregar_mensaje_usuario(SpeechResult)

    # NO generar respuesta IA. Solo confirmar y seguir escuchando.
    respuesta = VoiceResponse()

    # Dar un breve "beep" o pausa para indicar que sigue grabando
    respuesta.pause(length=1)

    # Seguir escuchando por si quieren agregar algo más
    gather = Gather(
        input="speech",
        action="/webhooks/voice/contestadora-escuchar",
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
# STATUS: ANÁLISIS POST-LLAMADA (igual para los 3 modos)
# ═══════════════════════════════════════════════════════════

@router.api_route("/status", methods=["POST"])
async def estado_llamada(request: Request):
    """Análisis post-llamada + WhatsApp. Funciona igual para los 3 modos."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    call_status = form_data.get("CallStatus", "unknown")
    call_duration = form_data.get("CallDuration", "0")

    logger.info(f"📊 Estado {call_sid}: {call_status} ({call_duration}s)")

    if call_status in ("completed", "busy", "no-answer", "failed", "canceled"):
        conv = call_manager.finalizar_llamada(call_sid)

        db = SessionLocal()
        try:
            llamada_db = db.query(Llamada).filter(Llamada.call_sid == call_sid).first()

            if conv and conv.transcripcion_completa.strip():
                logger.info(f"🧠 Analizando llamada {call_sid}...")
                analisis = analizar_llamada(conv.transcripcion_completa)
                logger.info(f"📋 Análisis: {analisis}")

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
