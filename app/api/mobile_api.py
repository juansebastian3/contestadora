"""API REST para la aplicación móvil - PROTEGIDA con JWT.

Todos los endpoints (excepto /health, /voces y /planes que son públicos)
requieren un Bearer token válido en el header Authorization.

La app móvil debe:
1. Hacer POST /auth/registro o /auth/login para obtener tokens
2. Guardar access_token y refresh_token en AsyncStorage
3. Enviar access_token en cada request: Authorization: Bearer <token>
4. Si recibe 401, hacer POST /auth/refresh con el refresh_token
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from fastapi import UploadFile, File
from pathlib import Path
import shutil
import requests as http_requests

from app.models.database import (
    get_db, Llamada, Configuracion, VozDisponible, Plan, Usuario,
    ModoFiltrado, ModoAsistente, PlanTipo,
)
from app.models.schemas import (
    LlamadaResponse, DashboardStats, ConfiguracionUpdate,
    SeleccionarVozRequest, CambiarModoRequest, ContactosRequest,
    GuardarPromptRequest, CambiarModoAsistenteRequest, PersonalizacionResponse,
)
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Mobile API"])


# ═══════════════════════════════════════════════════════════
# HELPER: convertir Llamada DB → LlamadaResponse
# ═══════════════════════════════════════════════════════════

def _llamada_to_response(ll: Llamada) -> LlamadaResponse:
    return LlamadaResponse(
        id=ll.id, call_sid=ll.call_sid, numero_origen=ll.numero_origen,
        fecha_inicio=ll.fecha_inicio, fecha_fin=ll.fecha_fin,
        duracion_segundos=ll.duracion_segundos, estado=ll.estado,
        transcripcion=ll.transcripcion or "", categoria=ll.categoria,
        prioridad=ll.prioridad, resumen=ll.resumen,
        nombre_contacto=ll.nombre_contacto,
        whatsapp_enviado=bool(ll.whatsapp_enviado),
    )


# ═══════════════════════════════════════════════════════════
# DASHBOARD (protegido)
# ═══════════════════════════════════════════════════════════

@router.get("/dashboard", response_model=DashboardStats)
async def obtener_dashboard(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Estadísticas del dashboard - solo las llamadas del usuario autenticado."""
    hoy = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    base = db.query(Llamada).filter(Llamada.usuario_id == usuario.id)

    total = base.count()
    hoy_count = base.filter(Llamada.fecha_inicio >= hoy).count()
    spam = base.filter(Llamada.categoria == "Marketing").count()
    importantes = base.filter(Llamada.prioridad.in_(["Alta", "Media"])).count()

    categorias_raw = db.query(
        Llamada.categoria, func.count(Llamada.id)
    ).filter(Llamada.usuario_id == usuario.id).group_by(Llamada.categoria).all()
    por_categoria = {cat or "Sin categoría": count for cat, count in categorias_raw}

    prioridades_raw = db.query(
        Llamada.prioridad, func.count(Llamada.id)
    ).filter(Llamada.usuario_id == usuario.id).group_by(Llamada.prioridad).all()
    por_prioridad = {pri or "Sin prioridad": count for pri, count in prioridades_raw}

    ultimas = base.order_by(desc(Llamada.fecha_inicio)).limit(20).all()

    return DashboardStats(
        total_llamadas=total,
        llamadas_hoy=hoy_count,
        spam_bloqueado=spam,
        llamadas_importantes=importantes,
        por_categoria=por_categoria,
        por_prioridad=por_prioridad,
        ultimas_llamadas=[_llamada_to_response(ll) for ll in ultimas],
    )


# ═══════════════════════════════════════════════════════════
# LLAMADAS (protegido)
# ═══════════════════════════════════════════════════════════

@router.get("/llamadas", response_model=list[LlamadaResponse])
async def listar_llamadas(
    categoria: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    dias: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista llamadas del usuario autenticado con filtros."""
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    query = db.query(Llamada).filter(
        Llamada.usuario_id == usuario.id,
        Llamada.fecha_inicio >= desde,
    )

    if categoria:
        query = query.filter(Llamada.categoria == categoria)
    if prioridad:
        query = query.filter(Llamada.prioridad == prioridad)
    if estado:
        query = query.filter(Llamada.estado == estado)

    llamadas = query.order_by(desc(Llamada.fecha_inicio)).offset(offset).limit(limit).all()
    return [_llamada_to_response(ll) for ll in llamadas]


@router.get("/llamadas/{llamada_id}", response_model=LlamadaResponse)
async def obtener_llamada(
    llamada_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Detalle de una llamada. Solo accesible si pertenece al usuario."""
    ll = db.query(Llamada).filter(
        Llamada.id == llamada_id,
        Llamada.usuario_id == usuario.id,
    ).first()
    if not ll:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return _llamada_to_response(ll)


@router.get("/stats/semanal")
async def estadisticas_semanales(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Estadísticas de los últimos 7 días del usuario autenticado."""
    datos = []
    for i in range(6, -1, -1):
        dia = datetime.now(timezone.utc) - timedelta(days=i)
        inicio = dia.replace(hour=0, minute=0, second=0, microsecond=0)
        fin = inicio + timedelta(days=1)
        total = db.query(func.count(Llamada.id)).filter(
            Llamada.usuario_id == usuario.id,
            Llamada.fecha_inicio >= inicio,
            Llamada.fecha_inicio < fin,
        ).scalar() or 0
        spam = db.query(func.count(Llamada.id)).filter(
            Llamada.usuario_id == usuario.id,
            Llamada.fecha_inicio >= inicio,
            Llamada.fecha_inicio < fin,
            Llamada.categoria == "Marketing",
        ).scalar() or 0
        datos.append({
            "fecha": inicio.strftime("%Y-%m-%d"),
            "dia": inicio.strftime("%a"),
            "total": total,
            "spam": spam,
            "importantes": total - spam,
        })
    return {"semana": datos}


# ═══════════════════════════════════════════════════════════
# VOCES (catálogo público, selección protegida)
# ═══════════════════════════════════════════════════════════

@router.get("/voces")
async def listar_voces(db: Session = Depends(get_db)):
    """Catálogo de voces disponibles. Público (no requiere auth)."""
    voces = db.query(VozDisponible).filter(VozDisponible.activa == True).order_by(VozDisponible.orden).all()
    return [
        {
            "id": v.id,
            "nombre": v.nombre,
            "descripcion": v.descripcion,
            "idioma": v.idioma,
            "genero": v.genero,
            "tipo": v.tipo,
            "plan_minimo": v.plan_minimo,
            "preview_url": v.preview_url,
            "es_premium": v.tipo == "elevenlabs",
        }
        for v in voces
    ]


@router.post("/voces/seleccionar")
async def seleccionar_voz(
    data: SeleccionarVozRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """El usuario selecciona una voz. Verifica que su plan lo permita."""
    voz = db.query(VozDisponible).filter(VozDisponible.id == data.voz_id).first()
    if not voz:
        raise HTTPException(status_code=404, detail="Voz no encontrada")

    plan_orden = {"free": 0, "pro": 1, "premium": 2}
    if plan_orden.get(usuario.plan, 0) < plan_orden.get(voz.plan_minimo, 0):
        raise HTTPException(
            status_code=403,
            detail=f"Tu plan ({usuario.plan}) no incluye esta voz. Necesitas plan {voz.plan_minimo}."
        )

    usuario.voz_tipo = voz.tipo
    if voz.tipo == "polly":
        usuario.voz_polly_id = voz.polly_voice_id
    elif voz.tipo == "elevenlabs":
        usuario.voz_elevenlabs_id = voz.elevenlabs_voice_id

    db.commit()
    return {"status": "ok", "voz_seleccionada": voz.nombre, "tipo": voz.tipo}


# ═══════════════════════════════════════════════════════════
# PLANES (público)
# ═══════════════════════════════════════════════════════════

@router.get("/planes")
async def listar_planes(db: Session = Depends(get_db)):
    """Lista todos los planes disponibles. Público."""
    planes = db.query(Plan).filter(Plan.activo == True).order_by(Plan.precio_mensual_usd).all()
    return [
        {
            "codigo": p.codigo,
            "nombre": p.nombre,
            "precio_mensual": p.precio_mensual_usd,
            "precio_anual": p.precio_anual_usd,
            "ahorro_anual": round((p.precio_mensual_usd * 12 - p.precio_anual_usd), 2) if p.precio_anual_usd else 0,
            "llamadas_mes": p.llamadas_mes,
            "minutos_mes": p.minutos_mes,
            "voces_polly": p.voces_polly,
            "voces_elevenlabs": p.voces_elevenlabs,
            "voz_personalizada": p.voz_personalizada,
            "modo_luna": p.modo_luna,
            "analisis_avanzado": p.analisis_avanzado,
            "prioridad_soporte": p.prioridad_soporte,
            "destacado": p.destacado,
            "descripcion": p.descripcion,
            "features": p.features_json,
        }
        for p in planes
    ]


# ═══════════════════════════════════════════════════════════
# PERFIL Y MODO DE FILTRADO (protegido)
# ═══════════════════════════════════════════════════════════

@router.get("/perfil")
async def obtener_perfil(usuario: Usuario = Depends(get_current_user)):
    """Perfil del usuario autenticado. Ya no necesita UID en la URL."""
    return {
        "uid": usuario.uid,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "telefono": usuario.telefono,
        "plan": usuario.plan,
        "plan_expira": usuario.plan_expira,
        "nombre_asistente": usuario.nombre_asistente,
        "modo_filtrado": usuario.modo_filtrado,
        "horario_luna": {
            "inicio": usuario.horario_luna_inicio,
            "fin": usuario.horario_luna_fin,
        },
        "voz": {
            "tipo": usuario.voz_tipo,
            "polly_id": usuario.voz_polly_id,
            "elevenlabs_id": usuario.voz_elevenlabs_id,
        },
        "notificaciones": {
            "whatsapp": usuario.notif_whatsapp,
            "push": usuario.notif_push,
            "solo_importantes": usuario.notif_solo_importantes,
        },
        "personalizacion": {
            "modo_asistente": usuario.modo_asistente or "asistente_basico",
            "prompt_personalizado": usuario.prompt_personalizado,
            "tiene_audio_saludo": bool(usuario.audio_saludo_url),
            "audio_saludo_url": usuario.audio_saludo_url,
            "audio_saludo_duracion": usuario.audio_saludo_duracion,
        },
        "telefono_twilio": usuario.telefono_twilio,
        "contactos_conocidos_count": len(usuario.contactos_conocidos or []),
        "calendario": {
            "google_conectado": bool(usuario.google_calendar_token),
            "outlook_conectado": bool(usuario.outlook_calendar_token),
            "auto_activar": usuario.calendario_auto_activar,
            "modo": usuario.calendario_modo or "solo_reuniones",
        },
    }


@router.post("/perfil/modo-filtrado")
async def cambiar_modo_filtrado(
    data: CambiarModoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cambia el modo de filtrado del usuario autenticado."""
    modos_validos = [m.value for m in ModoFiltrado]
    if data.modo not in modos_validos:
        raise HTTPException(status_code=400, detail=f"Modo inválido. Opciones: {modos_validos}")

    if data.modo == ModoFiltrado.LUNA.value:
        if usuario.plan not in (PlanTipo.PRO.value, PlanTipo.PREMIUM.value):
            raise HTTPException(
                status_code=403,
                detail="El modo Luna requiere plan Pro o Premium."
            )

    usuario.modo_filtrado = data.modo
    if data.horario_inicio:
        usuario.horario_luna_inicio = data.horario_inicio
    if data.horario_fin:
        usuario.horario_luna_fin = data.horario_fin

    db.commit()
    return {
        "status": "ok",
        "modo": data.modo,
        "horario_luna": {"inicio": usuario.horario_luna_inicio, "fin": usuario.horario_luna_fin},
    }


@router.post("/perfil/contactos")
async def actualizar_contactos(
    data: ContactosRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza contactos conocidos del usuario autenticado."""
    usuario.contactos_conocidos = data.contactos
    db.commit()
    return {"status": "ok", "total_contactos": len(data.contactos)}


# ═══════════════════════════════════════════════════════════
# PERSONALIZACIÓN: PROMPT, CONTESTADORA, MODO ASISTENTE
# ═══════════════════════════════════════════════════════════

@router.get("/perfil/personalizacion", response_model=PersonalizacionResponse)
async def obtener_personalizacion(usuario: Usuario = Depends(get_current_user)):
    """Obtener configuración de personalización del asistente."""
    return PersonalizacionResponse(
        modo_asistente=usuario.modo_asistente or ModoAsistente.ASISTENTE_BASICO.value,
        prompt_personalizado=usuario.prompt_personalizado,
        audio_saludo_url=usuario.audio_saludo_url,
        audio_saludo_duracion=usuario.audio_saludo_duracion,
    )


@router.post("/perfil/prompt")
async def guardar_prompt(
    data: GuardarPromptRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Guardar prompt personalizado del usuario.

    El prompt se inyecta en las instrucciones del LLM como
    'INSTRUCCIONES DEL DUEÑO' para personalizar el comportamiento.
    Ejemplo: 'Soy veterinario, si llaman por emergencia pide dirección y síntomas.'
    """
    usuario.prompt_personalizado = data.prompt.strip() if data.prompt.strip() else None
    db.commit()
    return {
        "status": "ok",
        "prompt_guardado": usuario.prompt_personalizado is not None,
        "longitud": len(usuario.prompt_personalizado) if usuario.prompt_personalizado else 0,
    }


@router.delete("/perfil/prompt")
async def borrar_prompt(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar prompt personalizado (volver al comportamiento por defecto)."""
    usuario.prompt_personalizado = None
    db.commit()
    return {"status": "ok", "prompt_guardado": False}


@router.post("/perfil/modo-asistente")
async def cambiar_modo_asistente(
    data: CambiarModoAsistenteRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cambiar el modo del asistente: asistente_basico, contestadora, secretaria_ia.

    - asistente_basico: Polly saluda, IA solo escucha y transcribe (Free)
    - contestadora: Tu voz grabada como saludo, IA solo escucha (Pro)
    - secretaria_ia: Tu voz saluda + IA conversa como secretaria (Premium)
    """
    modos_validos = [m.value for m in ModoAsistente]
    if data.modo not in modos_validos:
        raise HTTPException(status_code=400, detail=f"Modo inválido. Opciones: {modos_validos}")

    # Contestadora y secretaria_ia requieren audio grabado
    if data.modo in (ModoAsistente.CONTESTADORA.value, ModoAsistente.SECRETARIA_IA.value):
        if not usuario.audio_saludo_url:
            raise HTTPException(
                status_code=400,
                detail="Para usar modo contestadora o secretaria IA, primero sube tu audio de saludo."
            )

    # Verificar plan requerido
    if data.modo == ModoAsistente.CONTESTADORA.value:
        if usuario.plan not in (PlanTipo.PRO.value, PlanTipo.PREMIUM.value):
            raise HTTPException(status_code=403, detail="El modo contestadora requiere plan Pro o Premium.")
    elif data.modo == ModoAsistente.SECRETARIA_IA.value:
        if usuario.plan != PlanTipo.PREMIUM.value:
            raise HTTPException(status_code=403, detail="El modo secretaria IA requiere plan Premium.")

    usuario.modo_asistente = data.modo
    db.commit()
    return {"status": "ok", "modo_asistente": data.modo}


@router.post("/perfil/audio-saludo")
async def subir_audio_saludo(
    audio: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Subir audio de saludo grabado por el usuario (modo contestadora/híbrido).

    Acepta archivos MP3, WAV, M4A, OGG. Máximo 5 MB (~60 segundos).
    El audio se almacena en /audio_uploads/{uid}/ y se sirve como estático.
    """
    # Validar tipo de archivo
    extensiones_validas = {".mp3", ".wav", ".m4a", ".ogg", ".webm"}
    ext = Path(audio.filename).suffix.lower() if audio.filename else ".mp3"
    if ext not in extensiones_validas:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado ({ext}). Usa: {', '.join(extensiones_validas)}"
        )

    # Validar tamaño (5 MB máximo)
    contenido = await audio.read()
    if len(contenido) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El audio no debe superar 5 MB (~60 segundos).")

    # Guardar archivo
    upload_dir = Path(f"./audio_uploads/{usuario.uid}")
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"saludo{ext}"
    filepath = upload_dir / filename

    with open(filepath, "wb") as f:
        f.write(contenido)

    # Actualizar usuario
    from app.core.config import settings
    audio_url = f"{settings.BASE_URL}/audio_uploads/{usuario.uid}/{filename}"
    usuario.audio_saludo_url = audio_url
    db.commit()

    return {
        "status": "ok",
        "audio_url": audio_url,
        "tamaño_bytes": len(contenido),
        "formato": ext,
    }


@router.delete("/perfil/audio-saludo")
async def borrar_audio_saludo(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar audio de saludo. Si el modo requiere audio, vuelve a asistente_basico."""
    if usuario.audio_saludo_url:
        # Intentar borrar archivo físico
        upload_dir = Path(f"./audio_uploads/{usuario.uid}")
        if upload_dir.exists():
            shutil.rmtree(upload_dir, ignore_errors=True)

    usuario.audio_saludo_url = None
    usuario.audio_saludo_duracion = None

    # Si estaba en modo que requiere audio, volver a IA conversacional
    if usuario.modo_asistente in (ModoAsistente.CONTESTADORA.value, ModoAsistente.SECRETARIA_IA.value):
        usuario.modo_asistente = ModoAsistente.ASISTENTE_BASICO.value

    db.commit()
    return {"status": "ok", "modo_asistente": usuario.modo_asistente}


# ═══════════════════════════════════════════════════════════
# CALENDARIO: OAUTH2 + CONECTAR / DESCONECTAR / ESTADO
# ═══════════════════════════════════════════════════════════

@router.get("/calendario/google/auth-url")
async def google_calendar_auth_url(
    usuario: Usuario = Depends(get_current_user),
):
    """Genera la URL de autorización de Google Calendar OAuth2.

    La app móvil abre esta URL en un navegador. El usuario autoriza
    y Google redirige a /api/v1/calendario/google/callback con un code.
    """
    from app.core.config import settings
    import urllib.parse

    if usuario.plan not in (PlanTipo.PRO.value, PlanTipo.PREMIUM.value):
        raise HTTPException(status_code=403, detail="Integración de calendario requiere plan Pro o Premium.")

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Calendar no configurado en el servidor.")

    redirect_uri = f"{settings.BASE_URL}/api/v1/calendario/google/callback"

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.readonly",
        "access_type": "offline",
        "prompt": "consent",
        "state": usuario.uid,  # Para identificar al usuario en el callback
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return {"auth_url": auth_url}


@router.get("/calendario/google/callback")
async def google_calendar_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    db: Session = Depends(get_db),
):
    """Callback de Google OAuth2. Google redirige aquí tras autorizar.

    Intercambia el authorization code por tokens y los guarda en el usuario.
    Responde con HTML que la app móvil puede interceptar (deep link o mensaje de éxito).
    """
    from app.core.config import settings

    if error:
        return _calendar_callback_html("Error", f"Google rechazó la autorización: {error}")

    if not code or not state:
        return _calendar_callback_html("Error", "Faltan parámetros (code o state).")

    # Buscar usuario por UID (state)
    usuario = db.query(Usuario).filter(Usuario.uid == state).first()
    if not usuario:
        return _calendar_callback_html("Error", "Usuario no encontrado.")

    # Intercambiar code por tokens
    redirect_uri = f"{settings.BASE_URL}/api/v1/calendario/google/callback"

    try:
        token_resp = http_requests.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }, timeout=10)

        if token_resp.status_code != 200:
            logger.error(f"Google token exchange failed: {token_resp.text}")
            return _calendar_callback_html("Error", "No se pudo obtener el token de Google.")

        tokens = token_resp.json()

        # Guardar tokens en el usuario
        from datetime import datetime, timezone, timedelta
        expiry = datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))

        usuario.google_calendar_token = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "expiry": expiry.isoformat(),
        }
        usuario.calendario_auto_activar = True
        db.commit()

        return _calendar_callback_html(
            "Conectado",
            "Google Calendar conectado correctamente. Ya puedes cerrar esta ventana y volver a la app."
        )

    except Exception as e:
        logger.error(f"Error en Google OAuth callback: {e}")
        return _calendar_callback_html("Error", f"Error técnico: {str(e)[:100]}")


def _calendar_callback_html(titulo: str, mensaje: str) -> Response:
    """Genera una página HTML simple para mostrar resultado del OAuth."""
    from fastapi.responses import HTMLResponse
    color = "#22c55e" if titulo == "Conectado" else "#ef4444"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FiltroLlamadas - {titulo}</title>
<style>body{{font-family:-apple-system,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f9fafb}}
.card{{background:white;border-radius:16px;padding:40px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.1);max-width:400px}}
h1{{color:{color};margin-bottom:12px}}p{{color:#6b7280;line-height:1.6}}</style></head>
<body><div class="card"><h1>{titulo}</h1><p>{mensaje}</p></div></body></html>"""
    return HTMLResponse(content=html)


@router.post("/calendario/google/conectar")
async def conectar_google_calendar(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Alternativa: la app envía tokens directamente (si maneja OAuth2 con expo-auth-session).

    Requiere plan Pro o Premium.
    """
    if usuario.plan not in (PlanTipo.PRO.value, PlanTipo.PREMIUM.value):
        raise HTTPException(status_code=403, detail="Integración de calendario requiere plan Pro o Premium.")

    body = await request.json()

    # Si la app envía un authorization_code, intercambiarlo por tokens
    if body.get("code"):
        from app.core.config import settings
        redirect_uri = body.get("redirect_uri", f"{settings.BASE_URL}/api/v1/calendario/google/callback")

        token_resp = http_requests.post("https://oauth2.googleapis.com/token", data={
            "code": body["code"],
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }, timeout=10)

        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Error intercambiando code: {token_resp.text[:200]}")

        tokens = token_resp.json()
        expiry = datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))

        token_data = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "expiry": expiry.isoformat(),
        }
    else:
        # La app envía tokens directamente
        token_data = {
            "access_token": body.get("access_token"),
            "refresh_token": body.get("refresh_token"),
            "expiry": body.get("expiry"),
        }

    if not token_data.get("access_token"):
        raise HTTPException(status_code=400, detail="Falta access_token o code")

    usuario.google_calendar_token = token_data
    if not usuario.calendario_auto_activar:
        usuario.calendario_auto_activar = True

    db.commit()
    return {
        "status": "ok",
        "calendario": "google",
        "auto_activar": usuario.calendario_auto_activar,
    }


@router.delete("/calendario/google")
async def desconectar_google_calendar(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Desconecta Google Calendar."""
    usuario.google_calendar_token = None
    # Si no queda ningún calendario conectado, desactivar auto
    if not usuario.outlook_calendar_token:
        usuario.calendario_auto_activar = False
    db.commit()
    return {"status": "ok", "calendario_desconectado": "google"}


@router.post("/calendario/outlook/conectar")
async def conectar_outlook_calendar(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Guarda los tokens de Outlook/Office 365 Calendar tras OAuth2.

    La app móvil maneja el flujo OAuth2 con Microsoft y envía los tokens aquí.
    Requiere plan Pro o Premium.
    """
    if usuario.plan not in (PlanTipo.PRO.value, PlanTipo.PREMIUM.value):
        raise HTTPException(status_code=403, detail="Integración de calendario requiere plan Pro o Premium.")

    body = await request.json()
    token_data = {
        "access_token": body.get("access_token"),
        "refresh_token": body.get("refresh_token"),
        "expiry": body.get("expiry"),
    }

    if not token_data["access_token"]:
        raise HTTPException(status_code=400, detail="Falta access_token")

    usuario.outlook_calendar_token = token_data
    if not usuario.calendario_auto_activar:
        usuario.calendario_auto_activar = True

    db.commit()
    return {
        "status": "ok",
        "calendario": "outlook",
        "auto_activar": usuario.calendario_auto_activar,
    }


@router.delete("/calendario/outlook")
async def desconectar_outlook_calendar(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Desconecta Outlook Calendar."""
    usuario.outlook_calendar_token = None
    if not usuario.google_calendar_token:
        usuario.calendario_auto_activar = False
    db.commit()
    return {"status": "ok", "calendario_desconectado": "outlook"}


@router.get("/calendario/estado")
async def estado_calendario(
    usuario: Usuario = Depends(get_current_user),
):
    """Estado de la integración de calendarios del usuario."""
    google_conectado = bool(usuario.google_calendar_token)
    outlook_conectado = bool(usuario.outlook_calendar_token)

    # Verificar si hay evento activo ahora
    evento_actual = None
    if usuario.calendario_auto_activar and (google_conectado or outlook_conectado):
        try:
            from app.services.calendario_service import usuario_en_reunion
            evento_actual = usuario_en_reunion(usuario)
        except Exception:
            pass

    return {
        "google_conectado": google_conectado,
        "outlook_conectado": outlook_conectado,
        "auto_activar": usuario.calendario_auto_activar,
        "modo_calendario": usuario.calendario_modo or "solo_reuniones",
        "evento_actual": evento_actual,
    }


@router.post("/calendario/config")
async def configurar_calendario(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Configura el comportamiento del calendario.

    Body: {auto_activar: bool, modo: "solo_reuniones"|"siempre_agenda"|"manual"}
    """
    body = await request.json()

    if "auto_activar" in body:
        usuario.calendario_auto_activar = bool(body["auto_activar"])

    if "modo" in body:
        modos_validos = ["solo_reuniones", "siempre_agenda", "manual"]
        if body["modo"] not in modos_validos:
            raise HTTPException(status_code=400, detail=f"Modo inválido. Opciones: {modos_validos}")
        usuario.calendario_modo = body["modo"]

    db.commit()
    return {
        "status": "ok",
        "auto_activar": usuario.calendario_auto_activar,
        "modo_calendario": usuario.calendario_modo,
    }


# ═══════════════════════════════════════════════════════════
# TIPS PARA GRABAR SALUDO (mejora la experiencia de grabación)
# ═══════════════════════════════════════════════════════════

@router.get("/tips/saludo")
async def obtener_tips_saludo():
    """Tips y ejemplos para que el usuario grabe un buen saludo.

    Esto hace que la experiencia sea claramente diferente a un buzón
    de voz genérico, aumentando la tasa de recados completos (~80% vs ~30%).
    """
    return {
        "titulo": "Graba tu saludo personalizado",
        "descripcion": "Un saludo con tu voz real genera confianza. Los llamantes dejan mensajes completos cuando saben que es tu contestadora personal.",
        "tips": [
            "Usa tu nombre: 'Hola, soy [tu nombre]'",
            "Sé breve: 15-30 segundos es ideal",
            "Menciona que recibirás el mensaje: 'Te devuelvo la llamada apenas pueda'",
            "Habla con naturalidad, como si hablaras con un amigo",
            "Graba en un lugar silencioso",
        ],
        "ejemplos": [
            {
                "titulo": "Profesional",
                "texto": "Hola, soy [nombre]. No puedo contestar ahora, pero deja tu nombre y el motivo de tu llamada. Me llega un mensaje con lo que digas y te devuelvo el llamado. ¡Gracias!",
            },
            {
                "titulo": "Casual",
                "texto": "¡Hola! Soy [nombre]. Estoy ocupado pero deja tu mensaje después del tono y te llamo de vuelta. ¡Chao!",
            },
            {
                "titulo": "Con contexto de trabajo",
                "texto": "Hola, soy [nombre] de [empresa]. No puedo atender ahora. Deja tu nombre, empresa y motivo, y te contacto a la brevedad.",
            },
        ],
        "dato_clave": "Los usuarios que graban su propio saludo reciben recados 2.5x más completos que con voz genérica.",
    }


# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN Y HEALTH
# ═══════════════════════════════════════════════════════════

@router.post("/config")
async def actualizar_config(
    config: ConfiguracionUpdate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza configuración. Protegido."""
    existente = db.query(Configuracion).filter(Configuracion.clave == config.clave).first()
    if existente:
        existente.valor = config.valor
        existente.actualizado = datetime.now(timezone.utc)
    else:
        nueva = Configuracion(clave=config.clave, valor=config.valor)
        db.add(nueva)
    db.commit()
    return {"status": "ok", "clave": config.clave}


@router.get("/config")
async def obtener_config(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    configs = db.query(Configuracion).all()
    return {c.clave: c.valor for c in configs}


@router.get("/suscripcion/url")
async def obtener_url_suscripcion(
    usuario: Usuario = Depends(get_current_user),
):
    """Genera la URL de la página de suscripción con el token del usuario.

    La app abre esta URL en el navegador para que el usuario se suscriba
    sin necesidad de volver a iniciar sesión en la web.
    """
    from app.core.auth import create_access_token
    from app.core.config import settings

    # Crear un token de corta duración para la web (15 min)
    token = create_access_token(usuario.uid)
    url = f"{settings.BASE_URL}/suscripcion/planes?token={token}"
    return {"url": url, "plan_actual": usuario.plan}


@router.get("/health")
async def health_check():
    """Health check. Público."""
    return {"status": "healthy", "version": "1.0.0", "service": "FiltroLlamadas API"}


# ═══════════════════════════════════════════════════════════
# NUMERO TWILIO (auto-provisioning)
# ═══════════════════════════════════════════════════════════

@router.get("/mi-numero")
async def obtener_mi_numero(
    usuario: Usuario = Depends(get_current_user),
):
    """Obtiene el numero Twilio asignado al usuario."""
    return {
        "telefono_twilio": usuario.telefono_twilio,
        "tiene_numero": bool(usuario.telefono_twilio),
        "instrucciones": (
            "Configura desvio de llamadas en tu celular hacia este numero. "
            "Las llamadas desviadas seran atendidas por tu asistente IA."
        ) if usuario.telefono_twilio else (
            "Necesitas un plan activo para recibir un numero. "
            "Suscribete a un plan para obtener tu numero Twilio automaticamente."
        ),
    }


@router.post("/mi-numero/asignar")
async def asignar_mi_numero(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Asigna un numero Twilio al usuario. Se ejecuta automaticamente al activar plan.

    Body opcional: {codigo_pais: "US"} (default US)
    """
    from app.services.twilio_numbers import asignar_numero_a_usuario

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    codigo_pais = body.get("codigo_pais", "US")

    resultado = asignar_numero_a_usuario(db, usuario, codigo_pais)
    if not resultado:
        raise HTTPException(
            status_code=500,
            detail="No se pudo asignar un numero Twilio. Intenta de nuevo mas tarde."
        )

    return {
        "status": "ok",
        "telefono_twilio": resultado["phone_number"],
        "ya_asignado": resultado.get("ya_asignado", False),
        "instrucciones": (
            "Configura desvio de llamadas en tu celular hacia este numero. "
            "Las llamadas desviadas seran atendidas por tu asistente IA."
        ),
    }
