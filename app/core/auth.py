"""Sistema de autenticación JWT para FiltroLlamadas.

Flujo completo:
─────────────────────────────────────────────────────────────────
  REGISTRO (/auth/registro):
    1. Usuario envía nombre, email, teléfono, password
    2. Se valida que email y teléfono no existan
    3. Se hashea la contraseña con bcrypt
    4. Se crea el usuario en DB con plan "free"
    5. Se retorna access_token + refresh_token + perfil

  LOGIN (/auth/login):
    1. Usuario envía email + password
    2. Se verifica la contraseña contra el hash en DB
    3. Se retorna access_token + refresh_token + perfil

  REFRESH (/auth/refresh):
    1. App envía refresh_token cuando el access_token expira
    2. Se valida y genera nuevo access_token
    3. Sin necesidad de re-login

  PROTECCIÓN DE ENDPOINTS:
    - get_current_user: Dependencia FastAPI que extrae el usuario
      del Bearer token en cada request protegido
    - Los webhooks de Twilio NO llevan auth (Twilio no envía JWT)
    - La API móvil SÍ requiere auth en cada endpoint
─────────────────────────────────────────────────────────────────
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.database import get_db, Usuario, PlanTipo, ModoFiltrado, TipoVoz
from app.models.schemas import (
    RegistroRequest,
    LoginRequest,
    TokenResponse,
    PerfilResponse,
    RefreshRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE SEGURIDAD
# ═══════════════════════════════════════════════════════════

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(usuario_uid: str) -> str:
    return _create_token(
        {"sub": usuario_uid, "type": "access"},
        timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
    )


def create_refresh_token(usuario_uid: str) -> str:
    return _create_token(
        {"sub": usuario_uid, "type": "refresh"},
        timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
    )


def _decode_token(token: str) -> dict:
    """Decodifica y valida un JWT. Lanza HTTPException si es inválido."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verificar_token(token: str) -> Optional[dict]:
    """Verifica un JWT y retorna el payload, o None si es inválido.

    Versión que no lanza excepciones (útil para verificación en páginas web).
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") == "access":
            return {"uid": payload.get("sub")}
        return None
    except JWTError:
        return None


# ═══════════════════════════════════════════════════════════
# DEPENDENCIA: OBTENER USUARIO ACTUAL
# ═══════════════════════════════════════════════════════════

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependencia FastAPI que extrae el usuario autenticado del JWT.

    Uso en endpoints:
        @router.get("/mi-endpoint")
        async def mi_endpoint(usuario: Usuario = Depends(get_current_user)):
            # usuario ya está validado y cargado de la DB
    """
    payload = _decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere un access token, no un refresh token",
        )

    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Token malformado")

    usuario = db.query(Usuario).filter(Usuario.uid == uid).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    return usuario


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _build_perfil(u: Usuario) -> dict:
    """Construye el dict de perfil para incluir en la respuesta de auth."""
    return {
        "uid": u.uid,
        "nombre": u.nombre,
        "email": u.email,
        "telefono": u.telefono,
        "plan": u.plan,
        "nombre_asistente": u.nombre_asistente,
        "modo_filtrado": u.modo_filtrado,
        "telefono_twilio": u.telefono_twilio,
        "voz": {
            "tipo": u.voz_tipo,
            "polly_id": u.voz_polly_id,
        },
    }


def _build_token_response(usuario: Usuario) -> dict:
    """Genera la respuesta completa con tokens + perfil."""
    return {
        "access_token": create_access_token(usuario.uid),
        "refresh_token": create_refresh_token(usuario.uid),
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        "perfil": _build_perfil(usuario),
    }


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("/registro", response_model=TokenResponse)
async def registro(data: RegistroRequest, db: Session = Depends(get_db)):
    """Registra un nuevo usuario y retorna tokens de acceso.

    El usuario comienza con plan "free", voz Polly.Mia,
    y modo de filtrado "desconocidos".
    """
    # Validar que no exista
    if db.query(Usuario).filter(Usuario.email == data.email).first():
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con este email")

    if db.query(Usuario).filter(Usuario.telefono == data.telefono).first():
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con este número de teléfono")

    # Validaciones básicas
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    if not data.telefono.startswith("+"):
        raise HTTPException(status_code=400, detail="El teléfono debe incluir código de país (ej: +56912345678)")

    # Crear usuario con trial de 7 días (experiencia Pro completa)
    trial_fin = datetime.now(timezone.utc) + timedelta(days=7)
    nuevo = Usuario(
        nombre=data.nombre,
        email=data.email.lower().strip(),
        telefono=data.telefono.strip(),
        password_hash=_hash_password(data.password),
        plan=PlanTipo.FREE.value,
        trial_expira=trial_fin,
        trial_usado=False,
        modo_filtrado=ModoFiltrado.DESCONOCIDOS.value,
        voz_tipo=TipoVoz.POLLY.value,
        voz_polly_id="Polly.Mia",
        nombre_asistente="Dora",
    )
    # Detectar país por teléfono
    from app.services.geo_pricing_service import detectar_pais_por_telefono
    nuevo.pais_codigo = detectar_pais_por_telefono(data.telefono)

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    # Procesar código de referido si viene
    if data.codigo_referido:
        try:
            from app.services.referidos_service import registrar_referido
            registrar_referido(db, nuevo, data.codigo_referido)
        except Exception as e:
            logger.warning(f"Error procesando referido: {e}")

    # Programar drip campaigns de retención
    try:
        from app.services.drip_campaigns_service import programar_drip_para_usuario
        programar_drip_para_usuario(db, nuevo)
    except Exception as e:
        logger.warning(f"Error programando drip campaigns: {e}")

    logger.info(f"✅ Nuevo usuario registrado: {nuevo.nombre} ({nuevo.email}) [país: {nuevo.pais_codigo}]")
    return _build_token_response(nuevo)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Autentica con email + password y retorna tokens."""
    usuario = db.query(Usuario).filter(
        Usuario.email == data.email.lower().strip()
    ).first()

    if not usuario or not _verify_password(data.password, usuario.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos",
        )

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    logger.info(f"🔑 Login: {usuario.nombre} ({usuario.email})")
    return _build_token_response(usuario)


@router.post("/login-form", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login compatible con OAuth2 form (para Swagger UI /docs).

    Username = email del usuario.
    """
    usuario = db.query(Usuario).filter(
        Usuario.email == form_data.username.lower().strip()
    ).first()

    if not usuario or not _verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    return _build_token_response(usuario)


@router.post("/refresh")
async def refresh_token(data: RefreshRequest, db: Session = Depends(get_db)):
    """Renueva el access_token usando un refresh_token válido.

    La app móvil debe llamar a este endpoint cuando el access_token
    expire (status 401), enviando el refresh_token guardado.
    """
    payload = _decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Se requiere un refresh token")

    uid = payload.get("sub")
    usuario = db.query(Usuario).filter(Usuario.uid == uid).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o desactivado")

    # Generar nuevo access_token (el refresh_token se mantiene)
    return {
        "access_token": create_access_token(usuario.uid),
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    }


@router.get("/me")
async def mi_perfil(usuario: Usuario = Depends(get_current_user)):
    """Retorna el perfil del usuario autenticado. Útil para verificar el token."""
    return _build_perfil(usuario)


@router.post("/cambiar-password")
async def cambiar_password(
    password_actual: str,
    password_nueva: str,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cambia la contraseña del usuario autenticado."""
    if not _verify_password(password_actual, usuario.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    if len(password_nueva) < 6:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 6 caracteres")

    usuario.password_hash = _hash_password(password_nueva)
    db.commit()
    return {"status": "ok", "message": "Contraseña actualizada"}
