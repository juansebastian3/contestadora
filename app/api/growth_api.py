"""API endpoints para Growth: Referidos, Descuentos, Geo-Pricing, Drip Campaigns, Twilio Auto-Release.

Endpoints públicos:
- GET /api/v1/precios/{pais}          → Precios por país (PPP)
- GET /api/v1/referido/{codigo}       → Info de un código de referido
- POST /api/v1/descuento/validar      → Validar código de descuento

Endpoints protegidos (JWT):
- GET  /api/v1/mi-referido            → Mi código y link de referido
- GET  /api/v1/mis-referidos/stats    → Estadísticas de mis referidos
- POST /api/v1/descuento/aplicar      → Aplicar código de descuento a compra
- GET  /api/v1/precios/mi-plan        → Precio personalizado para mi país
- POST /api/v1/mi-numero/reactivar    → Reactivar número Twilio (post auto-release)

Endpoints admin (internos):
- POST /api/v1/admin/descuento/crear  → Crear código de descuento
- POST /api/v1/admin/drip/procesar    → Procesar drip campaigns pendientes
- POST /api/v1/admin/twilio/release   → Ejecutar auto-release de números
- GET  /api/v1/admin/metricas/referidos    → Métricas de referidos
- GET  /api/v1/admin/metricas/retencion    → Métricas de retención por cohorte
- GET  /api/v1/admin/metricas/geo-pricing  → Métricas de conversión por país
- GET  /api/v1/admin/metricas/twilio       → Métricas de números Twilio
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.models.database import get_db, Usuario

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Growth & Monetización"])


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class ValidarDescuentoRequest(BaseModel):
    codigo: str = Field(..., examples=["DORA50-WELCOME"])
    plan: Optional[str] = Field(None, examples=["pro"])


class AplicarDescuentoRequest(BaseModel):
    codigo: str = Field(..., examples=["DORA50-WELCOME"])
    monto_original: float = Field(..., examples=[6.99])
    plan: Optional[str] = Field(None, examples=["pro"])


class CrearDescuentoRequest(BaseModel):
    tipo: str = Field("porcentaje", examples=["porcentaje"])
    valor: float = Field(50, examples=[50])
    meses_gratis: int = Field(0, examples=[1])
    plan_aplicable: Optional[str] = Field(None, examples=["pro"])
    usos_maximos: int = Field(0, examples=[100])
    descripcion: str = Field("", examples=["50% off primer mes"])
    dias_validez: int = Field(30, examples=[30])
    prefijo: str = Field("FILTRO", examples=["DORA50"])


# ═══════════════════════════════════════════════════════════
# REFERIDOS (público + protegido)
# ═══════════════════════════════════════════════════════════

@router.get("/api/v1/referido/{codigo}")
async def info_referido(codigo: str, db: Session = Depends(get_db)):
    """Info pública de un código de referido (para landing de registro)."""
    referidor = db.query(Usuario).filter(Usuario.codigo_referido == codigo).first()
    if not referidor:
        raise HTTPException(status_code=404, detail="Código de referido no encontrado")

    return {
        "valido": True,
        "referidor_nombre": referidor.nombre.split()[0],  # Solo primer nombre
        "beneficio": "1 mes gratis para ti y para quien te invitó",
    }


@router.get("/api/v1/mi-referido")
async def mi_link_referido(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtiene el código y link de referido del usuario autenticado."""
    from app.services.referidos_service import obtener_link_referido
    return obtener_link_referido(db, usuario, settings.BASE_URL)


@router.get("/api/v1/mis-referidos/stats")
async def stats_referidos(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Estadísticas del programa de referidos del usuario."""
    from app.services.referidos_service import obtener_stats_referidos
    return obtener_stats_referidos(db, usuario)


# ═══════════════════════════════════════════════════════════
# CÓDIGOS DE DESCUENTO
# ═══════════════════════════════════════════════════════════

@router.post("/api/v1/descuento/validar")
async def validar_descuento(
    data: ValidarDescuentoRequest,
    db: Session = Depends(get_db),
):
    """Valida un código de descuento (público, para mostrar en checkout)."""
    from app.services.referidos_service import validar_codigo_descuento
    resultado = validar_codigo_descuento(db, data.codigo, data.plan)
    if not resultado:
        raise HTTPException(status_code=404, detail="Código inválido o expirado")
    return resultado


@router.post("/api/v1/descuento/aplicar")
async def aplicar_descuento(
    data: AplicarDescuentoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aplica un código de descuento a una compra."""
    from app.services.referidos_service import aplicar_codigo_descuento
    resultado = aplicar_codigo_descuento(
        db, usuario, data.codigo, data.monto_original, data.plan
    )
    if not resultado:
        raise HTTPException(status_code=400, detail="Código inválido o ya usado")
    return resultado


@router.post("/api/v1/admin/descuento/crear")
async def crear_descuento(
    data: CrearDescuentoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea un nuevo código de descuento (admin only)."""
    # TODO: Implementar verificación de admin real
    from app.services.referidos_service import crear_codigo_descuento
    codigo = crear_codigo_descuento(
        db,
        tipo=data.tipo,
        valor=data.valor,
        meses_gratis=data.meses_gratis,
        plan_aplicable=data.plan_aplicable,
        usos_maximos=data.usos_maximos,
        descripcion=data.descripcion,
        dias_validez=data.dias_validez,
        prefijo=data.prefijo,
    )
    return {
        "codigo": codigo.codigo,
        "tipo": codigo.tipo,
        "valor": codigo.valor,
        "usos_maximos": codigo.usos_maximos,
        "fecha_fin": codigo.fecha_fin.isoformat() if codigo.fecha_fin else None,
    }


# ═══════════════════════════════════════════════════════════
# GEO-PRICING
# ═══════════════════════════════════════════════════════════

@router.get("/api/v1/precios/{pais}")
async def precios_por_pais(pais: str, db: Session = Depends(get_db)):
    """Obtiene precios adaptados por país (PPP).

    Ejemplo: /api/v1/precios/CL → precios en CLP para Chile.
    """
    from app.services.geo_pricing_service import obtener_precios_por_pais
    return obtener_precios_por_pais(db, pais)


@router.get("/api/v1/precios/mi-plan")
async def precio_personalizado(
    plan: str = Query("pro", description="Código del plan"),
    periodo: str = Query("mensual", description="mensual o anual"),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtiene el precio personalizado para el usuario según su país."""
    from app.services.geo_pricing_service import obtener_precio_para_usuario
    return obtener_precio_para_usuario(db, usuario, plan, periodo)


# ═══════════════════════════════════════════════════════════
# REACTIVACIÓN TWILIO
# ═══════════════════════════════════════════════════════════

@router.post("/api/v1/mi-numero/reactivar")
async def reactivar_numero_twilio(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reactiva un número Twilio después de auto-release por inactividad."""
    from app.services.twilio_auto_release_service import reactivar_numero
    from app.services.geo_pricing_service import detectar_pais_por_telefono

    pais = detectar_pais_por_telefono(usuario.telefono)
    # Mapear país a código Twilio
    pais_twilio = {"CL": "CL", "CO": "CO", "AR": "AR", "MX": "MX"}.get(pais, "US")

    resultado = reactivar_numero(db, usuario, pais_twilio)
    if not resultado:
        raise HTTPException(status_code=500, detail="No se pudo asignar un nuevo número Twilio")
    return resultado


# ═══════════════════════════════════════════════════════════
# ADMIN: DRIP CAMPAIGNS
# ═══════════════════════════════════════════════════════════

@router.post("/api/v1/admin/drip/procesar")
async def procesar_drips(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Procesa y envía drip campaigns pendientes (cron job)."""
    from app.services.drip_campaigns_service import procesar_drips_pendientes
    enviados = procesar_drips_pendientes(db)
    return {"enviados": enviados}


# ═══════════════════════════════════════════════════════════
# ADMIN: TWILIO AUTO-RELEASE
# ═══════════════════════════════════════════════════════════

@router.post("/api/v1/admin/twilio/release")
async def ejecutar_release(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ejecuta el proceso de auto-release de números Twilio inactivos."""
    from app.services.twilio_auto_release_service import ejecutar_auto_release
    return ejecutar_auto_release(db)


# ═══════════════════════════════════════════════════════════
# ADMIN: MÉTRICAS
# ═══════════════════════════════════════════════════════════

@router.get("/api/v1/admin/metricas/referidos")
async def metricas_referidos_global(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Métricas globales del programa de referidos."""
    from app.models.database import Referido, EstadoReferido

    total = db.query(Referido).count()
    convertidos = db.query(Referido).filter(
        Referido.estado == EstadoReferido.CONVERTIDO.value
    ).count()
    usuarios_con_codigo = db.query(Usuario).filter(
        Usuario.codigo_referido.isnot(None)
    ).count()
    total_usuarios = db.query(Usuario).filter(Usuario.activo == True).count()

    return {
        "total_referidos": total,
        "convertidos": convertidos,
        "tasa_conversion": round(convertidos / total * 100, 1) if total > 0 else 0,
        "referral_rate": round(usuarios_con_codigo / total_usuarios * 100, 1) if total_usuarios > 0 else 0,
        "meses_gratis_otorgados": convertidos * 2,  # 1 mes para cada lado
        "cac_estimado_referidos": 0,  # $0 CAC por usuario referido
    }


@router.get("/api/v1/admin/metricas/retencion")
async def metricas_retencion(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Métricas de retención D7/D30/D90 por cohorte semanal."""
    from app.services.drip_campaigns_service import obtener_metricas_retencion
    return obtener_metricas_retencion(db)


@router.get("/api/v1/admin/metricas/geo-pricing")
async def metricas_geo(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Métricas de conversión por país y tipo de billing."""
    from app.services.geo_pricing_service import obtener_metricas_geo_pricing
    return obtener_metricas_geo_pricing(db)


@router.get("/api/v1/admin/metricas/twilio")
async def metricas_twilio(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Métricas de uso y costo de números Twilio."""
    from app.services.twilio_auto_release_service import obtener_metricas_twilio
    return obtener_metricas_twilio(db)
