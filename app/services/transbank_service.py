"""Servicio de integración con Transbank WebPay Plus para pagos en Chile.

Flujo WebPay Plus:
1. Usuario elige plan → se crea una transacción en WebPay
2. WebPay retorna un token + URL de formulario
3. El usuario paga en el formulario de WebPay (tarjetas chilenas)
4. WebPay redirige a nuestro return_url con el token
5. Confirmamos la transacción y activamos el plan

Soporta:
- Tarjetas de crédito chilenas (Visa, Mastercard, Amex)
- Tarjetas de débito (Redcompra)
- Prepago
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


# Precios en CLP (pesos chilenos)
PLANES_CLP = {
    "basico": {"mensual": 4490, "anual": 44900},
    "pro": {"mensual": 5490, "anual": 54900},
    "premium": {"mensual": 8990, "anual": 89900},
}


def _get_transaction_client():
    """Obtiene el cliente WebPay configurado según el entorno."""
    from transbank.webpay.webpay_plus.transaction import Transaction
    from transbank.common.integration_type import IntegrationType
    from transbank.common.options import WebpayOptions

    if settings.TRANSBANK_SANDBOX:
        # Modo integración/testing
        return Transaction(
            WebpayOptions(
                commerce_code="597055555532",
                api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
                integration_type=IntegrationType.TEST,
            )
        )
    else:
        return Transaction(
            WebpayOptions(
                commerce_code=settings.TRANSBANK_COMMERCE_CODE,
                api_key=settings.TRANSBANK_API_KEY,
                integration_type=IntegrationType.LIVE,
            )
        )


def crear_transaccion_webpay(
    usuario_uid: str,
    plan_codigo: str,
    periodo: str = "mensual",
) -> dict:
    """Crea una transacción WebPay Plus y retorna token + URL del formulario.

    Args:
        usuario_uid: UID del usuario
        plan_codigo: 'basico', 'pro' o 'premium'
        periodo: 'mensual' o 'anual'

    Returns:
        dict con token, url (formulario WebPay), buy_order
    """
    if plan_codigo not in PLANES_CLP:
        raise ValueError(f"Plan inválido: {plan_codigo}")

    monto = PLANES_CLP[plan_codigo][periodo]
    buy_order = f"CD-{usuario_uid[:8]}-{uuid.uuid4().hex[:6]}"
    session_id = f"s-{usuario_uid}"
    return_url = f"{settings.BASE_URL}/pagos/transbank/retorno"

    tx = _get_transaction_client()
    response = tx.create(buy_order, session_id, monto, return_url)

    logger.info(f"WebPay transacción creada: order={buy_order}, monto=${monto} CLP")

    return {
        "token": response.token,
        "url": response.url,
        "buy_order": buy_order,
        "monto_clp": monto,
    }


def confirmar_transaccion_webpay(token: str) -> dict:
    """Confirma una transacción WebPay tras el retorno del formulario.

    Args:
        token: Token retornado por WebPay en el redirect

    Returns:
        dict con estado, buy_order, monto, authorization_code, etc.
    """
    tx = _get_transaction_client()
    response = tx.commit(token)

    resultado = {
        "buy_order": response.buy_order,
        "session_id": response.session_id,
        "monto": response.amount,
        "status": response.status,
        "authorization_code": response.authorization_code,
        "response_code": response.response_code,
        "payment_type_code": response.payment_type_code,
        "transaction_date": str(response.transaction_date),
        "aprobado": response.response_code == 0,
    }

    logger.info(f"WebPay confirmación: order={response.buy_order}, status={response.status}, code={response.response_code}")
    return resultado


def procesar_pago_transbank(token: str, db_session, usuario_uid: str, plan_codigo: str, periodo: str) -> dict:
    """Procesa un pago de Transbank end-to-end: confirma y activa el plan.

    Returns:
        dict con el resultado del procesamiento
    """
    from app.models.database import Suscripcion, Usuario, EstadoSuscripcion

    resultado = confirmar_transaccion_webpay(token)

    usuario = db_session.query(Usuario).filter(Usuario.uid == usuario_uid).first()
    if not usuario:
        return {"status": "error", "detail": "Usuario no encontrado"}

    # Crear suscripción
    suscripcion = Suscripcion(
        usuario_id=usuario.id,
        plan_codigo=plan_codigo,
        origen="transbank",
        periodo=periodo,
        monto=resultado["monto"],
        moneda="CLP",
        tbk_buy_order=resultado["buy_order"],
        tbk_authorization_code=resultado.get("authorization_code"),
    )

    if resultado["aprobado"]:
        suscripcion.estado = EstadoSuscripcion.ACTIVA.value
        suscripcion.fecha_inicio = datetime.now(timezone.utc)
        suscripcion.fecha_fin = (
            datetime.now(timezone.utc) + timedelta(days=365)
            if periodo == "anual"
            else datetime.now(timezone.utc) + timedelta(days=30)
        )

        usuario.plan = plan_codigo
        usuario.plan_expira = suscripcion.fecha_fin
        logger.info(f"Plan {plan_codigo} activado vía WebPay para {usuario_uid}")

        # Auto-asignar número Twilio si no tiene
        if not usuario.telefono_twilio:
            try:
                from app.services.twilio_numbers import asignar_numero_a_usuario
                asignar_numero_a_usuario(db_session, usuario)
            except Exception as e:
                logger.error(f"Error auto-asignando Twilio: {e}")
    else:
        suscripcion.estado = EstadoSuscripcion.RECHAZADA.value

    db_session.add(suscripcion)
    db_session.commit()

    return {
        "status": "ok" if resultado["aprobado"] else "rechazado",
        "plan": plan_codigo,
        "monto_clp": resultado["monto"],
        "authorization_code": resultado.get("authorization_code"),
    }
