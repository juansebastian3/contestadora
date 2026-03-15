"""Rate limiter ligero para FastAPI.

Implementa rate limiting en memoria con ventana deslizante.
No requiere Redis ni dependencias externas — ideal para apps
de tamaño pequeño/mediano.

Limites por defecto:
- Auth (login/registro): 10 req/min por IP (protege contra brute force)
- API general: 60 req/min por IP
- Webhooks (Twilio): 120 req/min por IP (mas generoso porque son automaticos)
"""
import os
import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitStore:
    """Almacena contadores de requests por IP con limpieza automatica."""

    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Verifica si una request esta permitida.

        Args:
            key: Identificador (generalmente IP + ruta)
            max_requests: Maximo de requests en la ventana
            window_seconds: Ventana de tiempo en segundos

        Returns:
            True si esta permitida, False si excede el limite
        """
        now = time.time()
        cutoff = now - window_seconds

        # Limpiar entries viejas de esta key
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        # Limpieza global periodica (cada 5 min)
        if now - self._last_cleanup > 300:
            self._cleanup_old_entries(cutoff)
            self._last_cleanup = now

        if len(self._requests[key]) >= max_requests:
            return False

        self._requests[key].append(now)
        return True

    def _cleanup_old_entries(self, cutoff: float):
        """Elimina IPs inactivas para evitar memory leak."""
        keys_to_delete = []
        for key, timestamps in self._requests.items():
            self._requests[key] = [t for t in timestamps if t > cutoff]
            if not self._requests[key]:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del self._requests[key]


# Instancia global
_store = RateLimitStore()

# Configuracion de limites por tipo de ruta
RATE_LIMITS = {
    "auth": {"max_requests": 10, "window_seconds": 60},      # 10/min
    "api": {"max_requests": 60, "window_seconds": 60},        # 60/min
    "webhooks": {"max_requests": 120, "window_seconds": 60},   # 120/min
    "public": {"max_requests": 30, "window_seconds": 60},      # 30/min
}


def _get_client_ip(request: Request) -> str:
    """Obtiene la IP real del cliente, soportando proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_rate_limit_category(path: str) -> str:
    """Determina la categoria de rate limit segun la ruta."""
    if path.startswith("/auth/"):
        return "auth"
    elif path.startswith("/webhooks/"):
        return "webhooks"
    elif path.startswith("/api/"):
        return "api"
    else:
        return "public"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting para FastAPI."""

    async def dispatch(self, request: Request, call_next):
        # No limitar en tests ni healthcheck
        if os.environ.get("TESTING") == "1":
            return await call_next(request)
        if request.url.path in ("/api/v1/health", "/api/status"):
            return await call_next(request)

        client_ip = _get_client_ip(request)
        category = _get_rate_limit_category(request.url.path)
        limits = RATE_LIMITS[category]

        key = f"{client_ip}:{category}"

        if not _store.is_allowed(key, limits["max_requests"], limits["window_seconds"]):
            logger.warning(
                f"Rate limit excedido: {client_ip} en {category} "
                f"({limits['max_requests']}/{limits['window_seconds']}s)"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Demasiadas solicitudes. Intenta de nuevo en un momento.",
                    "retry_after_seconds": limits["window_seconds"],
                },
                headers={
                    "Retry-After": str(limits["window_seconds"]),
                    "X-RateLimit-Limit": str(limits["max_requests"]),
                },
            )

        response = await call_next(request)

        # Agregar headers informativos
        response.headers["X-RateLimit-Limit"] = str(limits["max_requests"])
        response.headers["X-RateLimit-Category"] = category

        return response
