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
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from fastapi import UploadFile, File
from pathlib import Path
import shutil

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
            "modo_asistente": usuario.modo_asistente or "ia_conversacional",
            "prompt_personalizado": usuario.prompt_personalizado,
            "tiene_audio_saludo": bool(usuario.audio_saludo_url),
            "audio_saludo_url": usuario.audio_saludo_url,
            "audio_saludo_duracion": usuario.audio_saludo_duracion,
        },
        "contactos_conocidos_count": len(usuario.contactos_conocidos or []),
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
        modo_asistente=usuario.modo_asistente or ModoAsistente.IA_CONVERSACIONAL.value,
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
    """Cambiar el modo del asistente: ia_conversacional, contestadora, hibrido.

    - ia_conversacional: Sofía conversa normalmente con el llamante
    - contestadora: Reproduce audio grabado del usuario, IA solo escucha y transcribe
    - hibrido: Reproduce audio grabado como saludo, luego IA toma el control
    """
    modos_validos = [m.value for m in ModoAsistente]
    if data.modo not in modos_validos:
        raise HTTPException(status_code=400, detail=f"Modo inválido. Opciones: {modos_validos}")

    # Contestadora e híbrido requieren audio grabado
    if data.modo in (ModoAsistente.CONTESTADORA.value, ModoAsistente.HIBRIDO.value):
        if not usuario.audio_saludo_url:
            raise HTTPException(
                status_code=400,
                detail="Para usar modo contestadora o híbrido, primero sube tu audio de saludo."
            )

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
    """Eliminar audio de saludo. Si el modo es contestadora/híbrido, vuelve a ia_conversacional."""
    if usuario.audio_saludo_url:
        # Intentar borrar archivo físico
        upload_dir = Path(f"./audio_uploads/{usuario.uid}")
        if upload_dir.exists():
            shutil.rmtree(upload_dir, ignore_errors=True)

    usuario.audio_saludo_url = None
    usuario.audio_saludo_duracion = None

    # Si estaba en modo que requiere audio, volver a IA conversacional
    if usuario.modo_asistente in (ModoAsistente.CONTESTADORA.value, ModoAsistente.HIBRIDO.value):
        usuario.modo_asistente = ModoAsistente.IA_CONVERSACIONAL.value

    db.commit()
    return {"status": "ok", "modo_asistente": usuario.modo_asistente}


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


@router.get("/health")
async def health_check():
    """Health check. Público."""
    return {"status": "healthy", "version": "1.0.0", "service": "FiltroLlamadas API"}
