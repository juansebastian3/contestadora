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
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.core.auth import router as auth_router
from app.api.webhooks import router as webhooks_router
from app.api.mobile_api import router as mobile_router
from app.api.websocket_stream import router as ws_router
from app.api.suscripcion_web import router as suscripcion_router
from app.api.pagos import router as pagos_router
from app.api.growth_api import router as growth_router
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

# Rate limiting (debe ir antes de CORS para que aplique primero)
from app.core.rate_limiter import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

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
app.include_router(pagos_router)       # /api/v1/pagos/* + /webhooks/flow
app.include_router(growth_router)      # /api/v1/referido, descuento, precios, admin/*

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

        # Seed precios geográficos PPP
        from app.services.geo_pricing_service import seed_precios_geograficos
        seed_precios_geograficos(db)
        logger.info("✅ Precios geográficos PPP inicializados")

        # Crear código de descuento de bienvenida si no existe
        _seed_codigos_descuento(db)
    except Exception as e:
        logger.error(f"Error en seed: {e}")
    finally:
        db.close()


def _seed_codigos_descuento(db):
    """Crea códigos de descuento iniciales para campañas de retención."""
    from app.models.database import CodigoDescuento
    from datetime import timedelta

    codigos_iniciales = [
        {
            "codigo": "DORA50-WELCOME",
            "descripcion": "50% off primer mes - Drip campaign día 14",
            "tipo": "porcentaje",
            "valor": 50,
            "usos_maximos": 0,  # Ilimitado
        },
        {
            "codigo": "DORA-AMIGO",
            "descripcion": "1 mes gratis por referido",
            "tipo": "mes_gratis",
            "meses_gratis": 1,
            "usos_maximos": 0,
        },
        {
            "codigo": "DORA-LAUNCH",
            "descripcion": "30% off por lanzamiento",
            "tipo": "porcentaje",
            "valor": 30,
            "usos_maximos": 500,
        },
    ]

    for datos in codigos_iniciales:
        existente = db.query(CodigoDescuento).filter(
            CodigoDescuento.codigo == datos["codigo"]
        ).first()
        if not existente:
            db.add(CodigoDescuento(**datos))
            logger.info(f"  + Código descuento creado: {datos['codigo']}")

    db.commit()


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
            "telefono_twilio": "VARCHAR(20)",
            "twilio_phone_sid": "VARCHAR(50)",
            "expo_push_token": "VARCHAR(200)",
            "trial_expira": "DATETIME",
            "trial_usado": "BOOLEAN DEFAULT FALSE",
            "codigo_referido": "VARCHAR(20)",
            "referido_por_id": "INTEGER",
            "pais_codigo": "VARCHAR(5)",
            "ultima_llamada_recibida": "DATETIME",
            "twilio_numero_liberado": "BOOLEAN DEFAULT FALSE",
        }

        for col_name, col_type in nuevas_columnas.items():
            if col_name not in columnas_usuario:
                db.execute(text(f"ALTER TABLE usuarios ADD COLUMN {col_name} {col_type}"))
                logger.info(f"  + Columna '{col_name}' agregada a usuarios")

        # Migraciones para tabla suscripciones (pasarelas de pago)
        if "suscripciones" in inspector.get_table_names():
            columnas_suscripcion = [col["name"] for col in inspector.get_columns("suscripciones")]
            nuevas_col_suscripcion = {
                "tbk_buy_order": "VARCHAR(100)",
                "tbk_authorization_code": "VARCHAR(50)",
                "flow_order": "VARCHAR(100)",
                "flow_token": "VARCHAR(200)",
            }
            for col_name, col_type in nuevas_col_suscripcion.items():
                if col_name not in columnas_suscripcion:
                    db.execute(text(f"ALTER TABLE suscripciones ADD COLUMN {col_name} {col_type}"))
                    logger.info(f"  + Columna '{col_name}' agregada a suscripciones")

        db.commit()
        logger.info("✅ Migraciones aplicadas")
    except Exception as e:
        logger.warning(f"Migraciones: {e} (puede ser normal en primera ejecución)")
        db.rollback()


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Landing page pública de marketing."""
    from app.landing import render_landing_html
    return HTMLResponse(content=render_landing_html())


@app.get("/terminos", response_class=HTMLResponse)
async def terminos_page():
    """Terminos de servicio accesibles via web."""
    from app.legal import render_legal_html
    return HTMLResponse(content=render_legal_html("terminos"))


@app.get("/privacidad", response_class=HTMLResponse)
async def privacidad_page():
    """Politica de privacidad accesible via web."""
    from app.legal import render_legal_html
    return HTMLResponse(content=render_legal_html("privacidad"))


@app.get("/api/status")
async def api_status():
    return {
        "app": "FiltroLlamadas",
        "version": "1.0.0",
        "status": "running",
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