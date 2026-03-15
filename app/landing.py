"""Landing page pública de marketing para ContestaDora (contestadora.io).

Ruta: GET / → HTML con la página de marketing
Marca: ContestaDora — personaje Dora, pulpo agente secreto corporativo.
"""
from app.core.config import settings


def render_landing_html() -> str:
    """Genera la landing page de marketing optimizada para SEO, UX y UI."""
    base_url = settings.BASE_URL
    planes_url = f"{base_url}/suscripcion/planes"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ContestaDora — Tu agente IA que filtra y contesta llamadas por ti</title>
    <meta name="description" content="ContestaDora filtra, contesta y resume tus llamadas con IA. Ahorra casi 2 horas diarias entre interrupciones y pérdida de concentración. Dora, tu agente secreto, maneja todo por ti. Prueba 7 días gratis.">
    <meta name="keywords" content="filtro de llamadas, IA llamadas, contestador inteligente, bloquear spam, asistente virtual llamadas, ContestaDora, productividad, ahorro de tiempo">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
    <link rel="canonical" href="https://contestadora.io">

    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://contestadora.io">
    <meta property="og:title" content="ContestaDora — Tu agente IA que filtra llamadas por ti">
    <meta property="og:description" content="Pierdes casi 2 horas al día por llamadas innecesarias. Dora contesta, filtra y te resume todo por WhatsApp. Desde $6.99/mes.">
    <meta property="og:site_name" content="ContestaDora">
    <meta property="og:locale" content="es_LA">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="ContestaDora — Tu agente IA que filtra llamadas">
    <meta name="twitter:description" content="Dora contesta tus llamadas, filtra el spam y te avisa por WhatsApp. 7 días gratis.">

    <!-- Schema.org JSON-LD -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "ContestaDora",
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "iOS, Android",
        "description": "Asistente IA que filtra, contesta y resume tus llamadas telefónicas automáticamente.",
        "offers": [
            {{
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
                "description": "Prueba gratuita 7 días"
            }},
            {{
                "@type": "Offer",
                "price": "6.99",
                "priceCurrency": "USD",
                "description": "Plan Pro - 300 llamadas/mes"
            }}
        ],
        "aggregateRating": {{
            "@type": "AggregateRating",
            "ratingValue": "4.8",
            "ratingCount": "1200"
        }}
    }}
    </script>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --primary: #6366f1;
            --primary-light: #818cf8;
            --primary-dark: #4f46e5;
            --accent: #f59e0b;
            --accent-light: #fbbf24;
            --green: #22c55e;
            --red: #ef4444;
            --bg: #0a0f1e;
            --bg-card: #151d2e;
            --bg-card-light: #1e293b;
            --bg-card-hover: #243044;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --text-secondary: #cbd5e1;
            --border-subtle: rgba(99,102,241,0.12);
        }}
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; overflow-x: hidden; -webkit-font-smoothing: antialiased; }}
        a {{ color: var(--primary-light); text-decoration: none; transition: color 0.2s; }}
        a:focus-visible, button:focus-visible {{ outline: 2px solid var(--primary-light); outline-offset: 2px; border-radius: 4px; }}
        img {{ max-width: 100%; height: auto; }}

        /* ═══ NAV ═══ */
        nav {{ position: fixed; top: 0; width: 100%; z-index: 100; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); background: rgba(10,15,30,0.85); border-bottom: 1px solid var(--border-subtle); }}
        .nav-logo {{ font-size: 1.2rem; font-weight: 800; background: linear-gradient(135deg, var(--primary), var(--primary-light)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 10px; }}
        .nav-logo svg {{ width: 36px; height: 36px; flex-shrink: 0; }}
        .nav-links {{ display: flex; gap: 28px; align-items: center; }}
        .nav-links a {{ color: var(--text-muted); font-size: 0.9rem; font-weight: 500; transition: color 0.2s; }}
        .nav-links a:hover {{ color: var(--text); }}
        .nav-cta {{ background: var(--primary); color: white !important; padding: 10px 24px; border-radius: 10px; font-weight: 600; font-size: 0.85rem; -webkit-text-fill-color: white; transition: all 0.2s; box-shadow: 0 2px 12px rgba(99,102,241,0.25); }}
        .nav-cta:hover {{ opacity: 0.9; transform: translateY(-1px); box-shadow: 0 4px 16px rgba(99,102,241,0.35); }}

        /* ═══ HERO ═══ */
        .hero {{ text-align: center; padding: 150px 24px 80px; position: relative; }}
        .hero::before {{ content: ""; position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 700px; height: 700px; background: radial-gradient(circle, rgba(99,102,241,0.12), transparent 70%); pointer-events: none; }}
        .hero-badge {{ display: inline-flex; align-items: center; gap: 6px; background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.25); color: var(--primary-light); padding: 8px 18px; border-radius: 24px; font-size: 0.82rem; font-weight: 600; margin-bottom: 28px; }}
        .hero h1 {{ font-size: clamp(2.4rem, 5vw, 4rem); font-weight: 900; line-height: 1.08; margin-bottom: 22px; letter-spacing: -0.02em; }}
        .hero h1 span {{ background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .hero-mascot {{ width: 180px; height: 180px; margin: 0 auto 32px; animation: float 4s ease-in-out infinite; }}
        .hero-mascot svg {{ width: 100%; height: 100%; filter: drop-shadow(0 12px 40px rgba(99,102,241,0.35)); }}
        @keyframes float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-14px); }} }}
        .hero-sub {{ color: var(--text-muted); font-size: clamp(1rem, 2vw, 1.15rem); max-width: 580px; margin: 0 auto 40px; line-height: 1.75; }}
        .hero-buttons {{ display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }}
        .btn {{ padding: 14px 32px; border-radius: 14px; font-weight: 700; font-size: 1rem; cursor: pointer; border: none; transition: all 0.25s; display: inline-flex; align-items: center; gap: 8px; text-decoration: none; }}
        .btn-primary {{ background: linear-gradient(135deg, var(--primary), #7c3aed); color: white; box-shadow: 0 4px 24px rgba(99,102,241,0.3); }}
        .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 8px 32px rgba(99,102,241,0.45); }}
        .btn-secondary {{ background: var(--bg-card); color: var(--text); border: 1px solid var(--bg-card-light); }}
        .btn-secondary:hover {{ background: var(--bg-card-light); }}
        .hero-meta {{ color: var(--text-muted); font-size: 0.85rem; margin-top: 22px; opacity: 0.7; }}
        .hero-price-highlight {{ display: inline-block; background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3); padding: 4px 12px; border-radius: 8px; color: var(--primary-light); font-weight: 600; font-size: 0.85rem; margin-top: 12px; }}

        /* ═══ SOCIAL PROOF ═══ */
        .social {{ text-align: center; padding: 20px 24px 60px; }}
        .social-stats {{ display: flex; justify-content: center; gap: 56px; flex-wrap: wrap; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 2.2rem; font-weight: 800; color: var(--primary-light); }}
        .stat-label {{ color: var(--text-muted); font-size: 0.85rem; margin-top: 2px; }}

        /* ═══ TIME COST SECTION ═══ */
        .time-cost {{ padding: 80px 24px; max-width: 1100px; margin: 0 auto; }}
        .time-cost-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-top: 40px; }}
        .time-card {{ background: var(--bg-card); border-radius: 20px; padding: 36px 28px; border: 1px solid var(--border-subtle); position: relative; overflow: hidden; }}
        .time-card::before {{ content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; }}
        .time-card.direct::before {{ background: linear-gradient(90deg, var(--red), #f97316); }}
        .time-card.indirect::before {{ background: linear-gradient(90deg, #f97316, var(--accent)); }}
        .time-card-icon {{ font-size: 2.5rem; margin-bottom: 16px; }}
        .time-card h3 {{ font-size: 1.15rem; font-weight: 700; margin-bottom: 8px; }}
        .time-card p {{ color: var(--text-muted); font-size: 0.9rem; line-height: 1.6; }}
        .time-stat {{ display: flex; align-items: baseline; gap: 6px; margin-top: 16px; }}
        .time-stat-number {{ font-size: 2.4rem; font-weight: 900; }}
        .time-stat-number.red {{ color: var(--red); }}
        .time-stat-number.orange {{ color: #f97316; }}
        .time-stat-label {{ color: var(--text-muted); font-size: 0.88rem; }}
        .time-total {{ background: linear-gradient(135deg, rgba(239,68,68,0.1), rgba(245,158,11,0.1)); border: 1px solid rgba(239,68,68,0.2); border-radius: 16px; padding: 28px; text-align: center; margin-top: 24px; }}
        .time-total h3 {{ font-size: 1.1rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; }}
        .time-total .big-number {{ font-size: 3rem; font-weight: 900; background: linear-gradient(135deg, var(--red), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .time-total p {{ color: var(--text-muted); font-size: 0.9rem; margin-top: 8px; }}
        .time-total .savings {{ display: inline-flex; align-items: center; gap: 6px; background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.25); color: var(--green); padding: 8px 16px; border-radius: 10px; font-weight: 600; font-size: 0.9rem; margin-top: 16px; }}

        /* ═══ PAIN POINTS ═══ */
        .pain {{ padding: 60px 24px 20px; max-width: 800px; margin: 0 auto; }}
        .pain-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 24px; }}
        .pain-card {{ background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15); border-radius: 16px; padding: 24px; text-align: center; transition: transform 0.2s, border-color 0.2s; }}
        .pain-card:hover {{ transform: translateY(-2px); border-color: rgba(239,68,68,0.3); }}
        .pain-card-icon {{ font-size: 2rem; margin-bottom: 10px; }}
        .pain-card p {{ color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5; }}

        /* ═══ HOW IT WORKS ═══ */
        .how {{ padding: 80px 24px; max-width: 900px; margin: 0 auto; }}
        .section-label {{ color: var(--primary-light); font-weight: 700; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 2.5px; text-align: center; margin-bottom: 12px; }}
        .section-title {{ font-size: clamp(1.8rem, 3vw, 2.4rem); font-weight: 800; text-align: center; margin-bottom: 12px; letter-spacing: -0.01em; }}
        .section-subtitle {{ color: var(--text-muted); text-align: center; font-size: 1rem; max-width: 560px; margin: 0 auto 48px; }}
        .steps {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; }}
        .step {{ background: var(--bg-card); border-radius: 20px; padding: 36px 24px; text-align: center; border: 1px solid var(--border-subtle); transition: all 0.3s; }}
        .step:hover {{ border-color: var(--primary); transform: translateY(-4px); box-shadow: 0 8px 32px rgba(99,102,241,0.12); }}
        .step-number {{ width: 48px; height: 48px; border-radius: 14px; background: linear-gradient(135deg, var(--primary), #7c3aed); color: white; font-size: 1.2rem; font-weight: 800; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; }}
        .step-icon {{ font-size: 2.5rem; margin-bottom: 16px; }}
        .step h3 {{ font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; }}
        .step p {{ color: var(--text-muted); font-size: 0.9rem; line-height: 1.6; }}

        /* ═══ FEATURES ═══ */
        .features {{ padding: 80px 24px; max-width: 1000px; margin: 0 auto; }}
        .features-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }}
        .feature {{ background: var(--bg-card); border-radius: 16px; padding: 28px 24px; border: 1px solid var(--border-subtle); transition: all 0.3s; }}
        .feature:hover {{ border-color: var(--primary); transform: translateY(-2px); }}
        .feature-icon {{ font-size: 2rem; margin-bottom: 12px; }}
        .feature h3 {{ font-size: 1.05rem; font-weight: 700; margin-bottom: 6px; }}
        .feature p {{ color: var(--text-muted); font-size: 0.88rem; line-height: 1.6; }}

        /* ═══ EXAMPLES / PREVIEW SECTION ═══ */
        .examples {{ padding: 80px 24px; max-width: 1100px; margin: 0 auto; }}
        .examples-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 28px; margin-top: 40px; }}
        .example-card {{ background: var(--bg-card); border-radius: 20px; padding: 0; overflow: hidden; border: 1px solid var(--border-subtle); transition: all 0.3s; }}
        .example-card:hover {{ border-color: var(--primary); transform: translateY(-3px); box-shadow: 0 12px 40px rgba(99,102,241,0.1); }}
        .example-card-header {{ padding: 20px 24px 12px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid var(--border-subtle); }}
        .example-card-header .dot {{ width: 8px; height: 8px; border-radius: 50%; }}
        .example-card-header .dot.green {{ background: var(--green); }}
        .example-card-header .dot.yellow {{ background: var(--accent); }}
        .example-card-header .dot.red {{ background: var(--red); }}
        .example-card-header span {{ font-size: 0.82rem; font-weight: 600; color: var(--text-muted); margin-left: 6px; }}
        .example-card-body {{ padding: 20px 24px 24px; }}

        /* WhatsApp message mockup */
        .wa-msg {{ background: #1a2e1a; border-radius: 12px; padding: 14px 16px; margin-bottom: 12px; position: relative; max-width: 95%; }}
        .wa-msg::after {{ content: ""; position: absolute; bottom: -6px; left: 16px; width: 12px; height: 12px; background: #1a2e1a; transform: rotate(45deg); }}
        .wa-msg.right {{ background: #0b3d2e; margin-left: auto; }}
        .wa-msg.right::after {{ left: auto; right: 16px; background: #0b3d2e; }}
        .wa-msg-sender {{ font-size: 0.75rem; font-weight: 700; color: var(--green); margin-bottom: 4px; }}
        .wa-msg-text {{ font-size: 0.85rem; color: var(--text); line-height: 1.55; }}
        .wa-msg-time {{ font-size: 0.7rem; color: var(--text-muted); text-align: right; margin-top: 4px; }}
        .wa-msg-emoji {{ font-size: 1.1rem; }}

        /* Weekly report mockup */
        .report-item {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(99,102,241,0.08); }}
        .report-item:last-child {{ border-bottom: none; }}
        .report-label {{ font-size: 0.88rem; color: var(--text-secondary); }}
        .report-value {{ font-size: 0.95rem; font-weight: 700; }}
        .report-value.green {{ color: var(--green); }}
        .report-value.red {{ color: var(--red); }}
        .report-value.primary {{ color: var(--primary-light); }}
        .report-bar {{ height: 6px; border-radius: 3px; margin-top: 6px; background: var(--bg-card-light); }}
        .report-bar-fill {{ height: 100%; border-radius: 3px; }}

        /* App navigation mockup */
        .app-mock {{ background: var(--bg); border-radius: 14px; border: 1px solid var(--border-subtle); overflow: hidden; }}
        .app-mock-header {{ background: var(--primary); padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; }}
        .app-mock-header span {{ font-size: 0.85rem; font-weight: 700; color: white; }}
        .app-mock-body {{ padding: 12px; }}
        .app-mock-tab-bar {{ display: flex; gap: 0; border-top: 1px solid var(--border-subtle); }}
        .app-mock-tab {{ flex: 1; padding: 10px 8px; text-align: center; font-size: 0.72rem; color: var(--text-muted); font-weight: 500; }}
        .app-mock-tab.active {{ color: var(--primary-light); font-weight: 600; }}
        .app-mock-tab .tab-icon {{ font-size: 1.1rem; display: block; margin-bottom: 2px; }}
        .call-item {{ display: flex; align-items: center; gap: 12px; padding: 10px 8px; border-radius: 10px; transition: background 0.2s; }}
        .call-item:hover {{ background: rgba(99,102,241,0.05); }}
        .call-avatar {{ width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700; color: white; flex-shrink: 0; }}
        .call-avatar.spam {{ background: rgba(239,68,68,0.2); color: var(--red); }}
        .call-avatar.important {{ background: rgba(34,197,94,0.2); color: var(--green); }}
        .call-avatar.work {{ background: rgba(99,102,241,0.2); color: var(--primary-light); }}
        .call-info {{ flex: 1; min-width: 0; }}
        .call-name {{ font-size: 0.82rem; font-weight: 600; color: var(--text); }}
        .call-desc {{ font-size: 0.72rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .call-meta {{ text-align: right; flex-shrink: 0; }}
        .call-time {{ font-size: 0.7rem; color: var(--text-muted); }}
        .call-badge {{ font-size: 0.65rem; font-weight: 600; padding: 2px 8px; border-radius: 6px; margin-top: 2px; display: inline-block; }}
        .call-badge.spam {{ background: rgba(239,68,68,0.15); color: var(--red); }}
        .call-badge.urgent {{ background: rgba(34,197,94,0.15); color: var(--green); }}
        .call-badge.normal {{ background: rgba(99,102,241,0.15); color: var(--primary-light); }}

        /* ═══ PLANS ═══ */
        .plans {{ padding: 80px 24px; }}
        .plans-grid {{ display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; max-width: 1300px; margin: 0 auto; }}
        .plan {{ background: var(--bg-card); border-radius: 20px; padding: 32px 24px; width: 280px; border: 1px solid var(--bg-card-light); position: relative; transition: all 0.3s; }}
        .plan-subtitle {{ color: var(--accent); font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
        .plan:hover {{ border-color: var(--primary); transform: translateY(-4px); box-shadow: 0 8px 32px rgba(99,102,241,0.1); }}
        .plan.featured {{ border: 2px solid var(--primary); box-shadow: 0 0 40px rgba(99,102,241,0.15); }}
        .plan.featured::before {{ content: "RECOMENDADO"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, var(--primary), #7c3aed); color: white; font-size: 0.7rem; font-weight: 700; padding: 4px 16px; border-radius: 20px; letter-spacing: 1px; }}
        .plan-name {{ font-size: 1.2rem; font-weight: 700; margin-bottom: 4px; }}
        .plan-price {{ font-size: 2.8rem; font-weight: 900; color: var(--primary-light); }}
        .plan-price span {{ font-size: 1rem; font-weight: 400; color: var(--text-muted); }}
        .plan-desc {{ color: var(--text-muted); font-size: 0.88rem; margin: 8px 0 20px; line-height: 1.5; }}
        .plan-features {{ list-style: none; margin-bottom: 24px; }}
        .plan-features li {{ padding: 5px 0; font-size: 0.88rem; color: var(--text-secondary); display: flex; align-items: center; gap: 8px; }}
        .plan-features li::before {{ content: "\\2713"; color: var(--green); font-weight: 700; font-size: 0.9rem; }}
        .plan-btn {{ display: block; width: 100%; padding: 14px; border: none; border-radius: 12px; font-size: 1rem; font-weight: 600; cursor: pointer; text-align: center; transition: all 0.25s; text-decoration: none; }}
        .plan-btn.primary {{ background: linear-gradient(135deg, var(--primary), #7c3aed); color: white; }}
        .plan-btn.secondary {{ background: var(--bg-card-light); color: var(--text); }}
        .plan-btn:hover {{ opacity: 0.9; transform: scale(1.02); }}

        /* ═══ FAQ ═══ */
        .faq {{ padding: 80px 24px; max-width: 700px; margin: 0 auto; }}
        .faq-item {{ background: var(--bg-card); border-radius: 14px; padding: 20px 24px; margin-bottom: 12px; cursor: pointer; border: 1px solid var(--border-subtle); transition: border-color 0.3s; }}
        .faq-item:hover {{ border-color: var(--primary); }}
        .faq-q {{ font-weight: 600; font-size: 1rem; display: flex; justify-content: space-between; align-items: center; }}
        .faq-q::after {{ content: "+"; font-size: 1.4rem; color: var(--primary-light); transition: transform 0.3s; flex-shrink: 0; margin-left: 12px; }}
        .faq-item.open .faq-q::after {{ transform: rotate(45deg); }}
        .faq-a {{ color: var(--text-muted); font-size: 0.9rem; line-height: 1.7; max-height: 0; overflow: hidden; transition: max-height 0.4s ease, padding 0.3s; }}
        .faq-item.open .faq-a {{ max-height: 250px; padding-top: 14px; }}

        /* ═══ CTA FINAL ═══ */
        .cta {{ text-align: center; padding: 80px 24px; position: relative; }}
        .cta::before {{ content: ""; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 600px; height: 400px; background: radial-gradient(circle, rgba(99,102,241,0.1), transparent 70%); pointer-events: none; }}
        .cta h2 {{ font-size: clamp(1.8rem, 3vw, 2.4rem); font-weight: 800; margin-bottom: 16px; }}
        .cta p {{ color: var(--text-muted); max-width: 500px; margin: 0 auto 32px; font-size: 1.05rem; line-height: 1.7; }}

        /* ═══ FOOTER ═══ */
        footer {{ text-align: center; padding: 40px 24px; border-top: 1px solid var(--border-subtle); color: var(--text-muted); font-size: 0.8rem; }}
        footer a {{ color: var(--text-secondary); }}

        /* ═══ TABLE ═══ */
        .compare-table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
        .compare-table th {{ padding: 12px 8px; font-weight: 700; }}
        .compare-table td {{ padding: 10px 8px; text-align: center; }}
        .compare-table thead tr {{ border-bottom: 2px solid var(--primary); }}
        .compare-table tbody tr {{ border-bottom: 1px solid #1e293b; }}
        .compare-table tbody tr:hover {{ background: rgba(99,102,241,0.03); }}

        /* ═══ RESPONSIVE ═══ */
        @media (max-width: 768px) {{
            .time-cost-grid {{ grid-template-columns: 1fr; }}
            .examples-grid {{ grid-template-columns: 1fr; }}
        }}
        @media (max-width: 640px) {{
            .nav-links a:not(.nav-cta) {{ display: none; }}
            .social-stats {{ gap: 24px; }}
            .hero-buttons {{ flex-direction: column; align-items: center; }}
            .btn {{ width: 100%; max-width: 300px; justify-content: center; }}
            .plans-grid {{ flex-direction: column; align-items: center; }}
            .plan {{ width: 100%; max-width: 340px; }}
        }}
    </style>
</head>
<body>
    <!-- ═══ NAV ═══ -->
    <nav role="navigation" aria-label="Navegacion principal">
        <div class="nav-logo">
            <!-- Dora Agente Secreto Corporativo -->
            <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" aria-label="Logo ContestaDora">
              <defs>
                <radialGradient id="nb" cx="50%" cy="40%" r="55%"><stop offset="0%" stop-color="#7B73FF"/><stop offset="100%" stop-color="#4A42CC"/></radialGradient>
                <linearGradient id="nt" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#5B53DD"/><stop offset="100%" stop-color="#3A32AA"/></linearGradient>
              </defs>
              <!-- Tentaculos corporativos -->
              <path d="M62,128 Q50,150 52,170 Q54,180 62,175 Q67,165 68,145" fill="none" stroke="url(#nt)" stroke-width="7" stroke-linecap="round"/>
              <path d="M78,132 Q70,155 73,175 Q77,183 82,175 Q85,165 83,145" fill="none" stroke="url(#nt)" stroke-width="6.5" stroke-linecap="round"/>
              <path d="M115,132 Q123,155 120,175 Q116,183 111,175 Q108,165 110,145" fill="none" stroke="url(#nt)" stroke-width="6.5" stroke-linecap="round"/>
              <path d="M131,128 Q143,150 141,170 Q139,180 131,175 Q126,165 125,145" fill="none" stroke="url(#nt)" stroke-width="7" stroke-linecap="round"/>
              <!-- Telefonos en tentaculos -->
              <g transform="translate(48,168) rotate(-15)"><rect x="-5" y="-9" width="10" height="18" rx="2" fill="#1A1A2E" stroke="#00D9FF" stroke-width="1"/><circle cx="0" cy="6" r="1.5" fill="#00D9FF"/></g>
              <g transform="translate(75,176) rotate(5)"><rect x="-5" y="-9" width="10" height="18" rx="2" fill="#1A1A2E" stroke="#00E676" stroke-width="1"/><circle cx="0" cy="6" r="1.5" fill="#00E676"/></g>
              <g transform="translate(118,176) rotate(-5)"><rect x="-5" y="-9" width="10" height="18" rx="2" fill="#1A1A2E" stroke="#FF9100" stroke-width="1"/><circle cx="0" cy="6" r="1.5" fill="#FF9100"/></g>
              <g transform="translate(145,168) rotate(15)"><rect x="-5" y="-9" width="10" height="18" rx="2" fill="#1A1A2E" stroke="#6C63FF" stroke-width="1"/><circle cx="0" cy="6" r="1.5" fill="#6C63FF"/></g>
              <!-- Cabeza -->
              <ellipse cx="96" cy="92" rx="44" ry="42" fill="url(#nb)"/>
              <!-- Headphones negros (ENCIMA de la cabeza) -->
              <path d="M52,92 Q52,55 96,48 Q140,55 140,92" fill="none" stroke="#1a1a2e" stroke-width="6" stroke-linecap="round"/>
              <!-- Almohadillas -->
              <rect x="44" y="82" width="14" height="24" rx="6" fill="#1a1a2e"/><rect x="46" y="85" width="10" height="18" rx="4" fill="#2a2a3e"/>
              <rect x="134" y="82" width="14" height="24" rx="6" fill="#1a1a2e"/><rect x="136" y="85" width="10" height="18" rx="4" fill="#2a2a3e"/>
              <!-- Anteojos de sol clasicos (wayfarer, ENCIMA de headphones) -->
              <rect x="62" y="80" rx="5" ry="5" width="28" height="22" fill="#0d0d1a" stroke="#1a1a2e" stroke-width="2"/>
              <rect x="102" y="80" rx="5" ry="5" width="28" height="22" fill="#0d0d1a" stroke="#1a1a2e" stroke-width="2"/>
              <!-- Puente grueso -->
              <path d="M90,89 L102,89" stroke="#1a1a2e" stroke-width="2.5" stroke-linecap="round"/>
              <!-- Patillas -->
              <path d="M62,86 Q55,84 50,88" fill="none" stroke="#1a1a2e" stroke-width="2.5" stroke-linecap="round"/>
              <path d="M130,86 Q137,84 142,88" fill="none" stroke="#1a1a2e" stroke-width="2.5" stroke-linecap="round"/>
              <!-- Reflejo sutil en lentes -->
              <line x1="67" y1="84" x2="72" y2="87" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" stroke-linecap="round"/>
              <line x1="107" y1="84" x2="112" y2="87" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" stroke-linecap="round"/>
              <!-- Boca seria (linea recta con leve curva) -->
              <path d="M86,110 Q96,113 106,110" fill="none" stroke="#1A1A2E" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <span><span style="font-weight:300;">Contesta</span><span style="font-weight:800;">Dora</span></span>
        </div>
        <div class="nav-links">
            <a href="#tiempo-perdido">El problema</a>
            <a href="#como-funciona">Como funciona</a>
            <a href="#ejemplos">Ejemplos</a>
            <a href="#planes">Planes</a>
            <a href="#faq">FAQ</a>
            <a href="{planes_url}" class="nav-cta">Probar 7 dias gratis</a>
        </div>
    </nav>

    <!-- ═══ HERO ═══ -->
    <section class="hero">
        <div class="hero-mascot">
            <!-- Dora Hero: Agente secreto corporativo -->
            <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dora, agente secreto de ContestaDora">
              <defs>
                <radialGradient id="hb" cx="50%" cy="40%" r="55%"><stop offset="0%" stop-color="#7B73FF"/><stop offset="100%" stop-color="#4A42CC"/></radialGradient>
                <radialGradient id="hh" cx="35%" cy="30%" r="40%"><stop offset="0%" stop-color="#9B93FF" stop-opacity="0.5"/><stop offset="100%" stop-color="#4A42CC" stop-opacity="0"/></radialGradient>
                <linearGradient id="ht" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#5B53DD"/><stop offset="100%" stop-color="#3A32AA"/></linearGradient>
              </defs>
              <!-- Tentaculos corporativos -->
              <path d="M140,235 Q110,265 90,305 Q78,335 95,345 Q108,350 112,330 Q118,310 130,285" fill="none" stroke="url(#ht)" stroke-width="14" stroke-linecap="round"/>
              <path d="M155,240 Q130,275 118,320 Q112,345 130,352 Q142,355 140,335 Q138,310 150,280" fill="none" stroke="url(#ht)" stroke-width="13" stroke-linecap="round"/>
              <path d="M175,250 Q165,285 158,330 Q155,350 170,355 Q182,355 178,335 Q175,310 180,280" fill="none" stroke="url(#ht)" stroke-width="12" stroke-linecap="round"/>
              <path d="M220,250 Q230,285 237,330 Q240,350 225,355 Q213,355 217,335 Q220,310 215,280" fill="none" stroke="url(#ht)" stroke-width="12" stroke-linecap="round"/>
              <path d="M240,240 Q265,275 277,320 Q283,345 265,352 Q253,355 255,335 Q257,310 245,280" fill="none" stroke="url(#ht)" stroke-width="13" stroke-linecap="round"/>
              <path d="M255,235 Q285,265 305,305 Q317,335 300,345 Q287,350 283,330 Q277,310 265,285" fill="none" stroke="url(#ht)" stroke-width="14" stroke-linecap="round"/>
              <!-- Telefonos en tentaculos (4) -->
              <g transform="translate(82,342) rotate(-20)"><rect x="-10" y="-16" width="20" height="32" rx="4" fill="#1A1A2E" stroke="#00D9FF" stroke-width="1.5"/><rect x="-7" y="-12" width="14" height="20" rx="1" fill="#0a1628"/><circle cx="0" cy="12" r="2.5" fill="#00D9FF"/></g>
              <g transform="translate(135,352) rotate(5)"><rect x="-10" y="-16" width="20" height="32" rx="4" fill="#1A1A2E" stroke="#00E676" stroke-width="1.5"/><rect x="-7" y="-12" width="14" height="20" rx="1" fill="#0a1628"/><circle cx="0" cy="12" r="2.5" fill="#00E676"/></g>
              <g transform="translate(260,352) rotate(-5)"><rect x="-10" y="-16" width="20" height="32" rx="4" fill="#1A1A2E" stroke="#FF9100" stroke-width="1.5"/><rect x="-7" y="-12" width="14" height="20" rx="1" fill="#0a1628"/><circle cx="0" cy="12" r="2.5" fill="#FF9100"/></g>
              <g transform="translate(312,342) rotate(20)"><rect x="-10" y="-16" width="20" height="32" rx="4" fill="#1A1A2E" stroke="#6C63FF" stroke-width="1.5"/><rect x="-7" y="-12" width="14" height="20" rx="1" fill="#0a1628"/><circle cx="0" cy="12" r="2.5" fill="#6C63FF"/></g>
              <!-- Cabeza principal -->
              <ellipse cx="195" cy="185" rx="88" ry="80" fill="url(#hb)"/><ellipse cx="195" cy="185" rx="88" ry="80" fill="url(#hh)"/>
              <!-- Headphones negros (ENCIMA de la cabeza) -->
              <path d="M108,185 Q108,115 195,105 Q282,115 282,185" fill="none" stroke="#1a1a2e" stroke-width="10" stroke-linecap="round"/>
              <!-- Almohadillas grandes -->
              <rect x="94" y="172" width="24" height="40" rx="10" fill="#1a1a2e"/>
              <rect x="98" y="177" width="16" height="30" rx="6" fill="#2a2a3e"/>
              <rect x="272" y="172" width="24" height="40" rx="10" fill="#1a1a2e"/>
              <rect x="276" y="177" width="16" height="30" rx="6" fill="#2a2a3e"/>
              <!-- Anteojos de sol clasicos (wayfarer, ENCIMA de headphones) -->
              <rect x="133" y="168" rx="8" ry="8" width="52" height="38" fill="#0d0d1a" stroke="#1a1a2e" stroke-width="3"/>
              <rect x="205" y="168" rx="8" ry="8" width="52" height="38" fill="#0d0d1a" stroke="#1a1a2e" stroke-width="3"/>
              <!-- Puente grueso -->
              <path d="M185,184 L205,184" stroke="#1a1a2e" stroke-width="4" stroke-linecap="round"/>
              <!-- Patillas gruesas -->
              <path d="M133,180 Q118,176 108,182" fill="none" stroke="#1a1a2e" stroke-width="4" stroke-linecap="round"/>
              <path d="M257,180 Q272,176 282,182" fill="none" stroke="#1a1a2e" stroke-width="4" stroke-linecap="round"/>
              <!-- Reflejo sutil en lentes -->
              <line x1="140" y1="174" x2="150" y2="180" stroke="rgba(255,255,255,0.12)" stroke-width="2.5" stroke-linecap="round"/>
              <line x1="212" y1="174" x2="222" y2="180" stroke="rgba(255,255,255,0.12)" stroke-width="2.5" stroke-linecap="round"/>
              <!-- Boca seria confiada -->
              <path d="M178,220 Q195,228 212,220" fill="none" stroke="#1A1A2E" stroke-width="3.5" stroke-linecap="round"/>
            </svg>
        </div>
        <div class="hero-badge">Tu agente secreto contra las llamadas innecesarias</div>
        <h1>Deja de perder tiempo<br><span>en llamadas innecesarias.</span></h1>
        <p class="hero-sub">Spam, vendedores, llamadas en reuniones, fuera de horario, numeros desconocidos que interrumpen tu concentracion. Dora contesta por ti, filtra lo importante y te avisa por WhatsApp. Tu decides si devolver la llamada.</p>
        <div class="hero-buttons">
            <a href="{planes_url}" class="btn btn-primary">Recupera tu tranquilidad</a>
            <a href="#como-funciona" class="btn btn-secondary">Ver como funciona</a>
        </div>
        <p class="hero-meta">Activar toma 30 segundos. Desactivar tambien. Sin contratos.</p>
    </section>

    <!-- ═══ PAIN POINTS ═══ -->
    <section class="pain" aria-label="Problemas comunes">
        <div class="section-label" style="color: #ef4444;">Te suena familiar?</div>
        <div class="pain-grid">
            <div class="pain-card">
                <div class="pain-card-icon">😤</div>
                <p>Otra llamada de spam que te saco de lo que estabas haciendo</p>
            </div>
            <div class="pain-card">
                <div class="pain-card-icon">🔇</div>
                <p>Llamadas en reuniones, en la noche, o cuando necesitas concentrarte</p>
            </div>
            <div class="pain-card">
                <div class="pain-card-icon">🤷</div>
                <p>Numero desconocido: era importante o era spam? Nunca lo sabras</p>
            </div>
        </div>
    </section>

    <!-- ═══ SOCIAL PROOF ═══ -->
    <section class="social" aria-label="Estadisticas">
        <div class="social-stats">
            <div class="stat">
                <div class="stat-number">~31</div>
                <div class="stat-label">Llamadas spam al mes</div>
            </div>
            <div class="stat">
                <div class="stat-number">30s</div>
                <div class="stat-label">Para activar Dora</div>
            </div>
            <div class="stat">
                <div class="stat-number">24/7</div>
                <div class="stat-label">Dora nunca descansa</div>
            </div>
        </div>
    </section>

    <!-- ═══ LA FALSA SOLUCION ═══ -->
    <section style="padding: 60px 24px; max-width: 850px; margin: 0 auto;">
        <div class="section-label" style="color: var(--accent);">Y si simplemente bloqueo todo?</div>
        <h2 class="section-title" style="margin-bottom: 16px;">Bloquear llamadas no es la solucion</h2>
        <p class="section-subtitle" style="margin-bottom: 36px;">La solucion obvia parece ser silenciar o bloquear numeros desconocidos. Pero al hacerlo, estas pagando un precio mucho mas alto de lo que crees:</p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px;">
            <div style="background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.18); border-radius: 16px; padding: 24px; text-align: center; transition: transform 0.2s;">
                <div style="font-size: 2rem; margin-bottom: 10px;">💰</div>
                <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 6px; color: var(--text);">Oportunidades perdidas</h4>
                <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5;">Ese cliente nuevo, esa oferta de trabajo, ese negocio que te llamaba de un numero que no conocias. Bloqueado.</p>
            </div>
            <div style="background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.18); border-radius: 16px; padding: 24px; text-align: center; transition: transform 0.2s;">
                <div style="font-size: 2rem; margin-bottom: 10px;">🚨</div>
                <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 6px; color: var(--text);">Emergencias ignoradas</h4>
                <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5;">El colegio de tu hijo, la clinica, un familiar desde otro numero. Te llamaron y nunca lo supiste.</p>
            </div>
            <div style="background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.18); border-radius: 16px; padding: 24px; text-align: center; transition: transform 0.2s;">
                <div style="font-size: 2rem; margin-bottom: 10px;">📋</div>
                <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 6px; color: var(--text);">Tramites estancados</h4>
                <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5;">El banco confirmando tu credito, la notaria con tus documentos, el courier con tu paquete. Todo frenado.</p>
            </div>
            <div style="background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.18); border-radius: 16px; padding: 24px; text-align: center; transition: transform 0.2s;">
                <div style="font-size: 2rem; margin-bottom: 10px;">🏥</div>
                <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 6px; color: var(--text);">Horas medicas perdidas</h4>
                <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5;">Esa hora que te costo semanas conseguir y la clinica te llamaba para confirmar. No contestaste. La perdiste.</p>
            </div>
        </div>

        <div style="text-align: center; margin-top: 32px; background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2); border-radius: 14px; padding: 24px;">
            <p style="color: var(--text); font-size: 1.05rem; font-weight: 600; margin: 0 0 8px;">La solucion no es bloquear. Es <span style="color: var(--primary-light);">filtrar inteligentemente.</span></p>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin: 0;">Dora contesta TODAS las llamadas, identifica quien es y por que llama, y te avisa solo lo que importa. Nada se pierde, nada te interrumpe.</p>
        </div>
    </section>

    <!-- ═══ TIEMPO PERDIDO EN LLAMADAS ═══ -->
    <section class="time-cost" id="tiempo-perdido" aria-label="Costo real de las llamadas">
        <div class="section-label" style="color: var(--red);">El problema real</div>
        <h2 class="section-title">Cuanto tiempo estas perdiendo en llamadas?</h2>
        <p class="section-subtitle">Una llamada no solo dura lo que dura. Cada interrupcion destruye tu estado de flow y tu cerebro tarda <strong style="color:var(--accent);">23 minutos</strong> en recuperar la concentracion. Busca tu perfil:</p>

        <!-- EXPLICACION DE LA FORMULA -->
        <div style="background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 16px; padding: 24px; max-width: 700px; margin: 0 auto 36px; text-align: center;">
            <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.7; margin: 0;">
                <strong style="color: var(--text);">Como calculamos el costo real?</strong><br>
                <span style="color:var(--red);">Tiempo directo</span> (minutos en la llamada) + <span style="color:var(--accent);">Tiempo indirecto</span> (interrupciones x 23 min para recuperar flow)<br>
                <span style="color:var(--text-muted); font-size: 0.82rem;">Fuente: Investigadores de UC Irvine — "context switching cost"</span>
            </p>
        </div>

        <!-- 3 PERFILES -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">

            <!-- ESTUDIANTE -->
            <div class="time-card" style="border-top: 3px solid var(--primary-light);">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                    <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(99,102,241,0.15); display: flex; align-items: center; justify-content: center; font-size: 1.3rem;">📚</div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.1rem;">Estudiante</h3>
                        <span style="color: var(--primary-light); font-size: 0.78rem; font-weight: 600;">~3 llamadas no deseadas/dia</span>
                    </div>
                </div>
                <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5; margin-bottom: 14px;">Estas en clases, estudiando o haciendo un trabajo. Suena el telefono: spam, vendedor, encuesta. Contestas, pierdes el hilo, y te cuesta volver a concentrarte.</p>
                <div style="background: rgba(239,68,68,0.06); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: var(--text-muted); font-size: 0.82rem;">Tiempo directo</span>
                        <span style="color: var(--red); font-weight: 700; font-size: 0.9rem;">~10 min</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: var(--text-muted); font-size: 0.82rem;">Flow perdido (3 x 23 min)</span>
                        <span style="color: var(--accent); font-weight: 700; font-size: 0.9rem;">~69 min</span>
                    </div>
                </div>
                <div style="text-align: center; padding: 16px 0 8px;">
                    <div style="font-size: 2.8rem; font-weight: 900; color: var(--red); line-height: 1;">~1h 19min</div>
                    <div style="color: var(--text-muted); font-size: 0.82rem; margin-top: 4px;">perdidos cada dia</div>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-subtle);">
                    <div style="text-align: center;">
                        <div style="font-size: 1.1rem; font-weight: 800; color: var(--red);">~26h</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">/mes</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.1rem; font-weight: 800; color: var(--red);">~316h</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">/ano</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.1rem; font-weight: 800; color: var(--red);">13 dias</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">laborales/ano</div>
                    </div>
                </div>
                <a href="{planes_url}" style="display: block; text-align: center; margin-top: 14px; background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.25); color: var(--primary-light); padding: 10px; border-radius: 10px; font-weight: 600; font-size: 0.88rem; text-decoration: none;">Plan Estudiante &middot; $4.99/mes</a>
            </div>

            <!-- ADULTO / PRO -->
            <div class="time-card" style="border-top: 3px solid var(--red); box-shadow: 0 0 40px rgba(239,68,68,0.08);">
                <div style="position: absolute; top: 12px; right: 12px; background: var(--red); color: white; font-size: 0.65rem; font-weight: 700; padding: 3px 10px; border-radius: 6px; letter-spacing: 0.5px;">MAS COMUN</div>
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                    <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(239,68,68,0.15); display: flex; align-items: center; justify-content: center; font-size: 1.3rem;">💼</div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.1rem;">Adulto / Profesional</h3>
                        <span style="color: var(--red); font-size: 0.78rem; font-weight: 600;">~5 llamadas no deseadas/dia</span>
                    </div>
                </div>
                <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5; margin-bottom: 14px;">Trabajas, tienes reuniones, deadlines. Te llaman vendedores, bancos, encuestas, numeros desconocidos. Cada llamada te saca del flow y pierdes el doble en volver a enfocarte.</p>
                <div style="background: rgba(239,68,68,0.06); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: var(--text-muted); font-size: 0.82rem;">Tiempo directo</span>
                        <span style="color: var(--red); font-weight: 700; font-size: 0.9rem;">~17 min</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: var(--text-muted); font-size: 0.82rem;">Flow perdido (5 x 23 min)</span>
                        <span style="color: var(--accent); font-weight: 700; font-size: 0.9rem;">~115 min</span>
                    </div>
                </div>
                <div style="text-align: center; padding: 16px 0 8px;">
                    <div style="font-size: 3.2rem; font-weight: 900; color: var(--red); line-height: 1;">~2h 12min</div>
                    <div style="color: var(--text-muted); font-size: 0.82rem; margin-top: 4px;">perdidos cada dia</div>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-subtle);">
                    <div style="text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: 800; color: var(--red);">~44h</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">/mes</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: 800; color: var(--red);">~528h</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">/ano</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: 800; color: var(--red);">22 dias</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">laborales/ano</div>
                    </div>
                </div>
                <p style="text-align: center; color: var(--red); font-size: 0.82rem; font-weight: 600; margin-top: 8px;">Eso es un mes entero de trabajo perdido al ano.</p>
                <a href="{planes_url}" style="display: block; text-align: center; margin-top: 10px; background: linear-gradient(135deg, var(--primary), #7c3aed); color: white; padding: 12px; border-radius: 10px; font-weight: 700; font-size: 0.95rem; text-decoration: none; box-shadow: 0 4px 16px rgba(99,102,241,0.3);">Plan Pro &middot; $6.99/mes</a>
            </div>

            <!-- EJECUTIVO -->
            <div class="time-card" style="border-top: 3px solid var(--accent);">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                    <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(245,158,11,0.15); display: flex; align-items: center; justify-content: center; font-size: 1.3rem;">🏢</div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.1rem;">Ejecutivo / Emprendedor</h3>
                        <span style="color: var(--accent); font-size: 0.78rem; font-weight: 600;">~10 llamadas no deseadas/dia</span>
                    </div>
                </div>
                <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5; margin-bottom: 14px;">Manejas equipo, clientes, proveedores. Tu telefono no para. Entre llamadas de ventas, bancos, tramites y gente que "solo quiere 5 minutitos", no logras hacer nada productivo.</p>
                <div style="background: rgba(239,68,68,0.06); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: var(--text-muted); font-size: 0.82rem;">Tiempo directo</span>
                        <span style="color: var(--red); font-weight: 700; font-size: 0.9rem;">~35 min</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: var(--text-muted); font-size: 0.82rem;">Flow perdido (10 x 23 min)</span>
                        <span style="color: var(--accent); font-weight: 700; font-size: 0.9rem;">~230 min</span>
                    </div>
                </div>
                <div style="text-align: center; padding: 16px 0 8px;">
                    <div style="font-size: 2.8rem; font-weight: 900; color: var(--red); line-height: 1;">~4h 25min</div>
                    <div style="color: var(--text-muted); font-size: 0.82rem; margin-top: 4px;">perdidos cada dia</div>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-subtle);">
                    <div style="text-align: center;">
                        <div style="font-size: 1.1rem; font-weight: 800; color: var(--red);">~88h</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">/mes</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.1rem; font-weight: 800; color: var(--red);">~1,056h</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">/ano</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.1rem; font-weight: 800; color: var(--red);">44 dias</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">laborales/ano</div>
                    </div>
                </div>
                <p style="text-align: center; color: var(--red); font-size: 0.82rem; font-weight: 600; margin-top: 8px;">Media jornada laboral perdida CADA DIA.</p>
                <a href="{planes_url}" style="display: block; text-align: center; margin-top: 10px; background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.3); color: var(--accent); padding: 10px; border-radius: 10px; font-weight: 600; font-size: 0.88rem; text-decoration: none;">Plan Ejecutivo &middot; $9.99/mes</a>
            </div>
        </div>

        <!-- RESUMEN FINAL DE IMPACTO -->
        <div class="time-total" style="margin-top: 36px; padding: 32px 28px;">
            <p style="color: var(--text-secondary); font-size: 1rem; margin: 0 auto 16px; max-width: 650px;">No importa cual sea tu perfil: estas perdiendo entre <strong style="color:var(--red);">1 y 4 horas cada dia</strong> por llamadas que no necesitabas contestar. Eso incluye el tiempo directo <em>y el tiempo invisible</em> que pierdes tratando de volver a concentrarte.</p>
            <div class="savings" style="font-size: 1.05rem; padding: 14px 28px;">&#10003; Dora recupera ese tiempo por ti</div>
        </div>
    </section>

    <!-- ═══ COMO FUNCIONA ═══ -->
    <section class="how" id="como-funciona">
        <div class="section-label">Como funciona</div>
        <h2 class="section-title">3 pasos y listo</h2>
        <p class="section-subtitle">Configurar ContestaDora toma menos de un minuto. Sin cambiar de numero, sin apps complicadas.</p>
        <div class="steps">
            <div class="step">
                <div class="step-icon">📱</div>
                <div class="step-number">1</div>
                <h3>Descarga la app</h3>
                <p>Registrate en segundos. Dora te asigna un numero de telefono exclusivo para empezar.</p>
            </div>
            <div class="step">
                <div class="step-icon">📞</div>
                <div class="step-number">2</div>
                <h3>Desvia tus llamadas</h3>
                <p>Configura el desvio de llamadas hacia tu numero ContestaDora. Dora toma el control.</p>
            </div>
            <div class="step">
                <div class="step-icon">💬</div>
                <div class="step-number">3</div>
                <h3>Dora te avisa</h3>
                <p>Dora contesta, escucha y te envia un resumen por WhatsApp con nombre, motivo y prioridad.</p>
            </div>
        </div>
    </section>

    <!-- ═══ FEATURES ═══ -->
    <section class="features" aria-label="Funcionalidades">
        <div class="section-label">Funcionalidades</div>
        <h2 class="section-title">Todo lo que necesitas</h2>
        <p class="section-subtitle">Dora tiene 8 tentaculos, y cada uno cumple una funcion. Por $6.99/mes tienes acceso a casi todos.</p>
        <div class="features-grid">
            <div class="feature">
                <div class="feature-icon">🕶️</div>
                <h3>Dora la FiltraDora</h3>
                <p>Como agente secreto, Dora analiza cada llamada en tiempo real. Categoriza, prioriza y resume automaticamente.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🎙️</div>
                <h3>Dora la GrabaDora</h3>
                <p>Graba tu propio saludo y Dora lo usa para contestar. Tus contactos escuchan tu voz, no un robot generico.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">📅</div>
                <h3>Dora la AgendaDora</h3>
                <p>Conecta Google Calendar u Outlook. Dora sabe cuando estas ocupado y agenda reuniones por ti.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🌙</div>
                <h3>Dora la GuardaDora</h3>
                <p>Activa el modo nocturno y Dora protege tu descanso. Todas las llamadas pasan por ella. Duerme tranquilo.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">💬</div>
                <h3>Dora la AvisaDora</h3>
                <p>Recibe un resumen por WhatsApp con nombre del llamante, motivo, categoria y prioridad. Nada se le escapa.</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🔒</div>
                <h3>Privacidad total</h3>
                <p>Dora transcribe en tiempo real y descarta el audio. Sin grabaciones almacenadas. Tu agente de confianza.</p>
            </div>
        </div>
    </section>

    <!-- ═══ EJEMPLOS DE MENSAJES Y APP ═══ -->
    <section class="examples" id="ejemplos" aria-label="Ejemplos de uso">
        <div class="section-label">Asi se ve</div>
        <h2 class="section-title">Lo que vas a recibir de Dora</h2>
        <p class="section-subtitle">Resumenes instantaneos, reportes semanales de ahorro, y una app donde ves todo de un vistazo.</p>

        <div class="examples-grid">
            <!-- EJEMPLO 1: Resumen WhatsApp instantaneo -->
            <div class="example-card">
                <div class="example-card-header">
                    <div class="dot green"></div>
                    <div class="dot yellow"></div>
                    <div class="dot red"></div>
                    <span>WhatsApp &mdash; Resumen instantaneo</span>
                </div>
                <div class="example-card-body">
                    <div class="wa-msg">
                        <div class="wa-msg-sender">🕶️ Dora &middot; ContestaDora</div>
                        <div class="wa-msg-text">
                            <strong>📞 Llamada filtrada</strong><br><br>
                            <strong>De:</strong> +56 9 8765 4321<br>
                            <strong>Nombre:</strong> Carlos Mendez<br>
                            <strong>Motivo:</strong> Quiere agendar reunion para el viernes para revisar contrato.<br>
                            <strong>Categoria:</strong> 🟢 Trabajo<br>
                            <strong>Prioridad:</strong> Alta<br><br>
                            <em>"Hola, soy Carlos de Inversiones del Sur. Te llamo porque quiero que revisemos el contrato el viernes. Porfavor devuelveme cuando puedas."</em>
                        </div>
                        <div class="wa-msg-time">14:32 ✓✓</div>
                    </div>
                    <div class="wa-msg" style="margin-top: 16px;">
                        <div class="wa-msg-sender">🕶️ Dora &middot; ContestaDora</div>
                        <div class="wa-msg-text">
                            <strong>📞 Llamada filtrada</strong><br><br>
                            <strong>De:</strong> +56 2 2345 6789<br>
                            <strong>Nombre:</strong> Desconocido<br>
                            <strong>Motivo:</strong> Ofrece plan de internet fibra optica.<br>
                            <strong>Categoria:</strong> 🔴 Spam/Ventas<br>
                            <strong>Prioridad:</strong> Baja
                        </div>
                        <div class="wa-msg-time">15:07 ✓✓</div>
                    </div>
                </div>
            </div>

            <!-- EJEMPLO 2: Reporte semanal de ahorro -->
            <div class="example-card">
                <div class="example-card-header">
                    <div class="dot green"></div>
                    <div class="dot yellow"></div>
                    <div class="dot red"></div>
                    <span>WhatsApp &mdash; Reporte semanal</span>
                </div>
                <div class="example-card-body">
                    <div class="wa-msg">
                        <div class="wa-msg-sender">🕶️ Dora &middot; Reporte semanal</div>
                        <div class="wa-msg-text">
                            <strong>📊 Tu semana con Dora</strong><br>
                            <span style="font-size:0.78rem;color:var(--text-muted);">Lun 10 - Dom 16 Marzo 2026</span><br><br>
                            <strong>Llamadas filtradas:</strong> 34<br>
                            <strong>Spam bloqueado:</strong> 18 (53%)<br>
                            <strong>Importantes:</strong> 9 que te avisamos<br>
                            <strong>Agendadas por Dora:</strong> 2 reuniones<br><br>
                            <span style="color:var(--green);">⏱️ <strong>Tiempo directo ahorrado:</strong> 1h 38min</span><br>
                            <span style="color:var(--accent);">🧠 <strong>Tiempo indirecto (flow):</strong> ~10h 44min</span><br><br>
                            <strong style="color:var(--primary-light);">Total ahorrado: ~12h 22min esta semana</strong><br><br>
                            <span style="font-size:0.8rem;">💡 Dato: Bloqueaste un 12% mas de spam que la semana pasada. Tu productividad se nota.</span>
                        </div>
                        <div class="wa-msg-time">Dom 09:00 ✓✓</div>
                    </div>
                </div>
            </div>

            <!-- EJEMPLO 3: Navegacion en la app -->
            <div class="example-card">
                <div class="example-card-header">
                    <div class="dot green"></div>
                    <div class="dot yellow"></div>
                    <div class="dot red"></div>
                    <span>ContestaDora App &mdash; Vista principal</span>
                </div>
                <div class="example-card-body">
                    <div class="app-mock">
                        <div class="app-mock-header">
                            <span>🕶️ ContestaDora</span>
                            <span style="font-size:0.75rem;opacity:0.8;">Hoy &middot; 5 filtradas</span>
                        </div>
                        <div class="app-mock-body">
                            <div class="call-item">
                                <div class="call-avatar spam">🔴</div>
                                <div class="call-info">
                                    <div class="call-name">+56 2 2345 6789</div>
                                    <div class="call-desc">Venta de plan de internet fibra</div>
                                </div>
                                <div class="call-meta">
                                    <div class="call-time">15:07</div>
                                    <div class="call-badge spam">Spam</div>
                                </div>
                            </div>
                            <div class="call-item">
                                <div class="call-avatar important">🟢</div>
                                <div class="call-info">
                                    <div class="call-name">Carlos Mendez</div>
                                    <div class="call-desc">Reunion viernes - revisar contrato</div>
                                </div>
                                <div class="call-meta">
                                    <div class="call-time">14:32</div>
                                    <div class="call-badge urgent">Urgente</div>
                                </div>
                            </div>
                            <div class="call-item">
                                <div class="call-avatar spam">🔴</div>
                                <div class="call-info">
                                    <div class="call-name">Numero oculto</div>
                                    <div class="call-desc">Encuesta telefonica automatizada</div>
                                </div>
                                <div class="call-meta">
                                    <div class="call-time">12:45</div>
                                    <div class="call-badge spam">Spam</div>
                                </div>
                            </div>
                            <div class="call-item">
                                <div class="call-avatar work">🔵</div>
                                <div class="call-info">
                                    <div class="call-name">Clinica Santa Maria</div>
                                    <div class="call-desc">Confirmar hora medica lunes 11:00</div>
                                </div>
                                <div class="call-meta">
                                    <div class="call-time">11:20</div>
                                    <div class="call-badge normal">Normal</div>
                                </div>
                            </div>
                            <div class="call-item">
                                <div class="call-avatar spam">🔴</div>
                                <div class="call-info">
                                    <div class="call-name">+56 9 1111 2222</div>
                                    <div class="call-desc">Oferta tarjeta de credito</div>
                                </div>
                                <div class="call-meta">
                                    <div class="call-time">09:15</div>
                                    <div class="call-badge spam">Spam</div>
                                </div>
                            </div>
                        </div>
                        <div class="app-mock-tab-bar">
                            <div class="app-mock-tab active"><span class="tab-icon">📋</span>Llamadas</div>
                            <div class="app-mock-tab"><span class="tab-icon">📊</span>Stats</div>
                            <div class="app-mock-tab"><span class="tab-icon">⚙️</span>Config</div>
                            <div class="app-mock-tab"><span class="tab-icon">🕶️</span>Dora</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- ═══ PLANES ═══ -->
    <section class="plans" id="planes" aria-label="Planes y precios">
        <div class="section-label">Planes</div>
        <h2 class="section-title">Elige tu plan</h2>
        <p style="color: var(--text-muted); max-width: 700px; margin: 0 auto 20px; font-size: 0.9rem; text-align: center; line-height: 1.7;">En Chile recibimos en promedio <strong style="color:var(--accent)">~8 llamadas al dia</strong> (240/mes), de las cuales ~31 son spam. Empieza con <strong style="color:var(--green)">7 dias gratis</strong> con experiencia completa y despues elige el plan que se adapte a tu vida.</p>

        <div class="plans-grid">
            <!-- FREE TRIAL -->
            <div class="plan" style="border-color: var(--green); border-width: 2px;">
                <div class="plan-subtitle" style="color: var(--green);">7 dias gratis</div>
                <div class="plan-name">Prueba gratis</div>
                <div class="plan-price">$0<span>/7 dias</span></div>
                <div class="plan-desc">Experiencia completa del plan Pro ($6.99/mes) durante 7 dias. Sin tarjeta, sin compromiso.</div>
                <ul class="plan-features">
                    <li>300 llamadas durante el trial</li>
                    <li>Todas las funciones Pro incluidas</li>
                    <li>Graba tu voz, Modo Luna, analisis IA</li>
                    <li>Resumen WhatsApp + push</li>
                    <li>Al terminar, elige tu plan</li>
                </ul>
                <a href="{planes_url}" class="plan-btn secondary" style="background: var(--green); color: #0f172a; font-weight: 700;">Empezar 7 dias gratis</a>
            </div>

            <!-- BASICO / ESTUDIANTE -->
            <div class="plan">
                <div class="plan-subtitle">Estudiante</div>
                <div class="plan-name">Basico</div>
                <div class="plan-price">$4.99<span>/mes</span></div>
                <div class="plan-desc">Recibes unas 3 llamadas de desconocidos al dia y no quieres distraerte mientras estudias.</div>
                <ul class="plan-features">
                    <li>100 llamadas/mes (~3/dia)</li>
                    <li>IA contesta, escucha y transcribe</li>
                    <li>Analisis: quien, por que, urgencia</li>
                    <li>Resumen WhatsApp + push</li>
                    <li>Categoriza: Personal, Trabajo, Spam</li>
                </ul>
                <a href="{planes_url}" class="plan-btn primary">Elegir Estudiante</a>
            </div>

            <!-- PRO / ADULTO -->
            <div class="plan featured">
                <div class="plan-subtitle">Adulto</div>
                <div class="plan-name">Pro</div>
                <div class="plan-price">$6.99<span>/mes</span></div>
                <div class="plan-desc">Te llaman bastante para ofrecerte cosas, pero tienes miedo de perderte una llamada importante de un numero desconocido.</div>
                <ul class="plan-features">
                    <li>300 llamadas/mes (~10/dia)</li>
                    <li>Todo lo del Estudiante +</li>
                    <li>Graba tu voz como saludo</li>
                    <li>Modo Luna: silencia TODO</li>
                    <li>Prompt personalizado para la IA</li>
                    <li>Google Calendar + Outlook</li>
                </ul>
                <a href="{planes_url}" class="plan-btn primary">Elegir Pro &middot; $6.99/mes</a>
            </div>

            <!-- PREMIUM / EJECUTIVO -->
            <div class="plan">
                <div class="plan-subtitle">Ejecutivo</div>
                <div class="plan-name">Premium</div>
                <div class="plan-price">$9.99<span>/mes</span></div>
                <div class="plan-desc">Hay tramites y clientes que necesitan ser atendidos. Tu secretario digital filtra, envia recados y agenda reuniones por ti.</div>
                <ul class="plan-features">
                    <li>Llamadas ilimitadas</li>
                    <li>Todo lo del Pro ($6.99) +</li>
                    <li>La IA CONVERSA, no solo escucha</li>
                    <li>Toma recados y agenda reuniones</li>
                    <li>Consulta tu calendario en vivo</li>
                    <li>Voces premium + soporte prioritario</li>
                </ul>
                <a href="{planes_url}" class="plan-btn primary">Elegir Ejecutivo</a>
            </div>
        </div>

        <!-- TABLA COMPARATIVA -->
        <div style="max-width: 900px; margin: 60px auto 0; overflow-x: auto;">
            <h3 style="text-align: center; color: var(--text); margin-bottom: 20px; font-size: 1.3rem;">Compara los planes en detalle</h3>
            <table class="compare-table">
                <thead>
                    <tr>
                        <th style="text-align: left; color: var(--text-muted);"></th>
                        <th style="color: var(--green);">Prueba gratis</th>
                        <th style="color: var(--text);">Estudiante</th>
                        <th style="color: var(--primary-light);">Pro $6.99</th>
                        <th style="color: var(--accent);">Ejecutivo</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="text-align: left; color: var(--text-secondary);">Precio</td>
                        <td style="color: var(--green);">$0 / 7 dias</td>
                        <td>$4.99/mes</td>
                        <td style="color: var(--primary-light);">$6.99/mes</td>
                        <td>$9.99/mes</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: var(--text-secondary);">Llamadas/mes</td>
                        <td>300 (trial)</td>
                        <td>100 (~3/dia)</td>
                        <td>300 (~10/dia)</td>
                        <td>Ilimitadas</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: var(--text-secondary);">IA contesta y transcribe</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: var(--green);">&#10003;</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: var(--text-secondary);">Analisis IA + WhatsApp</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: var(--green);">&#10003;</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: var(--text-secondary);">Tu voz como saludo</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: var(--green);">&#10003;</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: var(--text-secondary);">Modo Luna (no molestar)</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: var(--green);">&#10003;</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: var(--text-secondary);">Prompt personalizado</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: var(--green);">&#10003;</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: var(--text-secondary);">Calendario (Google/Outlook)</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: var(--green);">&#10003;</td>
                        <td style="color: var(--green);">&#10003;</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: var(--text-secondary);">IA conversa (no solo escucha)</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: var(--green);">&#10003;</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: var(--text-secondary);">Voces premium + soporte</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: #64748b;">&#10007;</td>
                        <td style="color: var(--green);">&#10003;</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </section>

    <!-- ═══ FAQ ═══ -->
    <section class="faq" id="faq" aria-label="Preguntas frecuentes">
        <div class="section-label">Preguntas frecuentes</div>
        <h2 class="section-title">FAQ</h2>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Y si quiero desactivarlo? Es dificil?</div>
            <div class="faq-a">Para nada. Si quieres dejar de usar ContestaDora, solo marcas ##002# en el teclado de tu telefono y listo, tus llamadas vuelven a la normalidad al instante. La app te guia paso a paso tanto para activar como para desactivar. Sin contratos, sin letra chica.</div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Como funciona el desvio de llamadas?</div>
            <div class="faq-a">Marcas un codigo simple en el teclado de tu telefono (la app te lo da listo) y tu operador desvia las llamadas que no contestas a tu asistente IA. Solo se desvian las que no contestas, las demas las sigues recibiendo normal.</div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Se graban mis llamadas?</div>
            <div class="faq-a">No. Dora transcribe en tiempo real usando speech-to-text. El audio no se almacena. Solo guardamos la transcripcion de texto y el resumen generado por la IA. Tu agente de confianza.</div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Cuanto cuesta el plan Pro?</div>
            <div class="faq-a">El plan Pro (Adulto) cuesta $6.99/mes e incluye 300 llamadas, saludo con tu voz, Modo Luna, prompt personalizado y calendario. Puedes empezar con 7 dias gratis con todas las funciones Pro sin tarjeta de credito.</div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Puedo cancelar en cualquier momento?</div>
            <div class="faq-a">Si, sin compromiso. Puedes cancelar tu suscripcion cuando quieras. Dora entiende, pero te va a extranar.</div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Funciona en mi pais?</div>
            <div class="faq-a">ContestaDora funciona en cualquier pais donde Twilio tenga cobertura, que incluye la mayoria de paises de America Latina, Estados Unidos y Europa. Dora habla todos los idiomas.</div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('open')">
            <div class="faq-q">Que es el Agente IA del plan Premium?</div>
            <div class="faq-a">Es Dora en su modo mas poderoso: la AgendaDora. No solo escucha, conversa con tus llamantes, agenda reuniones, consulta tu calendario y toma decisiones segun tus instrucciones. Tu secretaria digital con 8 tentaculos.</div>
        </div>
    </section>

    <!-- ═══ CTA FINAL ═══ -->
    <section class="cta">
        <h2>No contestes otra llamada innecesaria</h2>
        <p>Deja que Dora se encargue. 7 dias gratis, sin tarjeta, sin compromisos. Plan Pro desde $6.99/mes. Recupera tu concentracion y tu tiempo.</p>
        <a href="{planes_url}" class="btn btn-primary" style="font-size:1.1rem; padding:16px 40px;">Empezar 7 dias gratis</a>
        <p style="color: var(--text-muted); font-size: 0.82rem; margin-top: 16px;">Activar toma 30 segundos. Desactivar tambien. Sin contratos.</p>
    </section>

    <!-- ═══ FOOTER ═══ -->
    <footer>
        <p><span style="font-weight:300;">Contesta</span><span style="font-weight:800;color:#7B73FF;">Dora</span> &copy; 2026 &middot; contestadora.io &middot; Hecho con IA en Latinoamerica</p>
        <p style="margin-top:8px;"><a href="/docs">API Docs</a> &middot; <a href="{planes_url}">Planes</a></p>
    </footer>
</body>
</html>"""
