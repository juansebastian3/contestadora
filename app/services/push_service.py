"""Servicio de Push Notifications via Expo Push API.

Usa la API de Expo para enviar notificaciones a dispositivos iOS/Android
sin necesidad de configurar Firebase o APNS directamente.

Documentacion: https://docs.expo.dev/push-notifications/sending-notifications/
"""
import logging
import requests

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def enviar_push_notification(
    expo_push_token: str,
    titulo: str,
    mensaje: str,
    data: dict = None,
    sonido: str = "default",
    badge: int = None,
) -> bool:
    """Envia una push notification a un dispositivo via Expo Push API.

    Args:
        expo_push_token: Token del dispositivo (ExponentPushToken[xxx])
        titulo: Titulo de la notificacion
        mensaje: Cuerpo del mensaje
        data: Datos adicionales para la app al tocar la notificacion
        sonido: Sonido a reproducir ("default" o null)
        badge: Numero a mostrar en el icono de la app (iOS)

    Returns:
        True si se envio correctamente, False si fallo
    """
    if not expo_push_token or not expo_push_token.startswith("ExponentPushToken"):
        logger.warning(f"Push token invalido: {expo_push_token}")
        return False

    payload = {
        "to": expo_push_token,
        "title": titulo,
        "body": mensaje,
        "sound": sonido,
        "channelId": "llamadas",  # Android notification channel
    }

    if data:
        payload["data"] = data
    if badge is not None:
        payload["badge"] = badge

    try:
        response = requests.post(
            EXPO_PUSH_URL,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("data", {}).get("status") == "ok":
                logger.info(f"Push enviada a {expo_push_token[:30]}...")
                return True
            else:
                logger.warning(f"Push error: {result}")
                return False
        else:
            logger.error(f"Expo Push API error: {response.status_code} {response.text[:200]}")
            return False

    except Exception as e:
        logger.error(f"Error enviando push: {e}")
        return False


def notificar_llamada_entrante(usuario, numero_origen: str) -> bool:
    """Notifica al usuario que su asistente esta atendiendo una llamada."""
    if not usuario or not usuario.expo_push_token:
        return False

    if not usuario.notif_push:
        return False

    return enviar_push_notification(
        expo_push_token=usuario.expo_push_token,
        titulo="Llamada entrante",
        mensaje=f"Tu asistente esta atendiendo una llamada de {numero_origen}",
        data={"tipo": "llamada_entrante", "numero": numero_origen},
    )


def notificar_llamada_finalizada(usuario, analisis: dict, numero_origen: str) -> bool:
    """Notifica al usuario que una llamada fue procesada con su resumen."""
    if not usuario or not usuario.expo_push_token:
        return False

    if not usuario.notif_push:
        return False

    # Si solo quiere importantes, filtrar
    if usuario.notif_solo_importantes:
        prioridad = analisis.get("prioridad", "Baja")
        if prioridad not in ("Alta", "Media"):
            return False

    resumen = analisis.get("resumen", "Llamada procesada")
    categoria = analisis.get("categoria", "")
    nombre = analisis.get("nombre_contacto", numero_origen)

    titulo = f"Recado de {nombre}"
    if categoria:
        titulo = f"{categoria}: {nombre}"

    return enviar_push_notification(
        expo_push_token=usuario.expo_push_token,
        titulo=titulo,
        mensaje=resumen[:150],
        data={
            "tipo": "llamada_finalizada",
            "numero": numero_origen,
            "categoria": categoria,
            "prioridad": analisis.get("prioridad", "Baja"),
        },
        badge=1,
    )
