"""Servicio de auto-provisioning de números Twilio.

Cada usuario recibe un número Twilio dedicado para recibir llamadas desviadas.
El usuario configura desvío en su celular → llamadas van a su número Twilio →
Twilio llama al webhook → backend identifica al usuario y aplica su configuración.

Flujo:
1. Usuario se registra → se le asigna un número Twilio automáticamente
2. El número se configura con el webhook de incoming calls
3. Cuando el usuario cancela → se libera el número
"""
import logging
from typing import Optional

from twilio.rest import Client

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_twilio_client() -> Client:
    """Crea un cliente Twilio autenticado."""
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def buscar_numero_disponible(
    codigo_pais: str = "US",
    tipo: str = "local",
) -> Optional[dict]:
    """Busca un número de teléfono disponible para comprar en Twilio.

    Args:
        codigo_pais: Código ISO del país (US, CL, MX, etc.)
        tipo: "local", "toll_free", o "mobile"

    Returns:
        dict con phone_number y friendly_name, o None si no hay disponibles
    """
    try:
        client = _get_twilio_client()

        if tipo == "local":
            numeros = client.available_phone_numbers(codigo_pais).local.list(
                voice_enabled=True,
                sms_enabled=False,
                limit=1,
            )
        elif tipo == "toll_free":
            numeros = client.available_phone_numbers(codigo_pais).toll_free.list(
                voice_enabled=True,
                limit=1,
            )
        else:
            numeros = client.available_phone_numbers(codigo_pais).mobile.list(
                voice_enabled=True,
                limit=1,
            )

        if numeros:
            n = numeros[0]
            return {
                "phone_number": n.phone_number,
                "friendly_name": n.friendly_name,
                "pais": codigo_pais,
            }

        logger.warning(f"No hay números disponibles en {codigo_pais} tipo {tipo}")
        return None

    except Exception as e:
        logger.error(f"Error buscando número Twilio: {e}")
        return None


def comprar_y_configurar_numero(
    codigo_pais: str = "US",
    webhook_base_url: str = "",
) -> Optional[dict]:
    """Compra un número Twilio y lo configura con los webhooks.

    Args:
        codigo_pais: País del número
        webhook_base_url: URL base del servidor (ej: https://contestadora-production.up.railway.app)

    Returns:
        dict con phone_number, sid, friendly_name o None si falla
    """
    if not webhook_base_url:
        webhook_base_url = settings.BASE_URL

    try:
        client = _get_twilio_client()

        # Buscar número disponible
        disponible = buscar_numero_disponible(codigo_pais)
        if not disponible:
            return None

        # Comprar el número
        numero = client.incoming_phone_numbers.create(
            phone_number=disponible["phone_number"],
            voice_url=f"{webhook_base_url}/webhooks/voice/incoming",
            voice_method="POST",
            status_callback=f"{webhook_base_url}/webhooks/voice/status",
            status_callback_method="POST",
            friendly_name="ContestaDora Auto",
        )

        logger.info(f"Número Twilio comprado: {numero.phone_number} (SID: {numero.sid})")

        return {
            "phone_number": numero.phone_number,
            "sid": numero.sid,
            "friendly_name": numero.friendly_name,
        }

    except Exception as e:
        logger.error(f"Error comprando número Twilio: {e}")
        return None


def asignar_numero_a_usuario(db_session, usuario, codigo_pais: str = "US") -> Optional[dict]:
    """Asigna un número Twilio a un usuario. Compra uno si no tiene.

    Args:
        db_session: Sesión de SQLAlchemy
        usuario: Modelo Usuario
        codigo_pais: País del número

    Returns:
        dict con info del número o None si falla
    """
    # Si ya tiene número, no hacer nada
    if usuario.telefono_twilio:
        return {
            "phone_number": usuario.telefono_twilio,
            "sid": usuario.twilio_phone_sid,
            "ya_asignado": True,
        }

    resultado = comprar_y_configurar_numero(codigo_pais)
    if not resultado:
        return None

    # Guardar en el usuario
    usuario.telefono_twilio = resultado["phone_number"]
    usuario.twilio_phone_sid = resultado["sid"]
    db_session.commit()

    logger.info(f"Número {resultado['phone_number']} asignado a usuario {usuario.uid}")
    return resultado


def liberar_numero(db_session, usuario) -> bool:
    """Libera (elimina) el número Twilio de un usuario.

    Usado cuando el usuario cancela su suscripción.
    """
    if not usuario.twilio_phone_sid:
        return True

    try:
        client = _get_twilio_client()
        client.incoming_phone_numbers(usuario.twilio_phone_sid).delete()

        logger.info(f"Número {usuario.telefono_twilio} liberado de usuario {usuario.uid}")

        usuario.telefono_twilio = None
        usuario.twilio_phone_sid = None
        db_session.commit()
        return True

    except Exception as e:
        logger.error(f"Error liberando número Twilio: {e}")
        return False


def actualizar_webhooks_numero(phone_sid: str, webhook_base_url: str = "") -> bool:
    """Actualiza los webhooks de un número Twilio existente.

    Útil cuando cambia la URL del servidor (ej: nuevo deploy con dominio diferente).
    """
    if not webhook_base_url:
        webhook_base_url = settings.BASE_URL

    try:
        client = _get_twilio_client()
        client.incoming_phone_numbers(phone_sid).update(
            voice_url=f"{webhook_base_url}/webhooks/voice/incoming",
            voice_method="POST",
            status_callback=f"{webhook_base_url}/webhooks/voice/status",
            status_callback_method="POST",
        )
        return True
    except Exception as e:
        logger.error(f"Error actualizando webhooks: {e}")
        return False
