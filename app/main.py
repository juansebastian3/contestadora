"""FiltroLlamadas - Asistente IA de filtrado de llamadas.

Aplicación principal FastAPI que integra:
- Twilio Voice Webhooks con filtrado inteligente
- Selección de voz (Polly gratuito / ElevenLabs premium)
- Modos de filtrado (desconocidos / luna / desactivado)
- API REST para app móvil
- Análisis y resumen con LLM al finalizar llamada
- Notificaciones WhatsApp estructuradas
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.core.auth import router as auth_router
from app.api.webhooks import router as webhooks_router
from app.api.mobile_api import router as mobile_router
from app.api.websocket_stream import router as ws_router
from app.api.suscripcion_web import router as suscripcion_router
from app.models.database import SessionLocal, seed_voces_y_planes

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="FiltroLlamadas API",
    description="Asistente IA para filtrado inteligente de llamadas telefónicas",
    version="1.0.0",
)

# CORS para la app móvil
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: restringir a tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos de audio generados por ElevenLabs
audio_dir = Path("./audio_cache")
audio_dir.mkdir(exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

# Servir archivos de audio subidos por usuarios (saludos de contestadora)
uploads_dir = Path("./audio_uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/audio_uploads", StaticFiles(directory=str(uploads_dir)), name="audio_uploads")

# Registrar routers
app.include_router(auth_router)        # /auth/registro, /auth/login, /auth/refresh
app.include_router(webhooks_router)    # /webhooks/voice/* (sin auth - Twilio)
app.include_router(mobile_router)      # /api/v1/* (con auth JWT)
app.include_router(ws_router)          # /ws/* (WebSocket)
app.include_router(suscripcion_router) # /suscripcion/* + /webhooks/mercadopago

# --- NUEVA RUTA DE HEALTHCHECK PARA RAILWAY ---
@app.get("/api/v1/health")
async def health_check():
    """Ruta para que Railway verifique que la app está viva."""
    return {"status": "ok", "message": "FiltroLlamadas is healthy"}
# ----------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Inicializar datos al arrancar el servidor."""
    logger.info("🚀 Iniciando FiltroLlamadas...")

    # Asegurar que todas las tablas/columnas existan (crea las que falten)
    from app.models.database import Base, engine
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tablas de base de datos verificadas")

    db = SessionLocal()
    try:
        # Migración manual: agregar columnas nuevas si no existen (PostgreSQL)
        _aplicar_migraciones(db)

        seed_voces_y_planes(db)
        logger.info("✅ Voces y planes inicializados")
    except Exception as e:
        logger.error(f"Error en seed: {e}")
    finally:
        db.close()


def _aplicar_migraciones(db):
    """Agrega columnas nuevas a tablas existentes si no existen.

    SQLAlchemy create_all() solo crea tablas nuevas, no agrega columnas
    a tablas existentes. Esta función lo hace manualmente.
    """
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(db.bind)
        columnas_usuario = [col["name"] for col in inspector.get_columns("usuarios")]

        nuevas_columnas = {
            "google_calendar_token": "TEXT",
            "outlook_calendar_token": "TEXT",
            "calendario_auto_activar": "BOOLEAN DEFAULT FALSE",
            "calendario_modo": "VARCHAR(30) DEFAULT 'solo_reuniones'",
            "mercadopago_customer_id": "VARCHAR(100)",
        }

        for col_name, col_type in nuevas_columnas.items():
            if col_name not in columnas_usuario:
                db.execute(text(f"ALTER TABLE usuarios ADD COLUMN {col_name} {col_type}"))
                logger.info(f"  + Columna '{col_name}' agregada a usuarios")

        db.commit()
        logger.info("✅ Migraciones aplicadas")
    except Exception as e:
        logger.warning(f"Migraciones: {e} (puede ser normal en primera ejecución)")
        db.rollback()


@app.get("/")
async def root():
    return {
        "app": "FiltroLlamadas",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/v1/health",
            "auth": "/auth/registro | /auth/login | /auth/refresh",
            "webhooks": "/webhooks/voice/incoming",
            "websocket": "/ws/media-stream",
            "api": "/api/v1/dashboard (requiere Bearer token)",
            "docs": "/docs (Swagger UI con login)",
            "voces": "/api/v1/voces (público)",
            "planes": "/api/v1/planes (público)",
            "suscripcion": "/suscripcion/planes (página web pública)",
        },
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Iniciando FiltroLlamadas en {settings.APP_HOST}:{settings.APP_PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )