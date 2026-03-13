"""Tests para la API movil (endpoints protegidos)."""


class TestHealth:
    """Tests de health check."""

    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] in ("ok", "healthy")

    def test_api_status(self, client):
        response = client.get("/api/status")
        assert response.status_code == 200
        assert response.json()["app"] == "FiltroLlamadas"


class TestDashboard:
    """Tests del dashboard."""

    def test_dashboard_autenticado(self, client, auth_headers):
        response = client.get("/api/v1/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_llamadas" in data
        assert "llamadas_hoy" in data
        assert data["total_llamadas"] == 0  # Usuario nuevo, sin llamadas

    def test_dashboard_sin_auth(self, client):
        response = client.get("/api/v1/dashboard")
        assert response.status_code == 401


class TestPerfil:
    """Tests del perfil de usuario."""

    def test_obtener_perfil(self, client, auth_headers):
        response = client.get("/api/v1/perfil", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "free"
        assert data["modo_filtrado"] == "desconocidos"
        assert "personalizacion" in data
        assert "calendario" in data

    def test_cambiar_modo_filtrado(self, client, auth_headers):
        response = client.post("/api/v1/perfil/modo-filtrado",
            headers=auth_headers,
            json={"modo": "desactivado"},
        )
        assert response.status_code == 200
        assert response.json()["modo"] == "desactivado"

    def test_cambiar_modo_filtrado_invalido(self, client, auth_headers):
        response = client.post("/api/v1/perfil/modo-filtrado",
            headers=auth_headers,
            json={"modo": "modo_falso"},
        )
        assert response.status_code == 400

    def test_modo_luna_requiere_plan(self, client, auth_headers):
        """El modo luna requiere plan Pro o Premium."""
        response = client.post("/api/v1/perfil/modo-filtrado",
            headers=auth_headers,
            json={"modo": "luna"},
        )
        assert response.status_code == 403


class TestPersonalizacion:
    """Tests de personalizacion del asistente."""

    def test_obtener_personalizacion(self, client, auth_headers):
        response = client.get("/api/v1/perfil/personalizacion", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["modo_asistente"] == "asistente_basico"

    def test_guardar_prompt(self, client, auth_headers):
        response = client.post("/api/v1/perfil/prompt",
            headers=auth_headers,
            json={"prompt": "Soy veterinario, si llaman por emergencia pide sintomas"},
        )
        assert response.status_code == 200
        assert response.json()["prompt_guardado"] is True

    def test_borrar_prompt(self, client, auth_headers):
        # Primero guardar
        client.post("/api/v1/perfil/prompt",
            headers=auth_headers,
            json={"prompt": "algo"},
        )
        # Luego borrar
        response = client.delete("/api/v1/perfil/prompt", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["prompt_guardado"] is False

    def test_cambiar_modo_agente_requiere_premium(self, client, auth_headers):
        """El modo agente_ia requiere plan Premium."""
        response = client.post("/api/v1/perfil/modo-asistente",
            headers=auth_headers,
            json={"modo": "agente_ia"},
        )
        # Falla porque usuario free no tiene audio ni plan premium
        assert response.status_code in (400, 403)


class TestVoces:
    """Tests del catalogo de voces."""

    def test_listar_voces(self, client):
        response = client.get("/api/v1/voces")
        assert response.status_code == 200
        voces = response.json()
        assert isinstance(voces, list)


class TestPlanes:
    """Tests del catalogo de planes."""

    def test_listar_planes(self, client):
        response = client.get("/api/v1/planes")
        assert response.status_code == 200
        planes = response.json()
        assert isinstance(planes, list)


class TestLlamadas:
    """Tests de historial de llamadas."""

    def test_listar_llamadas_vacio(self, client, auth_headers):
        response = client.get("/api/v1/llamadas", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_llamada_inexistente(self, client, auth_headers):
        response = client.get("/api/v1/llamadas/99999", headers=auth_headers)
        assert response.status_code == 404


class TestPushToken:
    """Tests de registro de push token."""

    def test_registrar_push_token(self, client, auth_headers):
        response = client.post("/api/v1/push-token",
            headers=auth_headers,
            json={"expo_push_token": "ExponentPushToken[test123abc]"},
        )
        assert response.status_code == 200
        assert response.json()["push_registrado"] is True

    def test_push_token_invalido(self, client, auth_headers):
        response = client.post("/api/v1/push-token",
            headers=auth_headers,
            json={"expo_push_token": "token-invalido"},
        )
        assert response.status_code == 400


class TestNumeroTwilio:
    """Tests del numero Twilio."""

    def test_obtener_numero_sin_asignar(self, client, auth_headers):
        response = client.get("/api/v1/mi-numero", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["tiene_numero"] is False


class TestEstadisticas:
    """Tests de estadisticas."""

    def test_stats_semanales(self, client, auth_headers):
        response = client.get("/api/v1/stats/semanal", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "semana" in data
        assert len(data["semana"]) == 7
