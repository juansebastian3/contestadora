"""Base de datos SQLite con SQLAlchemy - Modelos completos para producción."""
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime,
    Float, Boolean, ForeignKey, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
import enum
import uuid

from app.core.config import settings

# check_same_thread solo aplica a SQLite
_connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ═══════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════

class PlanTipo(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"


class Categoria(str, enum.Enum):
    PERSONAL = "Personal"
    TRABAJO = "Trabajo"
    TRAMITE = "Trámite"
    MARKETING = "Marketing"
    DESCONOCIDO = "Desconocido"


class Prioridad(str, enum.Enum):
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"


class EstadoLlamada(str, enum.Enum):
    EN_CURSO = "en_curso"
    FINALIZADA = "finalizada"
    PERDIDA = "perdida"
    BLOQUEADA = "bloqueada"


class ModoFiltrado(str, enum.Enum):
    DESCONOCIDOS = "desconocidos"    # Solo filtra números no guardados
    LUNA = "luna"                     # Filtra TODAS las llamadas (modo no molestar total)
    DESACTIVADO = "desactivado"      # No filtra nada


class ModoAsistente(str, enum.Enum):
    IA_CONVERSACIONAL = "ia_conversacional"  # Sofía conversa con el llamante (default)
    CONTESTADORA = "contestadora"            # Audio grabado del usuario + IA solo escucha
    HIBRIDO = "hibrido"                      # Audio grabado como saludo + IA toma el control después


class CalendarioModo(str, enum.Enum):
    SOLO_REUNIONES = "solo_reuniones"   # Activa solo durante reuniones del calendario
    SIEMPRE_AGENDA = "siempre_agenda"   # Activa si hay CUALQUIER evento (incluso todo el día)
    MANUAL = "manual"                    # No auto-activar, el usuario decide


class EstadoSuscripcion(str, enum.Enum):
    PENDIENTE = "pendiente"        # Pago iniciado pero no completado
    ACTIVA = "activa"              # Pago aprobado, suscripción vigente
    CANCELADA = "cancelada"        # Usuario canceló
    EXPIRADA = "expirada"          # No se renovó
    RECHAZADA = "rechazada"        # Pago rechazado


class TipoVoz(str, enum.Enum):
    POLLY = "polly"            # Gratuita - Amazon Polly vía Twilio
    ELEVENLABS = "elevenlabs"  # Premium - ElevenLabs


# ═══════════════════════════════════════════════════════════
# MODELO: USUARIO
# ═══════════════════════════════════════════════════════════

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    telefono = Column(String(20), unique=True, nullable=False)
    telefono_twilio = Column(String(20), nullable=True)
    password_hash = Column(String(256), nullable=False)
    creado = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    activo = Column(Boolean, default=True)

    # Plan y suscripción
    plan = Column(String(20), default=PlanTipo.FREE.value)
    plan_expira = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(100), nullable=True)
    mercadopago_customer_id = Column(String(100), nullable=True)

    # Configuración del asistente
    nombre_asistente = Column(String(50), default="Sofía")
    modo_filtrado = Column(String(20), default=ModoFiltrado.DESCONOCIDOS.value)
    modo_asistente = Column(String(30), default=ModoAsistente.IA_CONVERSACIONAL.value)
    horario_luna_inicio = Column(String(5), nullable=True)  # "23:00"
    horario_luna_fin = Column(String(5), nullable=True)      # "07:00"

    # Prompt personalizado: el usuario escribe cómo quiere que la IA se comporte
    # Ej: "Soy diseñador freelance, si llaman por trabajo pide presupuesto y plazo"
    prompt_personalizado = Column(Text, nullable=True)

    # Modo contestadora: URL del audio grabado por el usuario
    # Se sube desde la app y se almacena en /audio_uploads/{uid}/saludo.mp3
    audio_saludo_url = Column(String(500), nullable=True)
    audio_saludo_duracion = Column(Float, nullable=True)  # segundos

    # Voz seleccionada
    voz_tipo = Column(String(20), default=TipoVoz.POLLY.value)
    voz_polly_id = Column(String(50), default="Polly.Mia")
    voz_elevenlabs_id = Column(String(50), nullable=True)
    voz_personalizada_id = Column(String(50), nullable=True)

    # Notificaciones
    notif_whatsapp = Column(Boolean, default=True)
    notif_push = Column(Boolean, default=True)
    notif_solo_importantes = Column(Boolean, default=False)

    # Contactos conocidos (JSON array de números)
    contactos_conocidos = Column(JSON, default=list)

    # Integración Calendarios (Pro/Premium)
    google_calendar_token = Column(JSON, nullable=True)      # {access_token, refresh_token, expiry}
    outlook_calendar_token = Column(JSON, nullable=True)     # {access_token, refresh_token, expiry}
    calendario_auto_activar = Column(Boolean, default=False) # Activar contestadora según agenda
    calendario_modo = Column(String(30), default="solo_reuniones")  # solo_reuniones | siempre_agenda | manual

    # Relaciones
    llamadas = relationship("Llamada", back_populates="usuario")


# ═══════════════════════════════════════════════════════════
# MODELO: CATÁLOGO DE VOCES
# ═══════════════════════════════════════════════════════════

class VozDisponible(Base):
    __tablename__ = "voces_disponibles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(String(200), nullable=True)
    idioma = Column(String(10), default="es-CL")
    genero = Column(String(20), default="femenino")

    # Tipo y IDs
    tipo = Column(String(20), nullable=False)              # polly, elevenlabs
    polly_voice_id = Column(String(50), nullable=True)
    elevenlabs_voice_id = Column(String(50), nullable=True)

    # Disponibilidad
    plan_minimo = Column(String(20), default=PlanTipo.FREE.value)
    activa = Column(Boolean, default=True)
    preview_url = Column(String(300), nullable=True)
    orden = Column(Integer, default=0)


# ═══════════════════════════════════════════════════════════
# MODELO: LLAMADA (con filtrado y usuario)
# ═══════════════════════════════════════════════════════════

class Llamada(Base):
    __tablename__ = "llamadas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    call_sid = Column(String(64), unique=True, index=True, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    numero_origen = Column(String(20), nullable=True)
    fecha_inicio = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_fin = Column(DateTime, nullable=True)
    duracion_segundos = Column(Float, nullable=True)
    estado = Column(String(20), default=EstadoLlamada.EN_CURSO.value)

    # Filtrado
    fue_filtrada = Column(Boolean, default=True)
    numero_conocido = Column(Boolean, default=False)
    modo_activo = Column(String(20), nullable=True)

    # Transcripción completa
    transcripcion = Column(Text, default="")

    # Análisis del LLM
    categoria = Column(String(20), nullable=True)
    prioridad = Column(String(10), nullable=True)
    resumen = Column(Text, nullable=True)
    nombre_contacto = Column(String(100), nullable=True)

    # WhatsApp
    whatsapp_enviado = Column(Integer, default=0)
    whatsapp_sid = Column(String(64), nullable=True)

    # Relaciones
    usuario = relationship("Usuario", back_populates="llamadas")


# ═══════════════════════════════════════════════════════════
# MODELO: PLANES Y PRECIOS
# ═══════════════════════════════════════════════════════════

class Plan(Base):
    __tablename__ = "planes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    precio_mensual_usd = Column(Float, default=0.0)
    precio_anual_usd = Column(Float, default=0.0)

    # Límites
    llamadas_mes = Column(Integer, default=30)
    minutos_mes = Column(Integer, default=60)
    voces_polly = Column(Boolean, default=True)
    voces_elevenlabs = Column(Boolean, default=False)
    voz_personalizada = Column(Boolean, default=False)
    modo_luna = Column(Boolean, default=False)
    analisis_avanzado = Column(Boolean, default=False)
    prioridad_soporte = Column(Boolean, default=False)

    # Metadata
    destacado = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)
    descripcion = Column(Text, nullable=True)
    features_json = Column(JSON, default=list)


# ═══════════════════════════════════════════════════════════
# MODELO: NÚMEROS BLOQUEADOS
# ═══════════════════════════════════════════════════════════

class NumeroBloqueado(Base):
    __tablename__ = "numeros_bloqueados"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    numero = Column(String(20), nullable=False)
    razon = Column(String(100), nullable=True)
    creado = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════
# MODELO: SUSCRIPCIONES (MercadoPago / Apple IAP / Google Play)
# ═══════════════════════════════════════════════════════════

class Suscripcion(Base):
    __tablename__ = "suscripciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    plan_codigo = Column(String(20), nullable=False)  # pro, premium

    # Origen del pago
    origen = Column(String(20), nullable=False)  # mercadopago, apple_iap, google_play
    estado = Column(String(20), default=EstadoSuscripcion.PENDIENTE.value)

    # MercadoPago
    mp_preference_id = Column(String(100), nullable=True)
    mp_payment_id = Column(String(100), nullable=True)
    mp_subscription_id = Column(String(100), nullable=True)
    mp_external_reference = Column(String(100), nullable=True, index=True)

    # Periodo
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    periodo = Column(String(10), default="mensual")  # mensual, anual

    # Montos
    monto = Column(Float, nullable=True)
    moneda = Column(String(5), default="USD")

    # Metadata
    creado = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    actualizado = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))

    usuario = relationship("Usuario")


# ═══════════════════════════════════════════════════════════
# MODELO: CONFIGURACIÓN (legacy, mantener para compatibilidad)
# ═══════════════════════════════════════════════════════════

class Configuracion(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True)
    clave = Column(String(50), unique=True, nullable=False)
    valor = Column(Text, nullable=True)
    actualizado = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Crear tablas
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_voces_y_planes(db):
    """Poblar voces y planes iniciales si la DB está vacía."""

    if db.query(VozDisponible).count() == 0:
        voces = [
            VozDisponible(nombre="Mia", descripcion="Femenina, español neutro latinoamericano", idioma="es-CL", genero="femenino", tipo="polly", polly_voice_id="Polly.Mia", plan_minimo="free", orden=1),
            VozDisponible(nombre="Conchita", descripcion="Femenina, español castellano cálido", idioma="es-ES", genero="femenino", tipo="polly", polly_voice_id="Polly.Conchita", plan_minimo="free", orden=2),
            VozDisponible(nombre="Lupe", descripcion="Femenina, español mexicano amigable", idioma="es-MX", genero="femenino", tipo="polly", polly_voice_id="Polly.Lupe", plan_minimo="free", orden=3),
            VozDisponible(nombre="Miguel", descripcion="Masculina, español neutro profesional", idioma="es-US", genero="masculino", tipo="polly", polly_voice_id="Polly.Miguel", plan_minimo="free", orden=4),
            VozDisponible(nombre="Andrés", descripcion="Masculina, español mexicano formal", idioma="es-MX", genero="masculino", tipo="polly", polly_voice_id="Polly.Andres", plan_minimo="free", orden=5),
            VozDisponible(nombre="Valentina", descripcion="IA ultra-realista femenina, natural y cálida", idioma="es-CL", genero="femenino", tipo="elevenlabs", elevenlabs_voice_id="oJIuRMopN0sojGjwD6rQ", plan_minimo="pro", orden=10),
            VozDisponible(nombre="Mateo", descripcion="IA ultra-realista masculina, profesional", idioma="es-CL", genero="masculino", tipo="elevenlabs", elevenlabs_voice_id="pNInz6obpgDQGcFmaJgB", plan_minimo="pro", orden=11),
            VozDisponible(nombre="Isabella", descripcion="IA premium femenina, elegante y sofisticada", idioma="es-CL", genero="femenino", tipo="elevenlabs", elevenlabs_voice_id="EXAVITQu4vr4xnSDxMaL", plan_minimo="pro", orden=12),
        ]
        db.add_all(voces)

    if db.query(Plan).count() == 0:
        planes = [
            Plan(
                codigo="free", nombre="Gratis", precio_mensual_usd=0, precio_anual_usd=0,
                llamadas_mes=30, minutos_mes=60,
                voces_polly=True, voces_elevenlabs=False, voz_personalizada=False,
                modo_luna=False, analisis_avanzado=False, prioridad_soporte=False,
                descripcion="Contestadora IA para llamadas desconocidas",
                features_json=["30 llamadas/mes", "60 min de filtrado", "5 voces estándar", "Resumen WhatsApp", "Modo desconocidos"],
            ),
            Plan(
                codigo="pro", nombre="Pro", precio_mensual_usd=4.99, precio_anual_usd=49.99,
                llamadas_mes=200, minutos_mes=500,
                voces_polly=True, voces_elevenlabs=True, voz_personalizada=True,
                modo_luna=True, analisis_avanzado=True, prioridad_soporte=False,
                destacado=True,
                descripcion="Graba tu propia contestadora + modo luna",
                features_json=["200 llamadas/mes", "500 min de filtrado", "Voces IA ElevenLabs", "Graba tu contestadora", "Prompt personalizado", "Modo Luna", "Análisis avanzado", "Google Calendar + Outlook"],
            ),
            Plan(
                codigo="premium", nombre="Premium", precio_mensual_usd=12.99, precio_anual_usd=129.99,
                llamadas_mes=9999, minutos_mes=9999,
                voces_polly=True, voces_elevenlabs=True, voz_personalizada=True,
                modo_luna=True, analisis_avanzado=True, prioridad_soporte=True,
                descripcion="Todo ilimitado + soporte prioritario",
                features_json=["Llamadas ilimitadas", "Minutos ilimitados", "Todas las voces", "Graba tu contestadora", "Prompt personalizado", "Modo Luna con horario", "Google Calendar + Outlook", "Soporte prioritario"],
            ),
        ]
        db.add_all(planes)

    db.commit()
