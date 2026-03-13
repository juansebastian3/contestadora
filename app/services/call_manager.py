"""Gestor de llamadas activas - maneja historial de conversación en memoria."""
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class ConversacionActiva:
    """Representa una conversación telefónica en curso."""

    def __init__(self, call_sid: str, numero_origen: str = "Desconocido"):
        self.call_sid = call_sid
        self.numero_origen = numero_origen
        self.inicio = datetime.now(timezone.utc)
        self.historial: list[dict] = []  # Formato OpenAI messages
        self.transcripcion_completa: str = ""

    def agregar_mensaje_usuario(self, texto: str):
        self.historial.append({"role": "user", "content": texto})
        self.transcripcion_completa += f"\n[Llamante]: {texto}"

    def agregar_mensaje_asistente(self, texto: str):
        self.historial.append({"role": "assistant", "content": texto})
        self.transcripcion_completa += f"\n[Dora]: {texto}"

    def obtener_duracion(self) -> float:
        return (datetime.now(timezone.utc) - self.inicio).total_seconds()


class CallManager:
    """Singleton que gestiona todas las llamadas activas."""

    def __init__(self):
        self._llamadas_activas: dict[str, ConversacionActiva] = {}

    def iniciar_llamada(self, call_sid: str, numero_origen: str = "Desconocido") -> ConversacionActiva:
        conv = ConversacionActiva(call_sid, numero_origen)
        self._llamadas_activas[call_sid] = conv
        logger.info(f"Llamada iniciada: {call_sid} desde {numero_origen}")
        return conv

    def obtener_llamada(self, call_sid: str) -> Optional[ConversacionActiva]:
        return self._llamadas_activas.get(call_sid)

    def finalizar_llamada(self, call_sid: str) -> Optional[ConversacionActiva]:
        conv = self._llamadas_activas.pop(call_sid, None)
        if conv:
            logger.info(f"Llamada finalizada: {call_sid} (duración: {conv.obtener_duracion():.0f}s)")
        return conv

    def llamadas_activas_count(self) -> int:
        return len(self._llamadas_activas)


# Singleton global
call_manager = CallManager()
