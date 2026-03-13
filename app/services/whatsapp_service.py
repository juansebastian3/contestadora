"""Servicio de notificaciones WhatsApp vía Twilio."""
import logging
from twilio.rest import Client

from app.core.config import settings

logger = logging.getLogger(__name__)

twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def enviar_resumen_llamada(analisis: dict, numero_origen: str = "Desconocido") -> str | None:
    """Envía el resumen estructurado de la llamada por WhatsApp.

    Returns:
        El SID del mensaje si fue exitoso, None si falló.
    """
    try:
        if not settings.TU_CELULAR or not settings.TWILIO_WHATSAPP_NUMBER:
            logger.error("Faltan números de WhatsApp en configuración")
            return None

        # Emojis según categoría
        emoji_cat = {
            "Personal": "👨‍👩‍👧",
            "Trabajo": "💼",
            "Trámite": "📋",
            "Marketing": "📢",
            "Desconocido": "❓"
        }

        # Emojis según prioridad
        emoji_pri = {
            "Alta": "🔴",
            "Media": "🟡",
            "Baja": "🟢"
        }

        categoria = analisis.get("categoria", "Desconocido")
        prioridad = analisis.get("prioridad", "Media")
        resumen = analisis.get("resumen", "Sin resumen disponible")
        nombre = analisis.get("nombre_contacto", None)

        cuerpo = (
            f"🐙 *Dora reportando*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📱 *De:* {nombre or numero_origen}\n"
            f"{emoji_cat.get(categoria, '❓')} *Categoria:* {categoria}\n"
            f"{emoji_pri.get(prioridad, '🟡')} *Prioridad:* {prioridad}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📝 *Resumen:*\n{resumen}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"_Tu ContestaDora_ 🐙"
        )

        message = twilio_client.messages.create(
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
            body=cuerpo,
            to=f"whatsapp:{settings.TU_CELULAR}"
        )
        logger.info(f"WhatsApp enviado: {message.sid}")
        return message.sid

    except Exception as e:
        logger.error(f"Error enviando WhatsApp: {e}")
        return None


def enviar_alerta_llamada_entrante(numero_origen: str) -> str | None:
    """Envía alerta inmediata de llamada entrante."""
    try:
        if not settings.TU_CELULAR or not settings.TWILIO_WHATSAPP_NUMBER:
            return None

        cuerpo = (
            f"📲 *Llamada entrante*\n"
            f"De: {numero_origen}\n"
            f"_Dora esta atendiendo..._  🐙"
        )

        message = twilio_client.messages.create(
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
            body=cuerpo,
            to=f"whatsapp:{settings.TU_CELULAR}"
        )
        return message.sid
    except Exception as e:
        logger.error(f"Error enviando alerta: {e}")
        return None
