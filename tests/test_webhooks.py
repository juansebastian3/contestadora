"""Tests para los webhooks de Twilio (llamadas de voz)."""


class TestWebhookIncoming:
    """Tests del webhook de llamada entrante."""

    def test_incoming_sin_usuario(self, client):
        """Una llamada a un numero no asignado devuelve TwiML valido."""
        response = client.post("/webhooks/voice/incoming", data={
            "CallSid": "CA_test_123",
            "From": "+56911111111",
            "To": "+12025551234",
        })
        assert response.status_code == 200
        assert "xml" in response.headers.get("content-type", "")
        # Debe contener TwiML valido (respuesta de voz)
        body = response.text
        assert "<Response>" in body
        assert "<Say" in body or "<Gather" in body

    def test_incoming_retorna_twiml(self, client):
        """Cualquier llamada debe retornar TwiML valido."""
        response = client.post("/webhooks/voice/incoming", data={
            "CallSid": "CA_test_456",
            "From": "+56922222222",
            "To": "+12025559999",
        })
        assert response.status_code == 200
        body = response.text
        assert body.startswith("<?xml") or "<Response>" in body


class TestWebhookEscucharRecado:
    """Tests del webhook de recado (Free/Pro)."""

    def test_escuchar_recado(self, client):
        """El webhook de recado acepta speech result."""
        response = client.post("/webhooks/voice/escuchar-recado", data={
            "CallSid": "CA_test_recado",
            "SpeechResult": "Hola, soy Carlos, llamo por el proyecto de diseno",
        })
        assert response.status_code == 200
        body = response.text
        assert "<Response>" in body

    def test_escuchar_recado_vacio(self, client):
        """El webhook maneja speech result vacio."""
        response = client.post("/webhooks/voice/escuchar-recado", data={
            "CallSid": "CA_test_vacio",
            "SpeechResult": "",
        })
        assert response.status_code == 200


class TestWebhookStatus:
    """Tests del webhook de status (post-llamada)."""

    def test_status_completed(self, client):
        """El webhook de status procesa una llamada completada."""
        response = client.post("/webhooks/voice/status", data={
            "CallSid": "CA_test_status",
            "CallStatus": "completed",
            "CallDuration": "45",
        })
        assert response.status_code == 200

    def test_status_failed(self, client):
        """El webhook maneja llamadas fallidas sin error."""
        response = client.post("/webhooks/voice/status", data={
            "CallSid": "CA_test_failed",
            "CallStatus": "failed",
            "CallDuration": "0",
        })
        assert response.status_code == 200

    def test_status_canceled(self, client):
        """El webhook maneja llamadas canceladas."""
        response = client.post("/webhooks/voice/status", data={
            "CallSid": "CA_test_cancel",
            "CallStatus": "canceled",
            "CallDuration": "0",
        })
        assert response.status_code == 200


class TestWebhookAgente:
    """Tests del webhook del agente IA (Premium)."""

    def test_agente_procesar(self, client):
        """El webhook del agente acepta speech y responde."""
        response = client.post("/webhooks/voice/agente-procesar", data={
            "CallSid": "CA_test_agente",
            "To": "+12025551234",
            "SpeechResult": "Necesito hablar con Juan por favor",
        })
        assert response.status_code == 200
        body = response.text
        assert "<Response>" in body


class TestLandingYLegal:
    """Tests de paginas publicas."""

    def test_landing_page(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "ContestaDora" in response.text

    def test_terminos_page(self, client):
        response = client.get("/terminos")
        assert response.status_code == 200
        assert "Terminos" in response.text

    def test_privacidad_page(self, client):
        response = client.get("/privacidad")
        assert response.status_code == 200
        assert "Privacidad" in response.text
