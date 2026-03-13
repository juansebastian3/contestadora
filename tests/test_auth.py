"""Tests para el sistema de autenticacion (registro, login, refresh, perfil)."""


class TestRegistro:
    """Tests de registro de usuario."""

    def test_registro_exitoso(self, client):
        response = client.post("/auth/registro", json={
            "nombre": "Juan Test",
            "email": "juan@test.com",
            "telefono": "+56911111111",
            "password": "mipassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["perfil"]["nombre"] == "Juan Test"
        assert data["perfil"]["email"] == "juan@test.com"
        assert data["perfil"]["plan"] == "free"

    def test_registro_email_duplicado(self, client, usuario_registrado):
        response = client.post("/auth/registro", json={
            "nombre": "Otro User",
            "email": "test@example.com",  # Ya existe
            "telefono": "+56922222222",
            "password": "password123",
        })
        assert response.status_code == 409
        assert "email" in response.json()["detail"].lower()

    def test_registro_telefono_duplicado(self, client, usuario_registrado):
        response = client.post("/auth/registro", json={
            "nombre": "Otro User",
            "email": "otro@test.com",
            "telefono": "+56912345678",  # Ya existe
            "password": "password123",
        })
        assert response.status_code == 409

    def test_registro_password_corta(self, client):
        response = client.post("/auth/registro", json={
            "nombre": "Test",
            "email": "short@test.com",
            "telefono": "+56933333333",
            "password": "123",  # Muy corta
        })
        assert response.status_code in (400, 422)  # Pydantic valida con 422

    def test_registro_telefono_sin_codigo_pais(self, client):
        response = client.post("/auth/registro", json={
            "nombre": "Test",
            "email": "nocode@test.com",
            "telefono": "912345678",  # Sin +
            "password": "password123",
        })
        assert response.status_code == 400


class TestLogin:
    """Tests de login."""

    def test_login_exitoso(self, client, usuario_registrado):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "test123456",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["perfil"]["email"] == "test@example.com"

    def test_login_email_incorrecto(self, client, usuario_registrado):
        response = client.post("/auth/login", json={
            "email": "noexiste@test.com",
            "password": "test123456",
        })
        assert response.status_code == 401

    def test_login_password_incorrecta(self, client, usuario_registrado):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "passwordmal",
        })
        assert response.status_code == 401


class TestRefresh:
    """Tests de refresh token."""

    def test_refresh_exitoso(self, client, usuario_registrado):
        refresh_token = usuario_registrado["refresh_token"]
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_token_invalido(self, client):
        response = client.post("/auth/refresh", json={
            "refresh_token": "token-falso-invalido",
        })
        assert response.status_code == 401


class TestPerfil:
    """Tests de acceso al perfil."""

    def test_perfil_autenticado(self, client, auth_headers):
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    def test_perfil_sin_token(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_perfil_token_invalido(self, client):
        response = client.get("/auth/me", headers={
            "Authorization": "Bearer token-invalido"
        })
        assert response.status_code == 401
