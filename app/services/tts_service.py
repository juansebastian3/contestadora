"""Servicio de Text-to-Speech - Polly (gratis) y ElevenLabs (premium).

Este servicio genera audio para las respuestas del asistente durante la llamada.

FLUJO CON POLLY (gratuito):
    Twilio maneja el TTS directamente con <Say voice="Polly.Mia">.
    No necesitamos generar audio nosotros, solo retornar TwiML.

FLUJO CON ELEVENLABS (premium):
    1. Generamos el audio con la API de ElevenLabs
    2. Lo guardamos como archivo temporal
    3. Lo servimos desde una URL pública
    4. Usamos <Play> en TwiML para que Twilio lo reproduzca

    Formato requerido por Twilio: mulaw 8000Hz mono (para <Play>)
    o bien mp3/wav si usamos una URL directa.
"""
import os
import logging
import hashlib
import time
import httpx
from pathlib import Path
from fastapi import Request
from twilio.twiml.voice_response import VoiceResponse

from app.core.config import settings
from app.models.database import TipoVoz

logger = logging.getLogger(__name__)

# Directorio para cache de audio generado
AUDIO_CACHE_DIR = Path("./audio_cache")
AUDIO_CACHE_DIR.mkdir(exist_ok=True)


def generar_twiml_con_voz(
    texto: str,
    voz_tipo: str = TipoVoz.POLLY.value,
    polly_voice_id: str = "Polly.Mia",
    elevenlabs_voice_id: str = None,
    base_url: str = "",
) -> VoiceResponse:
    """Genera TwiML con la voz correcta según el plan del usuario.

    Args:
        texto: El texto que el asistente debe decir
        voz_tipo: "polly" o "elevenlabs"
        polly_voice_id: ID de voz Polly (ej: "Polly.Mia")
        elevenlabs_voice_id: ID de voz ElevenLabs
        base_url: URL base del servidor para servir audio

    Returns:
        VoiceResponse con <Say> (Polly) o <Play> (ElevenLabs)
    """
    respuesta = VoiceResponse()

    if voz_tipo == TipoVoz.ELEVENLABS.value and elevenlabs_voice_id:
        # ═══ ELEVENLABS (Premium) ═══
        audio_url = _generar_audio_elevenlabs(texto, elevenlabs_voice_id, base_url)
        if audio_url:
            respuesta.play(audio_url)
            return respuesta
        else:
            # Fallback a Polly si ElevenLabs falla
            logger.warning("ElevenLabs falló, usando Polly como fallback")

    # ═══ POLLY (Gratuito / Fallback) ═══
    respuesta.say(texto, language="es-CL", voice=polly_voice_id)
    return respuesta


def _generar_audio_elevenlabs(texto: str, voice_id: str, base_url: str) -> str | None:
    """Genera audio con ElevenLabs y retorna la URL para Twilio.

    Returns:
        URL del audio generado, o None si falla.
    """
    if not settings.ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY no configurada")
        return None

    try:
        # Cache: si ya generamos este texto+voz, reusar
        cache_key = hashlib.md5(f"{voice_id}:{texto}".encode()).hexdigest()
        cache_file = AUDIO_CACHE_DIR / f"{cache_key}.mp3"

        if not cache_file.exists():
            # Llamar a ElevenLabs API
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            }
            payload = {
                "text": texto,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.3,
                    "use_speaker_boost": True,
                },
            }

            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                logger.error(f"ElevenLabs error {response.status_code}: {response.text[:200]}")
                return None

            # Guardar audio
            cache_file.write_bytes(response.content)
            logger.info(f"Audio ElevenLabs generado: {cache_file.name} ({len(response.content)} bytes)")

        # Retornar URL pública para que Twilio descargue el audio
        audio_url = f"{base_url}/audio/{cache_key}.mp3"
        return audio_url

    except Exception as e:
        logger.error(f"Error generando audio ElevenLabs: {e}")
        return None


def limpiar_cache_audio(max_edad_horas: int = 24):
    """Elimina archivos de audio cache más viejos que max_edad_horas."""
    ahora = time.time()
    eliminados = 0
    for archivo in AUDIO_CACHE_DIR.glob("*.mp3"):
        edad = ahora - archivo.stat().st_mtime
        if edad > max_edad_horas * 3600:
            archivo.unlink()
            eliminados += 1
    if eliminados:
        logger.info(f"Cache limpiado: {eliminados} archivos de audio eliminados")
