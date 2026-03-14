"""Servicio de integración con Flow.cl para pagos en Chile.

Flujo Flow.cl:
1. Usuario elige plan → se crea una orden de pago vía API
2. Flow retorna URL de pago → el usuario paga ahí
3. Flow redirige a nuestro return_url con el token
4. Recibimos confirmación vía webhook y activamos el plan

Soporta:
- WebPay (tarjetas crédito/débito chilenas)
- Servipag
- Multicaja
- Mach
- Khipu (transferencia bancaria)

Flow.cl usa firma HMAC-SHA256 para autenticar las requests.
"""
import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlencode

import requests as http_requests

from app.core.config import settings

logger = logging.getLogger(__name__)

# URLs base de Flow
FLOW_BASE_URL_SANDBOX = "https://sandbox.flow.cl/api"
FLOW_BASE_URL_LIVE = "https://www.flow.cl/api"

# Precios en CLP
PLANES_CLP = {
    "basico": {"mensual": 4490, "anual": 44900},
    "pro": {"mensual": 5490, "anual": 54900},
    "premium": {"mensual": 8990, "anual": 89900},
}


def _get_base_url() -> str:
    return FLOW_BASE_URL_SANDBOX if settings.FLOW_SANDBOX else FLOW_BASE_URL_LIVE


def _firmar_params(params: dict) -> str:
    """Genera la firma HMAC-SHA256 requerida por Flow.

    Flow exige que todos los parámetros se ordenen alfabéticamente,
    se concatenen como key=value con &, y se firmen con la secret key.
    """
    sorted_keys = sorted(params.keys())
    to_sign = "&".join(f"{k}={params[k]}" for k in sorted_keys)
    signature = hmac.new(
        settings.FLOW_SECRET_KEY.encode("utf-8"),
        to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return signature


def crear_orden_flow(
    usuario_uid: str,
    usuario_email: str,
    plan_codigo: str,
    periodo: str = "mensual",
) -> dict:
    """Crea una orden de pago en Flow.cl y retorna la URL de pago.

    Args:
        usuario_uid: UID del usuario
        usuario_email: Email del usuario
        plan_codigo: 'basico', 'pro' o 'premium'
        periodo: 'mensual' o 'anual'

    Returns:
        dict con url (URL de pago Flow), token, flowOrder, commerceOrder
    """
    if plan_codigo not in PLANES_CLP:
        raise ValueError(f"Plan inválido: {plan_codigo}")

    monto = PLANES_CLP[plan_codigo][periodo]
    commerce_order = f"CD-{usuario_uid[:8]}-{uuid.uuid4().hex[:6]}"
    subject = f"ContestaDora {plan_codigo.capitalize()} - {'Anual' if periodo == 'anual' else 'Mensual'}"

    params = {
        "apiKey": settings.FLOW_API_KEY,
        "commerceOrder": commerce_order,
        "subject": subject,
        "currency": "CLP",
        "amount": str(monto),
        "email": usuario_email,
        "urlConfirmation": f"{settings.BASE_URL}/webhooks/flow",
        "urlReturn": f"{settings.BASE_URL}/pagos/flow/retorno",
        "optional": f'{{"uid":"{usuario_uid}","plan":"{plan_codigo}","periodo":"{periodo}"}}',
    }

    params["s"] = _firmar_params(params)

    base = _get_base_url()
    resp = http_requests.post(f"{base}/payment/create", data=params, timeout=15)

    if resp.status_code != 200:
        logger.error(f"Flow crear orden error: {resp.status_code} - {resp.text[:300]}")
        raise Exception(f"Error creando orden en Flow: {resp.status_code}")

    data = resp.json()

    # Flow retorna url + token; el redirect final es url?token=xxx
    payment_url = f"{data['url']}?token={data['token']}"

    logger.info(f"Flow orden creada: {commerce_order}, monto=${monto} CLP")

    return {
        "url": payment_url,
        "token": data["token"],
        "flow_order": data.get("flowOrder"),
        "commerce_order": commerce_order,
        "monto_clp": monto,
    }


def obtener_estado_pago(token: str) -> Optional[dict]:
    """Consulta el estado de un pago en Flow.cl usando el token.

    Returns:
        dict con flowOrder, commerceOrder, status, amount, payer, etc.
    """
    params = {
        "apiKey": settings.FLOW_API_KEY,
        "token": token,
    }
    params["s"] = _firmar_params(params)

    base = _get_base_url()
    resp = http_requests.get(f"{base}/payment/getStatus", params=params, timeout=10)

    if resp.status_code != 200:
        logger.error(f"Flow getStatus error: {resp.status_code} - {resp.text[:200]}")
        return None

    return resp.json()


def procesar_pago_flow(token: str, db_session) -> dict:
    """Procesa un pago de Flow: consulta estado y activa el plan.

    Flow envía el token al webhook de confirmación.
    Status de Flow: 1=pendiente, 2=pagada, 3=rechazada, 4=anulada

    Returns:
        dict con el resultado
    """
    import json
    from app.models.database import Suscripcion, Usuario, EstadoSuscripcion

    estado = obtener_estado_pago(token)
    if not estado:
        return {"status": "error", "detail": "No se pudo consultar estado en Flow"}

    flow_status = estado.get("status", 0)
    commerce_order = estado.get("commerceOrder", "")
    monto = estado.get("amount", 0)

    # Parsear datos opcionales
    optional_str = estado.get("optional", "{}")
    try:
        optional = json.loads(optional_str) if isinstance(optional_str, str) else optional_str
    except json.JSONDecodeError:
        optional = {}

    usuario_uid = optional.get("uid", "")
    plan_codigo = optional.get("plan", "")
    periodo = optional.get("periodo", "mensual")

    if not usuario_uid or not plan_codigo:
        logger.error(f"Flow pago sin datos de usuario: {commerce_order}")
        return {"status": "error", "detail": "Datos de usuario no encontrados"}

    usuario = db_session.query(Usuario).filter(Usuario.uid == usuario_uid).first()
    if not usuario:
        return {"status": "error", "detail": "Usuario no encontrado"}

    # Crear suscripción
    suscripcion = Suscripcion(
        usuario_id=usuario.id,
        plan_codigo=plan_codigo,
        origen="flow",
        periodo=periodo,
        monto=monto,
        moneda="CLP",
        flow_order=str(estado.get("flowOrder", "")),
        flow_token=token,
    )

    # Status 2 = pagada/aprobada
    if flow_status == 2:
        suscripcion.estado = EstadoSuscripcion.ACTIVA.value
        suscripcion.fecha_inicio = datetime.now(timezone.utc)
        suscripcion.fecha_fin = (
            datetime.now(timezone.utc) + timedelta(days=365)
            if periodo == "anual"
            else datetime.now(timezone.utc) + timedelta(days=30)
        )

        usuario.plan = plan_codigo
        usuario.plan_expira = suscripcion.fecha_fin
        logger.info(f"Plan {plan_codigo} activado vía Flow para {usuario_uid}")

        if not usuario.telefono_twilio:
            try:
                from app.services.twilio_numbers import asignar_numero_a_usuario
                asignar_numero_a_usuario(db_session, usuario)
            except Exception as e:
                logger.error(f"Error auto-asignando Twilio: {e}")

    elif flow_status in (3, 4):
        suscripcion.estado = EstadoSuscripcion.RECHAZADA.value
    else:
        suscripcion.estado = EstadoSuscripcion.PENDIENTE.value

    db_session.add(suscripcion)
    db_session.commit()

    return {
        "status": "ok" if flow_status == 2 else "rechazado",
        "flow_status": flow_status,
        "plan": plan_codigo,
        "monto_clp": monto,
    }
