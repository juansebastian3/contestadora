"""Paginas legales de FiltroLlamadas - Terminos y Privacidad.

Genera HTML para las rutas /terminos y /privacidad.
Reutiliza el estilo visual de la landing page.
"""


def render_legal_html(tipo: str = "terminos") -> str:
    """Genera el HTML de la pagina legal solicitada."""

    if tipo == "privacidad":
        titulo = "Politica de Privacidad"
        contenido = _privacidad_html()
    else:
        titulo = "Terminos de Servicio"
        contenido = _terminos_html()

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo} - FiltroLlamadas</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: #0F0F23;
            color: #B0B0D0;
            line-height: 1.7;
        }}
        .container {{
            max-width: 720px;
            margin: 0 auto;
            padding: 60px 24px 80px;
        }}
        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #6C63FF;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 32px;
        }}
        .back-link:hover {{ opacity: 0.8; }}
        h1 {{
            font-size: 32px;
            font-weight: 800;
            color: #fff;
            margin-bottom: 8px;
        }}
        .fecha {{
            font-size: 13px;
            color: #6B6B8D;
            margin-bottom: 40px;
        }}
        .tabs {{
            display: flex;
            gap: 4px;
            background: #1A1A2E;
            border-radius: 12px;
            padding: 4px;
            margin-bottom: 40px;
        }}
        .tab {{
            flex: 1;
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            color: #6B6B8D;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .tab.active {{
            background: #6C63FF;
            color: #fff;
        }}
        .tab:hover:not(.active) {{ color: #B0B0D0; }}
        h2 {{
            font-size: 18px;
            font-weight: 700;
            color: #fff;
            margin-top: 32px;
            margin-bottom: 12px;
        }}
        p {{
            margin-bottom: 16px;
            font-size: 15px;
        }}
        .contacto {{
            background: #1A1A2E;
            border-radius: 12px;
            padding: 20px;
            margin-top: 40px;
            font-size: 14px;
        }}
        .contacto a {{
            color: #6C63FF;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">&larr; Volver al inicio</a>

        <div class="tabs">
            <a href="/terminos" class="tab {'active' if tipo == 'terminos' else ''}">Terminos</a>
            <a href="/privacidad" class="tab {'active' if tipo == 'privacidad' else ''}">Privacidad</a>
        </div>

        <h1>{titulo}</h1>
        <p class="fecha">Ultima actualizacion: 12 de marzo de 2026</p>

        {contenido}

        <div class="contacto">
            Dudas? Escribe a <a href="mailto:soporte@filtrollamadas.com">soporte@filtrollamadas.com</a>
        </div>
    </div>
</body>
</html>"""


def _terminos_html() -> str:
    return """
<h2>1. Aceptacion de los terminos</h2>
<p>Al crear una cuenta y utilizar FiltroLlamadas, aceptas estos Terminos de Servicio en su totalidad. Si no estas de acuerdo con alguna parte, no debes usar el servicio. Nos reservamos el derecho de modificar estos terminos con previo aviso de 30 dias.</p>

<h2>2. Descripcion del servicio</h2>
<p>FiltroLlamadas es un servicio de asistencia telefonica basado en inteligencia artificial que filtra, contesta y transcribe llamadas en tu nombre. El servicio incluye: recepcion de llamadas desviadas, transcripcion automatica, resumen por WhatsApp, y gestion de agenda segun tu plan contratado.</p>

<h2>3. Planes y pagos</h2>
<p>Ofrecemos planes Gratis, Pro ($4.99/mes) y Premium ($9.99/mes). Los pagos se procesan a traves de MercadoPago. Puedes cancelar tu suscripcion en cualquier momento. Al cancelar, mantendras acceso hasta el final del periodo facturado. No ofrecemos reembolsos parciales por periodos no utilizados.</p>

<h2>4. Uso del numero telefonico</h2>
<p>Al suscribirte a un plan de pago, se te asigna un numero de telefono virtual. Este numero es propiedad de FiltroLlamadas y se te presta mientras mantengas tu suscripcion activa. Si cancelas, el numero puede ser reasignado despues de 30 dias de inactividad.</p>

<h2>5. Grabacion y transcripcion de llamadas</h2>
<p>Al utilizar el servicio, las llamadas recibidas por tu asistente seran procesadas por inteligencia artificial para generar transcripciones y resumenes. Es tu responsabilidad informar a terceros que las llamadas pueden ser grabadas y transcritas, segun la legislacion aplicable en tu jurisdiccion.</p>

<h2>6. Conducta del usuario</h2>
<p>Te comprometes a no usar el servicio para actividades ilegales, fraudulentas, acoso, spam, o cualquier proposito que viole los derechos de terceros. Nos reservamos el derecho de suspender cuentas que incumplan estas condiciones.</p>

<h2>7. Disponibilidad del servicio</h2>
<p>Nos esforzamos por mantener el servicio disponible 24/7, pero no garantizamos disponibilidad ininterrumpida. Pueden ocurrir interrupciones por mantenimiento, actualizaciones o circunstancias fuera de nuestro control. No somos responsables por llamadas perdidas durante periodos de inactividad.</p>

<h2>8. Limitacion de responsabilidad</h2>
<p>FiltroLlamadas se ofrece "tal cual". No garantizamos la exactitud de las transcripciones ni la precision de la clasificacion por IA. El servicio no sustituye la atencion humana directa. No somos responsables por danos indirectos derivados del uso del servicio.</p>

<h2>9. Cancelacion</h2>
<p>Puedes cancelar tu cuenta en cualquier momento desde la aplicacion. Al cancelar: tus datos se conservan por 90 dias por si deseas reactivar la cuenta, transcurrido ese plazo se eliminan permanentemente. El desvio de llamadas debe ser desactivado manualmente desde tu telefono usando el codigo ##002#.</p>

<h2>10. Contacto</h2>
<p>Para consultas sobre estos terminos, escribe a soporte@filtrollamadas.com. Intentaremos responder en un plazo de 48 horas habiles.</p>
"""


def _privacidad_html() -> str:
    return """
<h2>1. Informacion que recopilamos</h2>
<p>Recopilamos la informacion que proporcionas al registrarte (nombre, email, telefono), las grabaciones de audio de las llamadas que recibe tu asistente, las transcripciones generadas, y datos de uso basicos (frecuencia de uso, plan contratado). No recopilamos informacion financiera directamente; los pagos son procesados por MercadoPago.</p>

<h2>2. Como usamos tu informacion</h2>
<p>Usamos tu informacion para: operar el servicio de asistencia telefonica, generar transcripciones y resumenes de llamadas, enviar notificaciones por WhatsApp, mejorar la calidad de la IA, y comunicarte cambios en el servicio. No vendemos tu informacion personal a terceros bajo ninguna circunstancia.</p>

<h2>3. Almacenamiento y seguridad</h2>
<p>Tus datos se almacenan en servidores seguros con cifrado en transito (TLS) y en reposo. Los audios de llamadas se almacenan por un maximo de 90 dias y luego se eliminan automaticamente. Las transcripciones de texto se conservan mientras mantengas tu cuenta activa.</p>

<h2>4. Servicios de terceros</h2>
<p>Utilizamos los siguientes servicios de terceros: Twilio (telefonia), Amazon Polly (sintesis de voz), OpenAI (procesamiento de lenguaje), MercadoPago (pagos), y WhatsApp Business API (notificaciones). Cada uno de estos servicios opera bajo sus propias politicas de privacidad.</p>

<h2>5. Tus derechos</h2>
<p>Tienes derecho a: acceder a tu informacion personal, solicitar la correccion de datos inexactos, solicitar la eliminacion de tu cuenta y datos, exportar tus transcripciones, y revocar el consentimiento para el procesamiento de tus datos en cualquier momento.</p>

<h2>6. Consentimiento para grabacion</h2>
<p>Al usar FiltroLlamadas, consientes que las llamadas dirigidas a tu asistente sean grabadas y procesadas. Es tu responsabilidad cumplir con las leyes locales de grabacion de llamadas, que pueden requerir consentimiento de todas las partes involucradas.</p>

<h2>7. Cookies y seguimiento</h2>
<p>La aplicacion movil no utiliza cookies. Recopilamos datos anonimos de uso para mejorar el servicio. No realizamos seguimiento publicitario ni compartimos datos de uso con redes publicitarias.</p>

<h2>8. Menores de edad</h2>
<p>FiltroLlamadas no esta dirigido a menores de 18 anos. No recopilamos conscientemente informacion de menores. Si descubrimos que un menor ha creado una cuenta, la eliminaremos.</p>

<h2>9. Cambios en esta politica</h2>
<p>Podemos actualizar esta politica periodicamente. Te notificaremos de cambios significativos a traves de la aplicacion o por email con al menos 15 dias de anticipacion.</p>

<h2>10. Contacto</h2>
<p>Para ejercer tus derechos de privacidad o realizar consultas, escribe a privacidad@filtrollamadas.com.</p>
"""
