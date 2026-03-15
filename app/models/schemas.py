"""Schemas Pydantic para la API REST."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════

class RegistroRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["Juan Sebastián"])
    email: str = Field(..., examples=["juan@ejemplo.com"])
    telefono: str = Field(..., min_length=8, max_length=20, examples=["+56912345678"])
    password: str = Field(..., min_length=6, examples=["miPassword123"])
    codigo_referido: Optional[str] = Field(None, examples=["DORA-ABC123"])


class LoginRequest(BaseModel):
    email: str = Field(..., examples=["juan@ejemplo.com"])
    password: str = Field(..., examples=["miPassword123"])


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos
    perfil: dict


class PerfilResponse(BaseModel):
    uid: str
    nombre: str
    email: str
    telefono: str
    plan: str
    nombre_asistente: str
    modo_filtrado: str
    voz: dict


# ═══════════════════════════════════════════════════════════
# LLAMADAS
# ═══════════════════════════════════════════════════════════

class ResumenLlamada(BaseModel):
    categoria: str
    prioridad: str
    resumen: str
    nombre_contacto: Optional[str] = None


class LlamadaResponse(BaseModel):
    id: int
    call_sid: str
    numero_origen: Optional[str]
    fecha_inicio: datetime
    fecha_fin: Optional[datetime]
    duracion_segundos: Optional[float]
    estado: str
    transcripcion: str
    categoria: Optional[str]
    prioridad: Optional[str]
    resumen: Optional[str]
    nombre_contacto: Optional[str]
    whatsapp_enviado: bool

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_llamadas: int
    llamadas_hoy: int
    spam_bloqueado: int
    llamadas_importantes: int
    por_categoria: dict
    por_prioridad: dict
    ultimas_llamadas: List[LlamadaResponse]


# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════

class ConfiguracionUpdate(BaseModel):
    clave: str
    valor: str


# ═══════════════════════════════════════════════════════════
# VOCES Y FILTRADO
# ═══════════════════════════════════════════════════════════

class SeleccionarVozRequest(BaseModel):
    voz_id: int


class CambiarModoRequest(BaseModel):
    modo: str = Field(..., examples=["desconocidos"])
    horario_inicio: Optional[str] = Field(None, examples=["23:00"])
    horario_fin: Optional[str] = Field(None, examples=["07:00"])


class ContactosRequest(BaseModel):
    contactos: List[str] = Field(..., examples=[["+56912345678", "+56987654321"]])


# ═══════════════════════════════════════════════════════════
# PERSONALIZACIÓN (prompt, contestadora, modo asistente)
# ═══════════════════════════════════════════════════════════

class GuardarPromptRequest(BaseModel):
    prompt: str = Field(
        ..., max_length=2000,
        examples=["Soy diseñador freelance. Si llaman por trabajo, pregunta por presupuesto y plazo."]
    )


class CambiarModoAsistenteRequest(BaseModel):
    modo: str = Field(..., examples=["asistente_basico"])  # asistente_basico | contestadora | agente_ia


class PersonalizacionResponse(BaseModel):
    modo_asistente: str
    prompt_personalizado: Optional[str] = None
    audio_saludo_url: Optional[str] = None
    audio_saludo_duracion: Optional[float] = None
