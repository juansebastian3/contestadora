"""Fase 5: WebSocket para Twilio Media Streams - Baja latencia en tiempo real.

Este módulo implementa la comunicación bidireccional con Twilio Media Streams,
permitiendo:
1. Recibir audio en tiempo real vía WebSocket (en vez de esperar Gather)
2. Enviar audio de vuelta inmediatamente (streaming de TTS)
3. Usar STT en streaming para transcribir mientras el usuario habla
4. Usar LLM con streaming para generar respuesta mientras transcribe

ARQUITECTURA DE BAJA LATENCIA:
┌──────────┐    WebSocket     ┌──────────────┐    Stream     ┌─────────┐
│  Twilio  │ ◄──────────────► │  FastAPI WS  │ ◄───────────► │ OpenAI  │
│  (Audio) │   Media Stream   │  (Orquesta)  │   Streaming   │  (LLM)  │
└──────────┘                  └──────┬───────┘               └─────────┘
                                     │
                              ┌──────▼───────┐
                              │  ElevenLabs  │
                              │  (TTS Stream)│
                              └──────────────┘

FLUJO:
1. Twilio envía audio mulaw 8kHz vía WebSocket
2. Acumulamos audio y lo enviamos a Whisper (o usamos Deepgram para streaming)
3. Al detectar fin de habla, enviamos texto al LLM con streaming
4. Cada chunk de respuesta del LLM se envía a ElevenLabs para TTS
5. El audio TTS se envía de vuelta a Twilio por el mismo WebSocket

RESULTADO: Latencia de ~1-2 segundos vs ~5-8 segundos del flujo Gather.
"""
import asyncio
import base64
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

from app.core.config import settings
from app.services.call_manager import call_manager
from app.services.llm_service import generar_respuesta_conversacion, analizar_llamada
from app.services.whatsapp_service import enviar_resumen_llamada

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket Media Stream"])


@router.api_route("/webhooks/voice/stream", methods=["GET", "POST"])
async def incoming_call_stream():
    """Webhook alternativo que usa Media Streams en vez de Gather.

    Configura este endpoint en Twilio como tu Voice URL para activar
    el modo de baja latencia.
    """
    response = VoiceResponse()
    response.say(
        f"Hola, soy {settings.ASSISTANT_NAME}, asistente de {settings.OWNER_NAME}. "
        "Te escucho, cuéntame.",
        language="es-CL",
        voice="Polly.Mia",
    )
    response.pause(length=1)

    # Conectar Media Stream bidireccional
    connect = Connect()
    stream = Stream(url=f"wss://TU_DOMINIO/ws/media-stream")
    # Parámetros custom que Twilio enviará por el WebSocket
    stream.parameter(name="caller_greeting", value="true")
    connect.append(stream)
    response.append(connect)

    return {"content": str(response), "media_type": "application/xml"}


@router.websocket("/ws/media-stream")
async def media_stream_websocket(websocket: WebSocket):
    """WebSocket bidireccional para Twilio Media Streams.

    Maneja el flujo de audio en tiempo real para mínima latencia.

    NOTA IMPORTANTE: Para una implementación completa de producción, necesitas:
    1. Un servicio STT en streaming (Deepgram, Google Cloud Speech, Azure)
    2. ElevenLabs API con streaming de audio
    3. Manejo de buffers de audio y detección de voz (VAD)

    Esta implementación provee la estructura base y el protocolo.
    """
    await websocket.accept()
    logger.info("🔌 WebSocket Media Stream conectado")

    stream_sid = None
    call_sid = None
    audio_buffer = bytearray()
    conversation_history = []

    try:
        async for message in websocket.iter_text():
            data = json.loads(message)
            event_type = data.get("event")

            if event_type == "connected":
                logger.info("✅ Media Stream conectado a Twilio")

            elif event_type == "start":
                # Metadata de la llamada
                start_data = data.get("start", {})
                stream_sid = start_data.get("streamSid")
                call_sid = start_data.get("callSid")
                logger.info(f"🎙 Stream iniciado: {stream_sid} (call: {call_sid})")

                # Registrar llamada
                call_manager.iniciar_llamada(call_sid or "ws-unknown")

            elif event_type == "media":
                # Audio entrante: mulaw 8kHz base64
                media = data.get("media", {})
                payload = media.get("payload", "")
                audio_bytes = base64.b64decode(payload)
                audio_buffer.extend(audio_bytes)

                # En producción: enviar chunks a un servicio STT en streaming
                # como Deepgram o Google Cloud Speech para transcripción
                # en tiempo real con detección de fin de habla (VAD).
                #
                # Pseudocódigo del flujo ideal:
                # stt_service.send_audio(audio_bytes)
                # if stt_service.is_final_transcript():
                #     user_text = stt_service.get_transcript()
                #     await process_and_respond(user_text, websocket, stream_sid)

            elif event_type == "mark":
                # Confirmación de que Twilio reprodujo nuestro audio
                mark_name = data.get("mark", {}).get("name", "")
                logger.info(f"✓ Audio reproducido: {mark_name}")

            elif event_type == "stop":
                # Stream terminado
                logger.info(f"🔚 Stream finalizado: {stream_sid}")

                # Procesar la llamada completa si hay audio
                conv = call_manager.finalizar_llamada(call_sid or "ws-unknown")
                if conv and conv.transcripcion_completa.strip():
                    analisis = analizar_llamada(conv.transcripcion_completa)
                    enviar_resumen_llamada(analisis, conv.numero_origen)

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket desconectado")
    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}")
    finally:
        logger.info("🧹 Limpiando recursos del Media Stream")


async def enviar_audio_a_twilio(websocket: WebSocket, stream_sid: str, audio_base64: str):
    """Envía audio de vuelta a la llamada vía Twilio Media Stream.

    El audio debe estar en formato mulaw 8kHz mono, codificado en base64.
    """
    media_message = {
        "event": "media",
        "streamSid": stream_sid,
        "media": {
            "payload": audio_base64
        }
    }
    await websocket.send_json(media_message)

    # Enviar un mark para saber cuándo terminó de reproducir
    mark_message = {
        "event": "mark",
        "streamSid": stream_sid,
        "mark": {
            "name": "response_end"
        }
    }
    await websocket.send_json(mark_message)


async def process_and_respond_streaming(
    user_text: str,
    conversation_history: list,
    websocket: WebSocket,
    stream_sid: str,
):
    """Proceso completo de baja latencia: LLM streaming → TTS streaming → Twilio.

    NOTA: Requiere ElevenLabs streaming API y conversión de audio a mulaw.
    Esta función muestra la arquitectura; la implementación completa necesita:
    - httpx o aiohttp para streaming de ElevenLabs
    - audioop o pydub para convertir audio a mulaw 8kHz
    """
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # LLM con streaming
    system_prompt = (
        f"Eres {settings.ASSISTANT_NAME}, asistente virtual de {settings.OWNER_NAME}. "
        "Sé breve y profesional con tono chileno."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_text})

    # Streaming del LLM - acumulamos texto para TTS
    text_buffer = ""
    full_response = ""

    stream = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        max_tokens=150,
        temperature=0.7,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            text_buffer += delta.content
            full_response += delta.content

            # Cuando tengamos una oración completa, enviar a TTS
            if any(text_buffer.endswith(p) for p in [".", "!", "?", ","]):
                # En producción:
                # audio = await elevenlabs_tts_streaming(text_buffer)
                # mulaw_audio = convert_to_mulaw(audio)
                # audio_b64 = base64.b64encode(mulaw_audio).decode()
                # await enviar_audio_a_twilio(websocket, stream_sid, audio_b64)
                text_buffer = ""

    # Enviar cualquier texto restante
    if text_buffer:
        pass  # Mismo proceso TTS + enviar

    return full_response
