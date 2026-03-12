"""Servicio de integración con calendarios (Google Calendar + Outlook).

FLUJO PARA EL USUARIO PRO/PREMIUM:
─────────────────────────────────────────────────────────────────
  1. Conecta su cuenta de Google y/o Outlook desde la app
  2. Elige modo: "solo_reuniones" o "siempre_agenda"
  3. Cuando recibe una llamada:
     - El sistema verifica si tiene un evento activo en su calendario
     - Si sí → activa la contestadora automáticamente
     - Si no → sigue el modo de filtrado normal (desconocidos, etc.)

MODOS DE CALENDARIO:
  SOLO_REUNIONES: Solo activa durante reuniones/meetings (no todo el día)
  SIEMPRE_AGENDA: Activa si hay CUALQUIER evento, incluso "todo el día"
  MANUAL: No auto-activar, el usuario controla manualmente
─────────────────────────────────────────────────────────────────
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# GOOGLE CALENDAR
# ═══════════════════════════════════════════════════════════

def verificar_evento_google(token_data: dict, modo_calendario: str = "solo_reuniones") -> dict | None:
    """Verifica si el usuario tiene un evento activo en Google Calendar.

    Args:
        token_data: {access_token, refresh_token, expiry, client_id, client_secret}
        modo_calendario: "solo_reuniones" o "siempre_agenda"

    Returns:
        dict con info del evento si hay uno activo, None si no.
        {titulo, inicio, fin, tipo} donde tipo puede ser "reunion" o "evento"
    """
    try:
        import requests

        access_token = token_data.get("access_token")
        if not access_token:
            logger.warning("Google Calendar: no hay access_token")
            return None

        # Verificar si el token está vencido y refrescar si es necesario
        access_token = _refrescar_google_token_si_necesario(token_data)
        if not access_token:
            return None

        # Consultar eventos actuales
        ahora = datetime.now(timezone.utc)
        ahora_str = ahora.isoformat()
        en_1_min = (ahora + timedelta(minutes=1)).isoformat()

        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        params = {
            "timeMin": ahora_str,
            "timeMax": en_1_min,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 5,
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        resp = requests.get(url, params=params, headers=headers, timeout=5)

        if resp.status_code == 401:
            # Token vencido, intentar refresh
            logger.info("Google Calendar: token vencido, refrescando...")
            access_token = _refrescar_google_token(token_data)
            if access_token:
                headers = {"Authorization": f"Bearer {access_token}"}
                resp = requests.get(url, params=params, headers=headers, timeout=5)
            else:
                return None

        if resp.status_code != 200:
            logger.error(f"Google Calendar API error: {resp.status_code}")
            return None

        eventos = resp.json().get("items", [])

        for evento in eventos:
            # Ignorar eventos cancelados
            if evento.get("status") == "cancelled":
                continue

            # Determinar tipo de evento
            inicio = evento.get("start", {})
            es_todo_el_dia = "date" in inicio and "dateTime" not in inicio

            if modo_calendario == "solo_reuniones" and es_todo_el_dia:
                continue  # Ignorar eventos de todo el día en modo solo_reuniones

            # Verificar que el evento está activo AHORA
            if es_todo_el_dia:
                tipo = "evento"
            else:
                tipo = "reunion"

            titulo = evento.get("summary", "Evento sin título")

            return {
                "titulo": titulo,
                "inicio": inicio.get("dateTime") or inicio.get("date"),
                "fin": evento.get("end", {}).get("dateTime") or evento.get("end", {}).get("date"),
                "tipo": tipo,
                "origen": "google",
            }

        return None

    except ImportError:
        logger.error("Módulo 'requests' no disponible para Google Calendar")
        return None
    except Exception as e:
        logger.error(f"Error verificando Google Calendar: {e}")
        return None


def _refrescar_google_token_si_necesario(token_data: dict) -> str | None:
    """Devuelve el access_token, refrescando si expiró."""
    expiry = token_data.get("expiry")
    access_token = token_data.get("access_token")

    if not expiry:
        return access_token

    try:
        # expiry puede ser ISO string o timestamp
        if isinstance(expiry, str):
            expiry_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        else:
            expiry_dt = datetime.fromtimestamp(expiry, tz=timezone.utc)

        if datetime.now(timezone.utc) >= expiry_dt - timedelta(minutes=5):
            return _refrescar_google_token(token_data)

        return access_token
    except Exception:
        return access_token


def _refrescar_google_token(token_data: dict) -> str | None:
    """Refresca el access_token de Google usando el refresh_token."""
    try:
        import requests
        import os

        refresh_token = token_data.get("refresh_token")
        client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")

        if not refresh_token or not client_id:
            logger.warning("Google Calendar: faltan credenciales para refresh")
            return None

        resp = requests.post("https://oauth2.googleapis.com/token", data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            # Nota: el token actualizado se debe persistir en la DB
            # Eso se hace en el caller (filtrado_service)
            return data.get("access_token")
        else:
            logger.error(f"Error refrescando Google token: {resp.status_code}")
            return None

    except Exception as e:
        logger.error(f"Error en refresh Google: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# MICROSOFT OUTLOOK / OFFICE 365
# ═══════════════════════════════════════════════════════════

def verificar_evento_outlook(token_data: dict, modo_calendario: str = "solo_reuniones") -> dict | None:
    """Verifica si el usuario tiene un evento activo en Outlook Calendar.

    Args:
        token_data: {access_token, refresh_token, expiry}
        modo_calendario: "solo_reuniones" o "siempre_agenda"

    Returns:
        dict con info del evento activo o None.
    """
    try:
        import requests

        access_token = token_data.get("access_token")
        if not access_token:
            return None

        access_token = _refrescar_outlook_token_si_necesario(token_data)
        if not access_token:
            return None

        ahora = datetime.now(timezone.utc)
        ahora_str = ahora.strftime("%Y-%m-%dT%H:%M:%S.0000000")
        en_1_min = (ahora + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S.0000000")

        url = "https://graph.microsoft.com/v1.0/me/calendarview"
        params = {
            "startdatetime": ahora_str,
            "enddatetime": en_1_min,
            "$top": 5,
            "$select": "subject,start,end,isAllDay",
            "$orderby": "start/dateTime",
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        resp = requests.get(url, params=params, headers=headers, timeout=5)

        if resp.status_code == 401:
            access_token = _refrescar_outlook_token(token_data)
            if access_token:
                headers = {"Authorization": f"Bearer {access_token}"}
                resp = requests.get(url, params=params, headers=headers, timeout=5)
            else:
                return None

        if resp.status_code != 200:
            logger.error(f"Outlook Calendar API error: {resp.status_code}")
            return None

        eventos = resp.json().get("value", [])

        for evento in eventos:
            es_todo_el_dia = evento.get("isAllDay", False)

            if modo_calendario == "solo_reuniones" and es_todo_el_dia:
                continue

            titulo = evento.get("subject", "Evento sin título")
            inicio = evento.get("start", {}).get("dateTime")
            fin = evento.get("end", {}).get("dateTime")

            return {
                "titulo": titulo,
                "inicio": inicio,
                "fin": fin,
                "tipo": "evento" if es_todo_el_dia else "reunion",
                "origen": "outlook",
            }

        return None

    except Exception as e:
        logger.error(f"Error verificando Outlook Calendar: {e}")
        return None


def _refrescar_outlook_token_si_necesario(token_data: dict) -> str | None:
    """Devuelve access_token, refrescando si expiró."""
    expiry = token_data.get("expiry")
    access_token = token_data.get("access_token")

    if not expiry:
        return access_token

    try:
        if isinstance(expiry, str):
            expiry_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        else:
            expiry_dt = datetime.fromtimestamp(expiry, tz=timezone.utc)

        if datetime.now(timezone.utc) >= expiry_dt - timedelta(minutes=5):
            return _refrescar_outlook_token(token_data)

        return access_token
    except Exception:
        return access_token


def _refrescar_outlook_token(token_data: dict) -> str | None:
    """Refresca el access_token de Outlook."""
    try:
        import requests
        import os

        refresh_token = token_data.get("refresh_token")
        client_id = os.getenv("OUTLOOK_CLIENT_ID", "")
        client_secret = os.getenv("OUTLOOK_CLIENT_SECRET", "")

        if not refresh_token or not client_id:
            return None

        resp = requests.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/Calendars.Read offline_access",
        }, timeout=10)

        if resp.status_code == 200:
            return resp.json().get("access_token")
        else:
            logger.error(f"Error refrescando Outlook token: {resp.status_code}")
            return None

    except Exception as e:
        logger.error(f"Error en refresh Outlook: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL: ¿ESTÁ EN REUNIÓN?
# ═══════════════════════════════════════════════════════════

def usuario_en_reunion(usuario) -> dict | None:
    """Verifica si el usuario tiene una reunión activa en CUALQUIERA de sus calendarios.

    Revisa Google Calendar y Outlook Calendar. Devuelve el primer evento encontrado.

    Args:
        usuario: Objeto Usuario de la DB

    Returns:
        dict {titulo, inicio, fin, tipo, origen} si hay evento activo, None si no.
    """
    if not usuario.calendario_auto_activar:
        return None

    modo = usuario.calendario_modo or "solo_reuniones"

    # Verificar Google Calendar
    if usuario.google_calendar_token:
        evento = verificar_evento_google(usuario.google_calendar_token, modo)
        if evento:
            logger.info(f"📅 {usuario.nombre} en {evento['tipo']} (Google): {evento['titulo']}")
            return evento

    # Verificar Outlook Calendar
    if usuario.outlook_calendar_token:
        evento = verificar_evento_outlook(usuario.outlook_calendar_token, modo)
        if evento:
            logger.info(f"📅 {usuario.nombre} en {evento['tipo']} (Outlook): {evento['titulo']}")
            return evento

    return None
