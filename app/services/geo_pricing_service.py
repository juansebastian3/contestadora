"""Servicio de Pricing Dinámico por Geografía (PPP).

Precios ajustados por paridad de poder adquisitivo para LATAM:
- Chile (CL): Pro $6.99 USD → ~$5,490 CLP
- Colombia (CO): Pro $5.99 USD → ~$23,900 COP
- Argentina (AR): Pro $4.99 USD → ~$4,990 ARS (ajustado)
- México (MX): Pro $5.99 USD → ~$99 MXN
- Perú (PE): Pro $5.49 USD → ~$19.90 PEN

Annual billing: -20% descuento ($67/año vs $84).

Métricas objetivo:
- Conversion rate +20-30% en mercados sensibles al precio
- Annual suscripciones = 2x LTV
- Conversion rate por país
- % annual vs monthly
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database import PrecioGeografico, Usuario, Plan

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# TABLA DE PRECIOS PPP POR PAÍS
# ═══════════════════════════════════════════════════════════

PRECIOS_PPP = {
    "CL": {
        "pais_nombre": "Chile",
        "moneda": "CLP",
        "basico": {"mensual": 3490, "usd": 3.99},
        "pro":    {"mensual": 5490, "usd": 6.99},
        "premium": {"mensual": 7990, "usd": 9.99},
    },
    "CO": {
        "pais_nombre": "Colombia",
        "moneda": "COP",
        "basico": {"mensual": 19900, "usd": 3.99},
        "pro":    {"mensual": 23900, "usd": 5.99},
        "premium": {"mensual": 39900, "usd": 7.99},
    },
    "AR": {
        "pais_nombre": "Argentina",
        "moneda": "ARS",
        "basico": {"mensual": 3990, "usd": 2.99},
        "pro":    {"mensual": 4990, "usd": 4.99},
        "premium": {"mensual": 7990, "usd": 6.99},
    },
    "MX": {
        "pais_nombre": "México",
        "moneda": "MXN",
        "basico": {"mensual": 79, "usd": 3.99},
        "pro":    {"mensual": 99, "usd": 5.99},
        "premium": {"mensual": 169, "usd": 8.99},
    },
    "PE": {
        "pais_nombre": "Perú",
        "moneda": "PEN",
        "basico": {"mensual": 14.90, "usd": 3.99},
        "pro":    {"mensual": 19.90, "usd": 5.49},
        "premium": {"mensual": 34.90, "usd": 8.99},
    },
    "EC": {
        "pais_nombre": "Ecuador",
        "moneda": "USD",
        "basico": {"mensual": 3.99, "usd": 3.99},
        "pro":    {"mensual": 5.99, "usd": 5.99},
        "premium": {"mensual": 8.99, "usd": 8.99},
    },
    "DEFAULT": {
        "pais_nombre": "Internacional",
        "moneda": "USD",
        "basico": {"mensual": 4.99, "usd": 4.99},
        "pro":    {"mensual": 6.99, "usd": 6.99},
        "premium": {"mensual": 9.99, "usd": 9.99},
    },
}

DESCUENTO_ANUAL = 0.20  # 20% descuento por pago anual


# ═══════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES
# ═══════════════════════════════════════════════════════════

def seed_precios_geograficos(db: Session):
    """Puebla la tabla de precios geográficos con los datos PPP.

    Se ejecuta en el startup de la app.
    """
    for pais_codigo, datos in PRECIOS_PPP.items():
        if pais_codigo == "DEFAULT":
            continue

        existente = db.query(PrecioGeografico).filter(
            PrecioGeografico.pais_codigo == pais_codigo
        ).first()

        valores = {
            "pais_codigo": pais_codigo,
            "pais_nombre": datos["pais_nombre"],
            "moneda": datos["moneda"],
            "precio_basico_mensual": datos["basico"]["mensual"],
            "precio_pro_mensual": datos["pro"]["mensual"],
            "precio_premium_mensual": datos["premium"]["mensual"],
            "precio_basico_anual": round(datos["basico"]["mensual"] * 12 * (1 - DESCUENTO_ANUAL), 2),
            "precio_pro_anual": round(datos["pro"]["mensual"] * 12 * (1 - DESCUENTO_ANUAL), 2),
            "precio_premium_anual": round(datos["premium"]["mensual"] * 12 * (1 - DESCUENTO_ANUAL), 2),
            "precio_basico_usd": datos["basico"]["usd"],
            "precio_pro_usd": datos["pro"]["usd"],
            "precio_premium_usd": datos["premium"]["usd"],
        }

        if existente:
            for key, val in valores.items():
                setattr(existente, key, val)
            existente.actualizado = datetime.now(timezone.utc)
        else:
            db.add(PrecioGeografico(**valores))

    db.commit()
    logger.info("Precios geográficos PPP inicializados")


def obtener_precios_por_pais(db: Session, pais_codigo: str) -> dict:
    """Obtiene precios adaptados al país del usuario.

    Args:
        pais_codigo: ISO country code (CL, CO, AR, MX, PE...)

    Returns:
        dict con precios mensuales y anuales por plan en moneda local + USD.
    """
    pais_codigo = (pais_codigo or "DEFAULT").upper()

    # Buscar en DB primero (puede estar personalizado)
    geo = db.query(PrecioGeografico).filter(
        PrecioGeografico.pais_codigo == pais_codigo,
        PrecioGeografico.activo == True,
    ).first()

    if geo:
        return {
            "pais": geo.pais_codigo,
            "pais_nombre": geo.pais_nombre,
            "moneda": geo.moneda,
            "planes": {
                "basico": {
                    "mensual": geo.precio_basico_mensual,
                    "anual": geo.precio_basico_anual,
                    "mensual_usd": geo.precio_basico_usd,
                    "ahorro_anual_pct": round(DESCUENTO_ANUAL * 100),
                },
                "pro": {
                    "mensual": geo.precio_pro_mensual,
                    "anual": geo.precio_pro_anual,
                    "mensual_usd": geo.precio_pro_usd,
                    "ahorro_anual_pct": round(DESCUENTO_ANUAL * 100),
                },
                "premium": {
                    "mensual": geo.precio_premium_mensual,
                    "anual": geo.precio_premium_anual,
                    "mensual_usd": geo.precio_premium_usd,
                    "ahorro_anual_pct": round(DESCUENTO_ANUAL * 100),
                },
            },
        }

    # Fallback a tabla estática
    datos = PRECIOS_PPP.get(pais_codigo, PRECIOS_PPP["DEFAULT"])
    return _formatear_precios_ppp(pais_codigo, datos)


def _formatear_precios_ppp(pais_codigo: str, datos: dict) -> dict:
    """Formatea datos PPP estáticos al formato de respuesta."""
    resultado = {
        "pais": pais_codigo,
        "pais_nombre": datos["pais_nombre"],
        "moneda": datos["moneda"],
        "planes": {},
    }
    for plan in ["basico", "pro", "premium"]:
        mensual = datos[plan]["mensual"]
        resultado["planes"][plan] = {
            "mensual": mensual,
            "anual": round(mensual * 12 * (1 - DESCUENTO_ANUAL), 2),
            "mensual_usd": datos[plan]["usd"],
            "ahorro_anual_pct": round(DESCUENTO_ANUAL * 100),
        }
    return resultado


def detectar_pais_por_telefono(telefono: str) -> str:
    """Detecta el país del usuario por su código telefónico.

    Mapeo de códigos de área a países LATAM.
    """
    prefijos = {
        "+56": "CL",   # Chile
        "+57": "CO",   # Colombia
        "+54": "AR",   # Argentina
        "+52": "MX",   # México
        "+51": "PE",   # Perú
        "+593": "EC",  # Ecuador
        "+58": "VE",   # Venezuela
        "+55": "BR",   # Brasil
        "+591": "BO",  # Bolivia
        "+595": "PY",  # Paraguay
        "+598": "UY",  # Uruguay
        "+506": "CR",  # Costa Rica
        "+507": "PA",  # Panamá
        "+503": "SV",  # El Salvador
        "+502": "GT",  # Guatemala
        "+504": "HN",  # Honduras
        "+505": "NI",  # Nicaragua
        "+1": "US",    # USA/Canadá
    }

    for prefijo, pais in sorted(prefijos.items(), key=lambda x: -len(x[0])):
        if telefono.startswith(prefijo):
            return pais

    return "DEFAULT"


def obtener_precio_para_usuario(db: Session, usuario: Usuario, plan: str, periodo: str = "mensual") -> dict:
    """Obtiene el precio exacto que debe pagar un usuario.

    Considera país del usuario + periodo (mensual/anual).

    Returns:
        dict con monto, moneda, equivalente_usd, ahorro_vs_mensual.
    """
    pais = usuario.pais_codigo or detectar_pais_por_telefono(usuario.telefono)
    precios = obtener_precios_por_pais(db, pais)

    if plan not in precios["planes"]:
        # Fallback a precios default USD
        precios = obtener_precios_por_pais(db, "DEFAULT")

    plan_precios = precios["planes"].get(plan, precios["planes"]["pro"])

    if periodo == "anual":
        monto = plan_precios["anual"]
        ahorro = round(plan_precios["mensual"] * 12 - monto, 2)
    else:
        monto = plan_precios["mensual"]
        ahorro = 0

    return {
        "plan": plan,
        "periodo": periodo,
        "monto": monto,
        "moneda": precios["moneda"],
        "equivalente_usd_mensual": plan_precios["mensual_usd"],
        "ahorro_vs_mensual": ahorro,
        "pais": precios["pais"],
        "pais_nombre": precios["pais_nombre"],
    }


# ═══════════════════════════════════════════════════════════
# MÉTRICAS
# ═══════════════════════════════════════════════════════════

def obtener_metricas_geo_pricing(db: Session) -> dict:
    """Métricas de conversión por país y tipo de billing.

    Returns:
        dict con conversion rates por país, % annual vs monthly, etc.
    """
    from app.models.database import Suscripcion, EstadoSuscripcion

    total_usuarios = db.query(Usuario).filter(Usuario.activo == True).count()
    total_suscripciones = db.query(Suscripcion).filter(
        Suscripcion.estado == EstadoSuscripcion.ACTIVA.value
    ).count()

    # Breakdown por país
    paises = db.query(Usuario.pais_codigo).distinct().all()
    por_pais = {}
    for (pais,) in paises:
        if not pais:
            continue
        usuarios_pais = db.query(Usuario).filter(
            Usuario.pais_codigo == pais,
            Usuario.activo == True,
        ).count()
        suscripciones_pais = db.query(Suscripcion).join(Usuario).filter(
            Usuario.pais_codigo == pais,
            Suscripcion.estado == EstadoSuscripcion.ACTIVA.value,
        ).count()
        por_pais[pais] = {
            "usuarios": usuarios_pais,
            "suscripciones_activas": suscripciones_pais,
            "conversion_rate": round(suscripciones_pais / usuarios_pais * 100, 1) if usuarios_pais > 0 else 0,
        }

    # Annual vs monthly
    annual = db.query(Suscripcion).filter(
        Suscripcion.estado == EstadoSuscripcion.ACTIVA.value,
        Suscripcion.periodo == "anual",
    ).count()
    monthly = db.query(Suscripcion).filter(
        Suscripcion.estado == EstadoSuscripcion.ACTIVA.value,
        Suscripcion.periodo == "mensual",
    ).count()

    return {
        "total_usuarios": total_usuarios,
        "total_suscripciones": total_suscripciones,
        "conversion_global": round(total_suscripciones / total_usuarios * 100, 1) if total_usuarios > 0 else 0,
        "por_pais": por_pais,
        "billing_tipo": {
            "annual": annual,
            "monthly": monthly,
            "pct_annual": round(annual / (annual + monthly) * 100, 1) if (annual + monthly) > 0 else 0,
        },
    }
