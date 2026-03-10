"""Servicio de LLM para conversación y análisis de llamadas."""
import json
import logging
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT_CONVERSACION = f"""Eres {settings.ASSISTANT_NAME}, la asistente virtual de {settings.OWNER_NAME} en Chile.

REGLAS:
- Sé amable, breve y profesional con tono chileno cercano.
- Identifica si la llamada es importante (familia, amigos, trabajo, trámites reales) o spam/marketing.
- Si es spam o marketing, sé educada pero firme: "Gracias por llamar, pero {settings.OWNER_NAME} no está interesado. Que tenga buen día."
- Si es importante, recopila la información: quién llama, motivo, urgencia, y si desean dejar un mensaje.
- Responde SIEMPRE en español chileno, máximo 2-3 oraciones por respuesta.
- NO inventes información sobre {settings.OWNER_NAME}.
"""

SYSTEM_PROMPT_ANALISIS = """Eres un analizador de llamadas telefónicas. Recibirás la transcripción completa de una llamada.

Analiza la conversación y devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{
  "categoria": "Personal|Trabajo|Trámite|Marketing",
  "prioridad": "Alta|Media|Baja",
  "resumen": "Resumen breve de máximo 2 oraciones describiendo quién llamó y para qué",
  "nombre_contacto": "Nombre de la persona que llamó si se identificó, o null"
}

REGLAS DE CLASIFICACIÓN:
- Personal: familia, amigos, invitaciones personales
- Trabajo: clientes, colegas, reuniones laborales, oportunidades de negocio
- Trámite: bancos, seguros, salud, gobierno, servicios contratados
- Marketing: ventas, ofertas, encuestas, publicidad, telemarketing, spam

REGLAS DE PRIORIDAD:
- Alta: urgente, familiar enfermo, deadline laboral, trámite con plazo
- Media: importante pero no urgente, seguimiento, consultas de trabajo
- Baja: spam, marketing, información general no solicitada

Responde SOLO con el JSON, sin texto adicional ni markdown.
"""


def generar_respuesta_conversacion(historial: list[dict]) -> str:
    """Genera la respuesta de Sofía durante la llamada."""
    try:
        mensajes = [{"role": "system", "content": SYSTEM_PROMPT_CONVERSACION}]
        mensajes.extend(historial)

        completion = openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=mensajes,
            max_tokens=200,
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generando respuesta: {e}")
        return "Disculpa, tuve un problema técnico. ¿Podrías repetir eso?"


def analizar_llamada(transcripcion: str) -> dict:
    """Analiza la transcripción completa y genera resumen estructurado."""
    try:
        completion = openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_ANALISIS},
                {"role": "user", "content": f"Transcripción de la llamada:\n\n{transcripcion}"}
            ],
            max_tokens=300,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        resultado = json.loads(completion.choices[0].message.content)

        # Validar campos obligatorios
        campos = ["categoria", "prioridad", "resumen"]
        for campo in campos:
            if campo not in resultado:
                resultado[campo] = "Desconocido" if campo != "resumen" else "No se pudo analizar la llamada."

        return resultado
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON del análisis: {e}")
        return {
            "categoria": "Desconocido",
            "prioridad": "Media",
            "resumen": "Error al analizar la llamada automáticamente.",
            "nombre_contacto": None
        }
    except Exception as e:
        logger.error(f"Error analizando llamada: {e}")
        return {
            "categoria": "Desconocido",
            "prioridad": "Media",
            "resumen": f"Error técnico: {str(e)[:100]}",
            "nombre_contacto": None
        }
