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
    FREE = "free"           # Trial 7 días con experiencia Pro completa. Luego se bloquea.
    BASICO = "basico"       # "Estudiante"
    PRO = "pro"             # "Adulto"
    PREMIUM = "premium"     # "Ejecutivo"


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
    ASISTENTE_BASICO = "asistente_basico"    # Free: Polly saluda, IA solo escucha y transcribe
    CONTESTADORA = "contestadora"            # Pro: Tu voz grabada como saludo, IA solo escucha
    AGENTE_IA = "agente_ia"          # Premium: Tu voz saluda + IA conversa como agente IA


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
    telefono_twilio = Column(String(20), nullable=True)      # Número Twilio asignado
    twilio_phone_sid = Column(String(50), nullable=True)       # SID del número Twilio (para gestión)
    password_hash = Column(String(256), nullable=False)
    creado = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    activo = Column(Boolean, default=True)

    # Plan y suscripción
    plan = Column(String(20), default=PlanTipo.FREE.value)
    plan_expira = Column(DateTime, nullable=True)
    trial_expira = Column(DateTime, nullable=True)       # Fecha fin del trial de 7 días
    trial_usado = Column(Boolean, default=False)          # True si ya usó su trial (no puede volver a Free)
    stripe_customer_id = Column(String(100), nullable=True)
    mercadopago_customer_id = Column(String(100), nullable=True)

    # Configuración del asistente
    nombre_asistente = Column(String(50), default="Dora")
    modo_filtrado = Column(String(20), default=ModoFiltrado.DESCONOCIDOS.value)
    modo_asistente = Column(String(30), default=ModoAsistente.ASISTENTE_BASICO.value)
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
    expo_push_token = Column(String(200), nullable=True)  # ExponentPushToken[xxx]

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
    """Poblar voces Polly y planes iniciales si la DB está vacía."""

    if db.query(VozDisponible).count() == 0:
        voces = [
            VozDisponible(nombre="Mia", descripcion="Femenina, español neutro latinoamericano", idioma="es-CL", genero="femenino", tipo="polly", polly_voice_id="Polly.Mia", plan_minimo="free", orden=1),
            VozDisponible(nombre="Conchita", descripcion="Femenina, español castellano cálido", idioma="es-ES", genero="femenino", tipo="polly", polly_voice_id="Polly.Conchita", plan_minimo="free", orden=2),
            VozDisponible(nombre="Lupe", descripcion="Femenina, español mexicano amigable", idioma="es-MX", genero="femenino", tipo="polly", polly_voice_id="Polly.Lupe", plan_minimo="free", orden=3),
            VozDisponible(nombre="Miguel", descripcion="Masculina, español neutro profesional", idioma="es-US", genero="masculino", tipo="polly", polly_voice_id="Polly.Miguel", plan_minimo="free", orden=4),
            VozDisponible(nombre="Andrés", descripcion="Masculina, español mexicano formal", idioma="es-MX", genero="masculino", tipo="polly", polly_voice_id="Polly.Andres", plan_minimo="free", orden=5),
        ]
        db.add_all(voces)

    # ═══════════════════════════════════════════════════════════
    # ESTRUCTURA DE PLANES (Trial + 3 pagos)
    # ═══════════════════════════════════════════════════════════
    #
    # FREE = Trial 7 días con experiencia Pro completa.
    #   Después de 7 días: se bloquea, debe elegir plan pago.
    #   No puede volver a Free nunca más (trial_usado=True).
    #
    # Contexto de mercado (Chile, 2025):
    # - Una persona promedio recibe ~8 llamadas/día = ~240/mes
    # - De esas, ~31/mes son spam (Chile top 2 en LATAM)
    # - Total realista (personales + trabajo + spam): 150-250/mes
    #
    planes_config = [
        {
            "codigo": "free",
            "nombre": "Prueba gratis 7 dias",
            "precio_mensual_usd": 0,
            "precio_anual_usd": 0,
            "llamadas_mes": 300,           # Experiencia Pro completa durante el trial
            "minutos_mes": 600,
            "voces_polly": True, "voces_elevenlabs": False, "voz_personalizada": True,
            "modo_luna": True, "analisis_avanzado": True, "prioridad_soporte": False,
            "descripcion": "7 dias gratis con todas las funciones del plan Adulto. Sin tarjeta, sin compromiso.",
            "features_json": [
                "7 dias con experiencia Pro completa",
                "Numero propio temporal",
                "La IA contesta, transcribe y analiza",
                "Graba tu voz como saludo",
                "Modo Luna incluido",
                "Resumen WhatsApp + push notification",
                "Al terminar el trial, elige tu plan",
            ],
        },
        {
            "codigo": "basico",
            "nombre": "Estudiante",
            "precio_mensual_usd": 4.99,
            "precio_anual_usd": 49.99,
            "llamadas_mes": 100,
            "minutos_mes": 200,
            "voces_polly": True, "voces_elevenlabs": False, "voz_personalizada": False,
            "modo_luna": False, "analisis_avanzado": True, "prioridad_soporte": False,
            "descripcion": "Recibes unas 3 llamadas de desconocidos al dia y no quieres distraerte mientras estudias. La IA filtra el spam y te avisa solo cuando es importante.",
            "features_json": [
                "100 llamadas/mes (~3 al dia, perfecto para filtrar desconocidos)",
                "Numero propio dedicado",
                "La IA contesta, escucha y transcribe",
                "Analisis completo: quien llamo, por que, urgencia",
                "Resumen por WhatsApp + push notification",
                "Categorizacion: Personal, Trabajo, Spam, Tramite",
            ],
        },
        {
            "codigo": "pro",
            "nombre": "Adulto",
            "precio_mensual_usd": 5.99,
            "precio_anual_usd": 59.99,
            "llamadas_mes": 300,
            "minutos_mes": 600,
            "voces_polly": True, "voces_elevenlabs": False, "voz_personalizada": True,
            "modo_luna": True, "analisis_avanzado": True, "prioridad_soporte": False,
            "destacado": True,
            "descripcion": "Te llaman bastante al dia para ofrecerte cosas que no necesitas, pero tienes miedo de perderte la llamada de alguien importante desde un numero desconocido. Tu contestadora personal con tu propia voz se encarga.",
            "features_json": [
                "300 llamadas/mes (~10 al dia, cubre a una persona activa)",
                "Todo lo del plan Estudiante +",
                "Graba tu voz como saludo personalizado",
                "Modo Luna: silencia TODO cuando necesites descansar",
                "Prompt personalizado (dile a la IA como comportarse)",
                "Integracion con Google Calendar y Outlook",
            ],
        },
        {
            "codigo": "premium",
            "nombre": "Ejecutivo",
            "precio_mensual_usd": 9.99,
            "precio_anual_usd": 99.99,
            "llamadas_mes": 9999,
            "minutos_mes": 9999,
            "voces_polly": True, "voces_elevenlabs": True, "voz_personalizada": True,
            "modo_luna": True, "analisis_avanzado": True, "prioridad_soporte": True,
            "descripcion": "Te llaman mucho para ofrecerte cosas que no necesitas, pero hay tramites y clientes que si necesitan ser atendidos. Tu secretario digital filtra, envia recados y agenda reuniones por ti, 24/7.",
            "features_json": [
                "Llamadas ilimitadas (nunca te quedas sin cobertura)",
                "Todo lo del plan Adulto +",
                "La IA CONVERSA con quien llama, no solo escucha",
                "Toma recados, agenda reuniones, filtra spam",
                "Consulta tu calendario en tiempo real",
                "Voces premium ultra-realistas",
                "Soporte prioritario",
            ],
        },
    ]

    for plan_data in planes_config:
        plan_existente = db.query(Plan).filter(Plan.codigo == plan_data["codigo"]).first()
        if plan_existente:
            for key, val in plan_data.items():
                if key != "codigo":
                    setattr(plan_existente, key if key != "precio_mensual_usd" else "precio_mensual_usd", val)
        else:
            db.add(Plan(**plan_data))

    db.commit()
