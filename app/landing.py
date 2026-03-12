"""Landing page pública de marketing para FiltroLlamadas.

Ruta: GET / → HTML con la página de marketing
"""
from app.core.config import settings


def render_landing_html() -> str:
    """Genera la landing page de marketing."""
    base_url = settings.BASE_URL
    planes_url = f"{base_url}/suscripcion/planes"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FiltroLlamadas — Tu asistente IA que contesta por ti</title>
    <meta name="description" content="FiltroLlamadas filtra y contesta tus llamadas con inteligencia artificial. Recibe resumenes por WhatsApp, graba tu propio saludo y deja que la IA gestione tu agenda.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --primary: #6366f1;
            --primary-light: #818cf8;
            --accent: #f59e0b;
            --green: #22c55e;
            --bg: #0f172a;
            --bg-card: #1e293b;
            --bg-card-light: #334155;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --text-secondary: #cbd5e1;
        }}
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; overflow-x: hidden; }}
        a {{ color: var(--primary-light); text-decoration: none; }}

        /* ═══ NAV ═══ */
        nav {{ position: fixed; top: 0; width: 100%; z-index: 100; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; backdrop-filter: blur(20px); background: rgba(15,23,42,0.8); border-bottom: 1px solid rgba(99,102,241,0.1); }}
        .nav-logo {{ font-size: 1.2rem; font-weight: 800; background: linear-gradient(135deg, var(--primary), var(--primary-light)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .nav-links {{ display: flex; gap: 24px; align-items: center; }}
        .nav-links a {{ color: var(--text-muted); font-size: 0.9rem; font-weight: 500; transition: color 0.2s; }}
        .nav-links a:hover {{ color: var(--text); }}
        .nav-cta {{ background: var(--primary); color: white !important; padding: 8px 20px; border-radius: 10px; font-weight: 600; font-size: 0.85rem; -webkit-text-fill-color: white; transition: opacity 0.2s; }}
        .nav-cta:hover {{ opacity: 0.85; }}

        /* ═══ HERO ═══ */
        .hero {{ text-align: center; padding: 140px 24px 80px; position: relative; }}
        .hero::before {{ content: ""; position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 600px; height: 600px; background: radial-gradient(circle, rgba(99,102,241,0.15), transparent 70%); pointer-events: none; }}
        .hero-badge {{ display: inline-block; background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3); color: var(--primary-light); padding: 6px 16px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; margin-bottom: 24px; }}
        .hero h1 {{ font-size: clamp(2.2rem, 5vw, 3.8rem); font-weight: 900; line-height: 1.1; margin-bottom: 20px; }}
        .hero h1 span {{ background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .hero-sub {{ color: var(--text-muted); font-size: clamp(1rem, 2vw, 1.2rem); max-width: 560px; margin: 0 auto 36px; line-height: 1.7; }}
        .hero-buttons {{ display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }}
        .btn {{ padding: 14px 32px; border-radius: 14px; font-weight: 700; font-size: 1rem; cursor: pointer; border: none; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px; }}
        .btn-primary {{ background: linear-gradient(135deg, var(--primary), #7c3aed); color: white; box-shadow: 0 4px 24px rgba(99,102,241,0.3); }}
        .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 8px 32px rgba(99,102,241,0.4); }}
        .btn-secondary {{ background: var(--bg-card); color: var(--text); border: 1px solid var(--bg-card-light); }}
        .btn-secondary:hover {{ background: var(--bg-card-light); }}

        /* ═══ SOCIAL PROOF ═══ */
        .social {{ text-align: center; padding: 20px 24px 60px; }}
        .social-stats {{ display: flex; justify-content: center; gap: 48px; flex-wrap: wrap; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 2rem; font-weight: 800; color: var(--primary-light); }}
        .stat-label {{ color: var(--text-muted); font-size: 0.85rem; }}

        /* ═══ HOW IT WORKS ═══ */
        .how {{ padding: 80px 24px; max-width: 900px; margin: 0 auto; }}
        .section-label {{ color: var(--primary-light); font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 2px; text-align: center; margin-bottom: 12px; }}
        .section-title {{ font-size: clamp(1.8rem, 3vw, 2.4rem); font-weight: 800; text-align: center; margin-bottom: 48px; }}
        .steps {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; }}
        .step {{ background: var(--bg-card); border-radius: 20px; padding: 32px 24px; text-align: center; border: 1px solid transparent; transition: all 0.3s; }}
        .step:hover {{ border-color: var(--primary); transform: translateY(-4px); }}
        .step-number {{ width: 48px; height: 48px; border-radius: 14px; background: linear-gradient(135deg, var(--primary), #7c3aed); color: white; font-size: 1.2rem; font-weight: 800; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; }}
        .step-icon {{ font-size: 2.5rem; margin-bottom: 16px; }}
        .step h3 {{ font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; }}
        .step p {{ color: var(--text-muted); font-size: 0.9rem; line-height: 1.5; }}

        /* ═══ FEATURES ═══ */
        .features {{ padding: 80px 24px; max-width: 1000px; margin: 0 auto; }}
        .features-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }}
        .feature {{ background: var(--bg-card); border-radius: 16px; padding: 28px 24px; border: 1px solid rgba(99,102,241,0.08); transition: border-color 0.3s; }}
        .feature:hover {{ border-color: var(--primary); }}
        .feature-icon {{ font-size: 2rem; margin-bottom: 12px; }}
        .feature h3 {{ font-size: 1.05rem; font-weight: 700; margin-bottom: 6px; }}
        .feature p {{ color: var(--text-muted); font-size: 0.88rem; line-height: 1.5; }}

        /* ═══ PLANS ═══ */
        .plans {{ padding: 80px 24px; }}
        .plans-grid {{ display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; max-width: 1000px; margin: 0 auto; }}
        .plan {{ background: var(--bg-card); border-radius: 20px; padding: 36px 28px; width: 300px; border: 1px solid var(--bg-card-light); position: relative; transition: all 0.3s; }}
        .plan:hover {{ border-color: var(--primary); transform: translateY(-4px); }}
        .plan.featured {{ border: 2px solid var(--primary); }}
        .plan.featured::before {{ content: "RECOMENDADO"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, var(--primary), #7c3aed); color: white; font-size: 0.7rem; font-weight: 700; padding: 4px 16px; border-radius: 20px; letter-spacing: 1px; }}
        .plan-name {{ font-size: 1.2rem; font-weight: 700; margin-bottom: 4px; }}
        .plan-price {{ font-size: 2.8rem; font-weight: 900; color: var(--primary-light); }}
        .plan-price span {{ font-size: 1rem; font-weight: 400; color: var(--text-muted); }}
        .plan-desc {{ color: var(--text-muted); font-size: 0.88rem; margin: 8px 0 20px; }}
        .plan-features {{ list-style: none; margin-bottom: 24px; }}
        .plan-features li {{ padding: 5px 0; font-size: 0.88rem; color: var(--text-secondary); display: flex; align-items: center; gap: 8px; }}
        .plan-features li::before {{ content: "\\2713"; color: var(--green); font-weight: 700; font-size: 0.9rem; }}
        .plan-btn {{ display: block; width: 100%; padding: 14px; border: none; border-radius: 12px; font-size: 1rem; font-weight: 600; cursor: pointer; text-align: center; transition: all 0.2s; }}
        .plan-btn.primary {{ background: linear-gradient(135deg, var(--primary), #7c3aed); color: white; }}
        .plan-btn.secondary {{ background: var(--bg-card-light); color: var(--text); }}
        .plan-btn:hover {{ opacity: 0.85; transform: scale(1.02); }}

        /* ═══ FAQ ═══ */
        .faq {{ padding: 80px 24px; max-width: 700px; margin: 0 auto; }}
        .faq-item {{ background: var(--bg-card); border-radius: 14px; padding: 20px 24px; margin-bottom: 12px; cursor: pointer; border: 1px solid transparent; transition: border-color 0.3s; }}
        .faq-item:hover {{ border-color: var(--primary); }}
        .faq-q {{ font-weight: 600; font-size: 1rem; display: flex; justify-content: space-between; align-items: center; }}
        .faq-q::after {{ content: "+"; font-size: 1.4rem; color: var(--primary-light); transition: transform 0.3s; }}
        .faq-item.open .faq-q::after {{ transform: rotate(45deg); }}
        .faq-a {{ color: var(--text-muted); font-size: 0.9rem; line-height: 1.6; max-height: 0; overflow: hidden; transition: max-height 0.3s, padding 0.3s; }}
        .faq-item.open .faq-a {{ max-height: 200px; padding-top: 12px; }}

        /* ═══ CTA FINAL ═══ */
        .cta {{ text-align: center; padding: 80px 24px; position: relative; }}
        .cta::before {{ content: ""; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 500px; height: 300px; background: radial-gradient(circle, rgba(99,102,241,0.12), transparent 70%); pointer-events: none; }}
        .cta h2 {{ font-size: clamp(1.8rem, 3vw, 2.4rem); font-weight: 800; margin-bottom: 16px; }}
        .cta p {{ color: var(--text-muted); max-width: 480px; margin: 0 auto 32px; font-size: 1.05rem; }}

        /* ═══ FOOTER ═══ */
        footer {{ text-align: center; padding: 40px 24px; border-top: 1px solid rgba(99,102,241,0.1); color: var(--text-muted); font-size: 0.8rem; }}
        footer a {{ color: var(--text-secondary); }}

        @media (max-width: 640px) {{
            .nav-links a:not(.nav-cta) {{ display: none; }}
            .social-stats {{ gap: 24px; }}
            .hero-buttons {{ flex-direction: column; align-items: center; }}
            .btn {{ width: 100%; max-width: 300px; justify-content: center; }}
        }}
    </style>
</head>
<body>
    <nav>
        <div class="nav-logo">FiltroLlamadas</div>
        <div class="nav-links">
            <a href="#como-funciona">Como funciona</a>
            <a href="#planes">Planes</a>
            <a href="#faq">FAQ</a>
            <a href="{planes_url}" class="nav-cta">Empezar gratis</a>
        </div>
    </nav>

    <!-- HERO -->
    <section class="hero">
        <div class="hero-badge">Nuevo: Agente IA que gestiona tu agenda</div>
        <h1>Tu llamada, <span>tu decision.</span><br>La IA contesta por ti.</h1>
        <p class="hero-sub">FiltroLlamadas filtra, contesta y resume tus llamadas con inteligencia artificial. Recibe un resumen por WhatsApp sin interrumpir tu dia.</p>
        <div class="hero-buttons">
            <a href="{planes_url}" class="btn btn-primary">Empezar gratis</a>
            <a href="#como-funciona" class="btn btn-secondary">Ver como funciona</a>
        </div>
    </section>

    <!-- SOCIAL PROOF -->
    <section class="social">
        <div class="social-stats">
            <div class="stat">
                <div class="stat-number">3</div>
                <div class="stat-label">Planes flexibles</div>
            </div>
            <div class="stat">
                <div class="stat-number">30s</div>
                <div class="stat-label">Setup inicial</div>
            </div>
            <div class="stat">
                <div class="stat-number">24/7</div>
                <div class="stat-label">Siempre disponible</div>
            </div>
        </div>
    </section>

    <!-- COMO FUNCIONA -->
    <section class="how" id="como-funciona">
        <div class="section-label">Como funciona</div>
        <h2 class="section-title">3 pasos y listo</h2>
        <div class="steps">
            <div class="step">
                <div class="step-icon">📱</div>
                <div class="step-number">1</div>
                <h3>Descarga la app</h3>
                <p>Registrate en segundos. Recibiras un numero de telefono exclusivo para tu asistente.</p>
            </div>
            <div class="step">
                <div class="step-icon">📞</div>
                <div class="step-number">2</div>
                <h3>Desvia tus llamadas</h3>
                <p>Configura el desvio de llamadas en tu celular hacia tu numero FiltroLlamadas.</p>
            </div>
            <div class="step">
                <div class="step-icon">💬</div>
                <div class="step-number">3</div>
                <h3>Recibe resumenes</h3>
                <p>La IA contesta, escucha y te envia un resumen por WhatsApp con nombre, motivo y prioridad.</p>
            </div>
        </div>
    </section>

    <!-- FEATURES -->
    <section class="features">
        <div class="section-label">Funcionalidades</div>
        <h2 class="section-title">Todo lo que necesitas</h2>
        <div class="features-grid">
            <div class="feature">
                <div class="feature-icon">🤖</div>
                <h3>IA que entiende</h3>
                <p>GPT-4o analiza cada llamada en tiempo real. Categoriza, prioriza y resume automaticamente.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🎙️</div>
                <h3>Tu voz, tu estilo</h3>
                <p>Graba tu propio saludo personalizado. Tus contactos escuchan tu voz, no un robot generico.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">📅</div>
                <h3>Integra tu calendario</h3>
                <p>Conecta Google Calendar u Outlook. El agente IA sabe cuando estas ocupado y actua en consecuencia.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🌙</div>
                <h3>Modo Luna</h3>
                <p>Activa el modo nocturno y todas las llamadas van al asistente. Duerme tranquilo.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">💬</div>
                <h3>Resumen WhatsApp</h3>
                <p>Recibe un mensaje estructurado con nombre del llamante, motivo, categoria y prioridad.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🔒</div>
                <h3>Privacidad total</h3>
                <p>Sin grabaciones almacenadas. La IA transcribe en tiempo real y descarta el audio.</p>
            </div>
        </div>
    </section>

    <!-- PLANES -->
    <section class="plans" id="planes">
        <div class="section-label">Planes</div>
        <h2 class="section-title">Elige tu plan</h2>
        <div class="plans-grid">
            <!-- FREE -->
            <div class="plan">
                <div class="plan-name">Free</div>
                <div class="plan-price">$0<span>/mes</span></div>
                <div class="plan-desc">Perfecto para probar el servicio</div>
                <ul class="plan-features">
                    <li>50 llamadas / mes</li>
                    <li>Voz Polly como saludo</li>
                    <li>IA escucha y transcribe</li>
                    <li>Resumen por WhatsApp</li>
                    <li>Clasificacion automatica</li>
                </ul>
                <a href="{planes_url}" class="plan-btn secondary">Empezar gratis</a>
            </div>

            <!-- PRO -->
            <div class="plan featured">
                <div class="plan-name">Pro</div>
                <div class="plan-price">$4.99<span>/mes</span></div>
                <div class="plan-desc">Tu voz grabada como contestadora</div>
                <ul class="plan-features">
                    <li>200 llamadas / mes</li>
                    <li>Tu voz para conocidos</li>
                    <li>Polly para desconocidos</li>
                    <li>Prompt personalizado</li>
                    <li>Modo Luna</li>
                    <li>Transcripcion + resumen IA</li>
                </ul>
                <a href="{planes_url}" class="plan-btn primary">Suscribirme a Pro</a>
            </div>

            <!-- PREMIUM -->
            <div class="plan">
                <div class="plan-name">Premium</div>
                <div class="plan-price">$9.99<span>/mes</span></div>
                <div class="plan-desc">Agente IA que conversa y agenda</div>
                <ul class="plan-features">
                    <li>Llamadas ilimitadas</li>
                    <li>Tu voz + IA conversa</li>
                    <li>Agente IA inteligente</li>
                    <li>Google Calendar + Outlook</li>
                    <li>Modo Luna con horario</li>
                    <li>Soporte prioritario</li>
                </ul>
                <a href="{planes_url}" class="plan-btn primary">Suscribirme a Premium</a>
            </div>
        </div>
    </section>

    <!-- FAQ -->
    <section class="faq" id="faq">
        <div class="section-label">Preguntas frecuentes</div>
        <h2 class="section-title">FAQ</h2>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Como funciona el desvio de llamadas?</div>
            <div class="faq-a">Cuando recibes una llamada que no contestas (o que desvias manualmente), tu operador la redirige al numero FiltroLlamadas. La IA contesta en tu nombre, escucha al llamante y te envia un resumen.</div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Se graban mis llamadas?</div>
            <div class="faq-a">No. FiltroLlamadas transcribe en tiempo real usando speech-to-text. El audio no se almacena. Solo guardamos la transcripcion de texto y el resumen generado por la IA.</div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Puedo cancelar en cualquier momento?</div>
            <div class="faq-a">Si, sin compromiso. Puedes cancelar tu suscripcion cuando quieras y seguiras con el plan Free, que es gratuito para siempre.</div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Funciona en mi pais?</div>
            <div class="faq-a">FiltroLlamadas funciona en cualquier pais donde Twilio tenga cobertura, que incluye la mayoria de paises de America Latina, Estados Unidos y Europa.</div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Que es el Agente IA del plan Premium?</div>
            <div class="faq-a">Es un asistente conversacional que no solo escucha sino que conversa con tus llamantes. Puede agendar reuniones, consultar tu calendario y tomar decisiones segun tus instrucciones personalizadas.</div>
        </div>
    </section>

    <!-- CTA FINAL -->
    <section class="cta">
        <h2>Deja de perder llamadas importantes</h2>
        <p>Empieza gratis hoy. Sin tarjeta de credito, sin compromisos. Configura en 30 segundos.</p>
        <a href="{planes_url}" class="btn btn-primary" style="font-size:1.1rem; padding:16px 40px;">Empezar gratis ahora</a>
    </section>

    <footer>
        <p>FiltroLlamadas &copy; 2026. Hecho con IA en Latinoamerica.</p>
        <p style="margin-top:8px;"><a href="/docs">API Docs</a> &middot; <a href="{planes_url}">Planes</a></p>
    </footer>
</body>
</html>"""
