"""Servicio de integración con MercadoPago para suscripciones.

Flujo:
1. Usuario elige plan en la web → se crea una Preference de MercadoPago
2. MercadoPago redirige al usuario a pagar (Checkout Pro)
3. Tras el pago, MP redirige a nuestra URL de éxito/fallo
4. MP envía webhook (IPN) con el estado del pago → activamos el plan

Usa Checkout Pro (redirect) que soporta:
- Tarjetas de crédito/débito
- Transferencia bancaria
- Efectivo (en tiendas)
- Wallet MercadoPago
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests as http_requests

from app.core.config import settings

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# CREAR PREFERENCIA DE PAGO (Checkout Pro)
# ═══════════════════════════════════════════════════════════

PLANES_CONFIG = {
    "pro": {
        "titulo": "FiltroLlamadas Pro",
        "descripcion": "200 llamadas/mes, voces IA, modo luna, calendario",
        "precio_mensual": 4.99,
        "precio_anual": 49.99,
    },
    "premium": {
        "titulo": "FiltroLlamadas Premium",
        "descripcion": "Ilimitado, soporte prioritario, todas las funciones",
        "precio_mensual": 12.99,
        "precio_anual": 129.99,
    },
}


def crear_preferencia_pago(
    usuario_uid: str,
    usuario_email: str,
    plan_codigo: str,
    periodo: str = "mensual",
) -> dict:
    """Crea una Preference en MercadoPago y retorna la URL de pago.

    Args:
        usuario_uid: UID del usuario
        usuario_email: Email del usuario
        plan_codigo: 'pro' o 'premium'
        periodo: 'mensual' o 'anual'

    Returns:
        dict con preference_id, init_point (URL de pago), external_reference
    """
    if plan_codigo not in PLANES_CONFIG:
        raise ValueError(f"Plan inválido: {plan_codigo}")

    plan = PLANES_CONFIG[plan_codigo]
    precio = plan["precio_anual"] if periodo == "anual" else plan["precio_mensual"]
    titulo = f"{plan['titulo']} - {'Anual' if periodo == 'anual' else 'Mensual'}"

    # Referencia externa única para rastrear este pago
    external_ref = f"fl_{usuario_uid}_{plan_codigo}_{periodo}_{uuid.uuid4().hex[:8]}"

    # URLs de retorno tras el pago
    base = settings.BASE_URL
    back_urls = {
        "success": f"{base}/suscripcion/resultado?status=approved&ref={external_ref}",
        "failure": f"{base}/suscripcion/resultado?status=rejected&ref={external_ref}",
        "pending": f"{base}/suscripcion/resultado?status=pending&ref={external_ref}",
    }

    preference_data = {
        "items": [
            {
                "title": titulo,
                "description": plan["descripcion"],
                "quantity": 1,
                "currency_id": "USD",
                "unit_price": precio,
            }
        ],
        "payer": {
            "email": usuario_email,
        },
        "back_urls": back_urls,
        "auto_return": "approved",
        "external_reference": external_ref,
        "notification_url": f"{base}/webhooks/mercadopago",
        "statement_descriptor": "FiltroLlamadas",
        "expires": True,
        "expiration_date_from": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000-00:00"),
        "expiration_date_to": (datetime.now(timezone.utc) + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00"),
    }

    resp = http_requests.post(
        "https://api.mercadopago.com/checkout/preferences",
        json=preference_data,
        headers={
            "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        timeout=15,
    )

    if resp.status_code not in (200, 201):
        logger.error(f"MercadoPago preference error: {resp.status_code} - {resp.text[:300]}")
        raise Exception(f"Error creando preferencia de pago: {resp.status_code}")

    data = resp.json()
    logger.info(f"MercadoPago preference creada: {data['id']} para {usuario_uid}")

    return {
        "preference_id": data["id"],
        "init_point": data["init_point"],  # URL de pago (producción)
        "sandbox_init_point": data.get("sandbox_init_point", ""),  # URL sandbox
        "external_reference": external_ref,
    }


# ═══════════════════════════════════════════════════════════
# CONSULTAR ESTADO DE PAGO
# ═══════════════════════════════════════════════════════════

def obtener_pago(payment_id: str) -> Optional[dict]:
    """Consulta el estado de un pago en MercadoPago."""
    resp = http_requests.get(
        f"https://api.mercadopago.com/v1/payments/{payment_id}",
        headers={"Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"},
        timeout=10,
    )

    if resp.status_code != 200:
        logger.error(f"Error consultando pago {payment_id}: {resp.status_code}")
        return None

    return resp.json()


def buscar_pago_por_referencia(external_reference: str) -> Optional[dict]:
    """Busca un pago por external_reference."""
    resp = http_requests.get(
        "https://api.mercadopago.com/v1/payments/search",
        params={"external_reference": external_reference},
        headers={"Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"},
        timeout=10,
    )

    if resp.status_code != 200:
        return None

    data = resp.json()
    resultados = data.get("results", [])
    if resultados:
        return resultados[0]
    return None


# ═══════════════════════════════════════════════════════════
# PROCESAR WEBHOOK (IPN)
# ═══════════════════════════════════════════════════════════

def procesar_notificacion_pago(payment_id: str, db_session) -> dict:
    """Procesa una notificación de pago de MercadoPago.

    Busca el pago, verifica el estado, y activa/desactiva el plan del usuario.

    Returns:
        dict con el resultado del procesamiento
    """
    from app.models.database import Suscripcion, Usuario, EstadoSuscripcion

    pago = obtener_pago(payment_id)
    if not pago:
        return {"status": "error", "detail": "Pago no encontrado"}

    external_ref = pago.get("external_reference", "")
    estado_mp = pago.get("status", "")
    monto = pago.get("transaction_amount", 0)
    moneda = pago.get("currency_id", "USD")

    logger.info(f"Procesando pago {payment_id}: estado={estado_mp}, ref={external_ref}")

    # Parsear external_reference: fl_{uid}_{plan}_{periodo}_{random}
    partes = external_ref.split("_")
    if len(partes) < 4 or partes[0] != "fl":
        logger.warning(f"External reference inválida: {external_ref}")
        return {"status": "error", "detail": "Referencia inválida"}

    usuario_uid = partes[1]
    plan_codigo = partes[2]
    periodo = partes[3]

    # Buscar usuario
    usuario = db_session.query(Usuario).filter(Usuario.uid == usuario_uid).first()
    if not usuario:
        return {"status": "error", "detail": "Usuario no encontrado"}

    # Buscar o crear suscripción
    suscripcion = db_session.query(Suscripcion).filter(
        Suscripcion.mp_external_reference == external_ref
    ).first()

    if not suscripcion:
        suscripcion = Suscripcion(
            usuario_id=usuario.id,
            plan_codigo=plan_codigo,
            origen="mercadopago",
            mp_external_reference=external_ref,
            periodo=periodo,
            monto=monto,
            moneda=moneda,
        )
        db_session.add(suscripcion)

    suscripcion.mp_payment_id = str(payment_id)

    # Mapear estado de MercadoPago a nuestro estado
    if estado_mp == "approved":
        suscripcion.estado = EstadoSuscripcion.ACTIVA.value
        suscripcion.fecha_inicio = datetime.now(timezone.utc)

        if periodo == "anual":
            suscripcion.fecha_fin = datetime.now(timezone.utc) + timedelta(days=365)
        else:
            suscripcion.fecha_fin = datetime.now(timezone.utc) + timedelta(days=30)

        # Activar plan del usuario
        usuario.plan = plan_codigo
        usuario.plan_expira = suscripcion.fecha_fin
        logger.info(f"Plan {plan_codigo} activado para {usuario_uid} hasta {suscripcion.fecha_fin}")

    elif estado_mp in ("rejected", "cancelled"):
        suscripcion.estado = EstadoSuscripcion.RECHAZADA.value

    elif estado_mp in ("pending", "in_process"):
        suscripcion.estado = EstadoSuscripcion.PENDIENTE.value

    db_session.commit()

    return {
        "status": "ok",
        "payment_status": estado_mp,
        "plan": plan_codigo,
        "usuario_uid": usuario_uid,
    }
