"""Configuracion de tests para FiltroLlamadas.

Usa una base de datos SQLite en memoria para tests aislados.
Cada test tiene su propia sesion de DB limpia.
"""
import os
import pytest

# Limpiar proxies que interfieren con httpx/openai
for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                  "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(proxy_var, None)

# Configurar variables de entorno ANTES de importar la app
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["TWILIO_ACCOUNT_SID"] = "test-sid"
os.environ["TWILIO_AUTH_TOKEN"] = "test-token"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import Base, get_db, seed_voces_y_planes
import app.models.database as db_module
import app.api.webhooks as webhooks_module
import app.services.filtrado_service as filtrado_module
from app.main import app


# ─── Base de datos en memoria para tests ─────────────────
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Parchear SessionLocal en modulos que lo usan directamente (sin DI)
db_module.SessionLocal = TestingSessionLocal
webhooks_module.SessionLocal = TestingSessionLocal
filtrado_module.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def setup_db():
    """Crea tablas y datos iniciales antes de cada test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        seed_voces_y_planes(db)
    except Exception:
        pass
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Cliente HTTP para tests."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Sesion de DB para tests que necesitan acceso directo."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def usuario_registrado(client):
    """Registra un usuario de test y retorna tokens + perfil."""
    response = client.post("/auth/registro", json={
        "nombre": "Test User",
        "email": "test@example.com",
        "telefono": "+56912345678",
        "password": "test123456",
    })
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_headers(usuario_registrado):
    """Headers con Bearer token para endpoints protegidos."""
    token = usuario_registrado["access_token"]
    return {"Authorization": f"Bearer {token}"}
