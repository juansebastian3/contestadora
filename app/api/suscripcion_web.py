"""Páginas web de suscripción + Webhooks de MercadoPago.

Rutas:
- GET  /suscripcion/planes            → Landing page con planes y precios
- GET  /suscripcion/checkout/{plan}    → Página de checkout (requiere login)
- POST /suscripcion/crear-pago         → Crea preferencia MP y redirige
- GET  /suscripcion/resultado          → Página resultado tras pago
- GET  /suscripcion/mi-plan            → Estado de suscripción actual
- POST /webhooks/mercadopago           → Webhook IPN de MercadoPago
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.models.database import get_db, Usuario, Suscripcion, PlanTipo
from app.core.auth import get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Suscripciones Web"])


# ═══════════════════════════════════════════════════════════
# PÁGINA DE PLANES (pública)
# ═══════════════════════════════════════════════════════════

@router.get("/suscripcion/planes", response_class=HTMLResponse)
async def pagina_planes():
    """Landing page pública con los planes y precios."""
    html = _render_planes_html()
    return HTMLResponse(content=html)


# ═══════════════════════════════════════════════════════════
# CHECKOUT: CREAR PAGO Y REDIRIGIR A MERCADOPAGO
# ═══════════════════════════════════════════════════════════

@router.post("/suscripcion/crear-pago")
async def crear_pago(
    request: Request,
    db: Session = Depends(get_db),
):
    """Crea una preferencia de pago en MercadoPago.

    Body: {email: str, plan: "pro"|"premium", periodo: "mensual"|"anual", token: str}
    El token es el JWT del usuario (se envía desde el form).
    """
    from app.services.mercadopago_service import crear_preferencia_pago

    body = await request.json()
    email = body.get("email", "")
    plan = body.get("plan", "")
    periodo = body.get("periodo", "mensual")
    token = body.get("token", "")

    if plan not in ("pro", "premium"):
        raise HTTPException(status_code=400, detail="Plan inválido")
    if periodo not in ("mensual", "anual"):
        raise HTTPException(status_code=400, detail="Periodo inválido")

    # Verificar usuario por token JWT
    from app.core.auth import verificar_token
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido. Inicia sesión desde la app primero.")

    usuario_uid = payload.get("uid", "")
    usuario = db.query(Usuario).filter(Usuario.uid == usuario_uid).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        resultado = crear_preferencia_pago(
            usuario_uid=usuario.uid,
            usuario_email=usuario.email,
            plan_codigo=plan,
            periodo=periodo,
        )

        # Guardar la suscripción pendiente
        suscripcion = Suscripcion(
            usuario_id=usuario.id,
            plan_codigo=plan,
            origen="mercadopago",
            estado="pendiente",
            mp_preference_id=resultado["preference_id"],
            mp_external_reference=resultado["external_reference"],
            periodo=periodo,
        )
        db.add(suscripcion)
        db.commit()

        # Retornar URL de pago
        # En sandbox usa sandbox_init_point, en producción usa init_point
        use_sandbox = settings.MERCADOPAGO_SANDBOX
        payment_url = resultado["sandbox_init_point"] if use_sandbox else resultado["init_point"]

        return {"payment_url": payment_url, "preference_id": resultado["preference_id"]}

    except Exception as e:
        logger.error(f"Error creando pago: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando pago: {str(e)[:200]}")


# ═══════════════════════════════════════════════════════════
# RESULTADO: PÁGINA DESPUÉS DEL PAGO
# ═══════════════════════════════════════════════════════════

@router.get("/suscripcion/resultado", response_class=HTMLResponse)
async def pagina_resultado(
    status: str = Query("unknown"),
    ref: str = Query(""),
    payment_id: str = Query(""),
    db: Session = Depends(get_db),
):
    """Página de resultado tras el pago en MercadoPago."""

    # Si viene payment_id, intentar procesar
    if payment_id and status == "approved":
        try:
            from app.services.mercadopago_service import procesar_notificacion_pago
            procesar_notificacion_pago(payment_id, db)
        except Exception as e:
            logger.error(f"Error procesando pago en resultado: {e}")

    if status == "approved":
        html = _render_resultado_html(
            titulo="Pago Aprobado",
            mensaje="Tu suscripción ha sido activada correctamente. Ya puedes disfrutar de todas las funciones de tu plan.",
            color="#22c55e",
            icono="check-circle",
        )
    elif status == "pending":
        html = _render_resultado_html(
            titulo="Pago Pendiente",
            mensaje="Tu pago está siendo procesado. Recibirás una notificación cuando se confirme y tu plan se activará automáticamente.",
            color="#f59e0b",
            icono="clock",
        )
    else:
        html = _render_resultado_html(
            titulo="Pago No Completado",
            mensaje="El pago no pudo ser procesado. Puedes intentar nuevamente desde la app o elegir otro medio de pago.",
            color="#ef4444",
            icono="x-circle",
        )

    return HTMLResponse(content=html)


# ═══════════════════════════════════════════════════════════
# MI PLAN: ESTADO DE SUSCRIPCIÓN (API protegida)
# ═══════════════════════════════════════════════════════════

@router.get("/api/v1/suscripcion/estado")
async def estado_suscripcion(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna el estado actual de la suscripción del usuario."""
    suscripcion_activa = db.query(Suscripcion).filter(
        Suscripcion.usuario_id == usuario.id,
        Suscripcion.estado == "activa",
    ).order_by(Suscripcion.creado.desc()).first()

    plan_activo = usuario.plan or "free"
    plan_expira = usuario.plan_expira

    # Verificar si expiró
    if plan_expira and plan_expira < datetime.now(timezone.utc):
        usuario.plan = PlanTipo.FREE.value
        usuario.plan_expira = None
        db.commit()
        plan_activo = "free"
        plan_expira = None

    return {
        "plan": plan_activo,
        "plan_expira": plan_expira.isoformat() if plan_expira else None,
        "suscripcion": {
            "origen": suscripcion_activa.origen,
            "estado": suscripcion_activa.estado,
            "periodo": suscripcion_activa.periodo,
            "monto": suscripcion_activa.monto,
            "moneda": suscripcion_activa.moneda,
            "fecha_inicio": suscripcion_activa.fecha_inicio.isoformat() if suscripcion_activa.fecha_inicio else None,
            "fecha_fin": suscripcion_activa.fecha_fin.isoformat() if suscripcion_activa.fecha_fin else None,
        } if suscripcion_activa else None,
        "url_planes": f"{settings.BASE_URL}/suscripcion/planes",
    }


# ═══════════════════════════════════════════════════════════
# WEBHOOK MERCADOPAGO (IPN)
# ═══════════════════════════════════════════════════════════

@router.post("/webhooks/mercadopago")
async def webhook_mercadopago(
    request: Request,
    db: Session = Depends(get_db),
):
    """Webhook de MercadoPago (IPN - Instant Payment Notification).

    MercadoPago envía notificaciones aquí cuando cambia el estado de un pago.
    """
    try:
        body = await request.json()
    except Exception:
        # Algunos webhooks vienen como form data
        body = dict(request.query_params)

    logger.info(f"Webhook MercadoPago recibido: {body}")

    tipo = body.get("type", body.get("topic", ""))
    data = body.get("data", {})

    if tipo == "payment":
        payment_id = data.get("id") or body.get("data.id")
        if payment_id:
            from app.services.mercadopago_service import procesar_notificacion_pago
            resultado = procesar_notificacion_pago(str(payment_id), db)
            logger.info(f"Webhook procesado: {resultado}")

    elif tipo == "merchant_order":
        # Notificación de orden - por ahora solo logear
        logger.info(f"Merchant order notification: {body}")

    # MercadoPago espera 200 OK
    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════
# HTML TEMPLATES
# ═══════════════════════════════════════════════════════════

def _render_planes_html() -> str:
    """Genera la landing page de planes con checkout integrado."""
    base_url = settings.BASE_URL
    use_sandbox = settings.MERCADOPAGO_SANDBOX

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FiltroLlamadas - Planes y Precios</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }}

        .hero {{ text-align: center; padding: 60px 20px 40px; }}
        .hero h1 {{ font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 12px; }}
        .hero p {{ color: #94a3b8; font-size: 1.1rem; max-width: 500px; margin: 0 auto; }}

        .planes {{ display: flex; justify-content: center; gap: 24px; padding: 20px; flex-wrap: wrap; max-width: 1000px; margin: 0 auto; }}

        .plan-card {{ background: #1e293b; border-radius: 20px; padding: 32px 28px; width: 300px; position: relative; border: 1px solid #334155; transition: transform 0.2s, border-color 0.2s; }}
        .plan-card:hover {{ transform: translateY(-4px); border-color: #6366f1; }}
        .plan-card.destacado {{ border: 2px solid #6366f1; }}
        .plan-card.destacado::before {{ content: "MAS POPULAR"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; font-size: 0.7rem; font-weight: 700; padding: 4px 16px; border-radius: 20px; letter-spacing: 1px; }}

        .plan-nombre {{ font-size: 1.3rem; font-weight: 700; color: #f1f5f9; margin-bottom: 8px; }}
        .plan-precio {{ font-size: 2.5rem; font-weight: 800; color: #6366f1; }}
        .plan-precio span {{ font-size: 1rem; font-weight: 400; color: #94a3b8; }}
        .plan-ahorro {{ font-size: 0.85rem; color: #22c55e; margin-top: 4px; margin-bottom: 16px; }}
        .plan-desc {{ color: #94a3b8; font-size: 0.9rem; margin-bottom: 20px; line-height: 1.4; }}

        .features {{ list-style: none; margin-bottom: 24px; }}
        .features li {{ padding: 6px 0; font-size: 0.9rem; color: #cbd5e1; display: flex; align-items: center; gap: 8px; }}
        .features li::before {{ content: "\\2713"; color: #22c55e; font-weight: 700; }}

        .periodo-toggle {{ display: flex; justify-content: center; gap: 0; margin: 0 auto 8px; background: #334155; border-radius: 10px; overflow: hidden; }}
        .periodo-btn {{ padding: 8px 16px; font-size: 0.85rem; cursor: pointer; border: none; background: transparent; color: #94a3b8; transition: all 0.2s; }}
        .periodo-btn.active {{ background: #6366f1; color: white; }}

        .btn-suscribir {{ display: block; width: 100%; padding: 14px; border: none; border-radius: 12px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
        .btn-suscribir.pro {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; }}
        .btn-suscribir.premium {{ background: linear-gradient(135deg, #f59e0b, #f97316); color: white; }}
        .btn-suscribir:hover {{ opacity: 0.9; transform: scale(1.02); }}
        .btn-suscribir:disabled {{ opacity: 0.5; cursor: not-allowed; transform: none; }}

        .login-section {{ text-align: center; margin-top: 16px; padding: 16px; background: #1e293b; border-radius: 12px; }}
        .login-section input {{ padding: 10px 14px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: white; width: 100%; margin-bottom: 8px; font-size: 0.9rem; }}
        .login-section .btn-login {{ padding: 10px 20px; border-radius: 8px; background: #475569; color: white; border: none; cursor: pointer; font-size: 0.9rem; width: 100%; }}
        .login-section .btn-login:hover {{ background: #6366f1; }}

        .logged-in {{ color: #22c55e; font-size: 0.9rem; margin-bottom: 8px; }}
        .error {{ color: #ef4444; font-size: 0.85rem; margin-top: 8px; }}

        .garantia {{ text-align: center; padding: 40px 20px; color: #64748b; font-size: 0.85rem; }}
        .garantia strong {{ color: #94a3b8; }}

        .metodos {{ display: flex; justify-content: center; gap: 12px; margin-top: 12px; flex-wrap: wrap; }}
        .metodo {{ background: #1e293b; padding: 6px 14px; border-radius: 8px; font-size: 0.8rem; color: #94a3b8; }}

        @media (max-width: 700px) {{
            .planes {{ flex-direction: column; align-items: center; }}
            .hero h1 {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>FiltroLlamadas</h1>
        <p>Tu asistente IA que contesta y filtra llamadas. Elige el plan que se adapte a ti.</p>
    </div>

    <!-- Login previo -->
    <div id="auth-section" style="max-width: 400px; margin: 0 auto 24px; padding: 0 20px;">
        <div class="login-section" id="login-form">
            <p style="color: #94a3b8; margin-bottom: 12px; font-size: 0.9rem;">Inicia sesion con tu cuenta de FiltroLlamadas</p>
            <input type="email" id="login-email" placeholder="Email" autocomplete="email">
            <input type="password" id="login-password" placeholder="Contraseña" autocomplete="current-password">
            <button class="btn-login" onclick="iniciarSesion()">Iniciar Sesion</button>
            <p id="login-error" class="error" style="display:none;"></p>
        </div>
        <div id="logged-info" style="display:none; text-align:center;">
            <p class="logged-in" id="user-name"></p>
        </div>
    </div>

    <div class="planes">
        <!-- PRO -->
        <div class="plan-card destacado">
            <div class="plan-nombre">Pro</div>
            <div class="plan-precio" id="precio-pro">$4.99<span>/mes</span></div>
            <div class="plan-ahorro" id="ahorro-pro" style="display:none;"></div>
            <div class="plan-desc">Tu voz grabada como contestadora personal + modo luna</div>
            <div class="periodo-toggle">
                <button class="periodo-btn active" onclick="setPeriodo('pro','mensual',this)">Mensual</button>
                <button class="periodo-btn" onclick="setPeriodo('pro','anual',this)">Anual</button>
            </div>
            <ul class="features">
                <li>200 llamadas / mes</li>
                <li>500 minutos de filtrado</li>
                <li>Tu voz grabada para conocidos</li>
                <li>Voz Polly para desconocidos</li>
                <li>Prompt personalizado</li>
                <li>Modo Luna</li>
                <li>Transcripcion y resumen IA</li>
            </ul>
            <button class="btn-suscribir pro" onclick="suscribir('pro')" id="btn-pro" disabled>Suscribirme a Pro</button>
        </div>

        <!-- PREMIUM -->
        <div class="plan-card">
            <div class="plan-nombre">Premium</div>
            <div class="plan-precio" id="precio-premium">$9.99<span>/mes</span></div>
            <div class="plan-ahorro" id="ahorro-premium" style="display:none;"></div>
            <div class="plan-desc">Secretaria IA que conversa, agenda y gestiona tus llamadas</div>
            <div class="periodo-toggle">
                <button class="periodo-btn active" onclick="setPeriodo('premium','mensual',this)">Mensual</button>
                <button class="periodo-btn" onclick="setPeriodo('premium','anual',this)">Anual</button>
            </div>
            <ul class="features">
                <li>Llamadas ilimitadas</li>
                <li>Minutos ilimitados</li>
                <li>Tu voz grabada + IA conversa</li>
                <li>Secretaria IA inteligente</li>
                <li>Google Calendar + Outlook</li>
                <li>Modo Luna con horario</li>
                <li>Soporte prioritario</li>
            </ul>
            <button class="btn-suscribir premium" onclick="suscribir('premium')" id="btn-premium" disabled>Suscribirme a Premium</button>
        </div>
    </div>

    <div class="garantia">
        <p><strong>Pago seguro con MercadoPago</strong></p>
        <p>Tarjetas, transferencia bancaria, efectivo y mas</p>
        <div class="metodos">
            <span class="metodo">Visa</span>
            <span class="metodo">Mastercard</span>
            <span class="metodo">Transferencia</span>
            <span class="metodo">MercadoPago</span>
        </div>
        <p style="margin-top: 16px;">Cancela cuando quieras. Sin compromiso.</p>
    </div>

    <script>
        const BASE = "{base_url}";
        let token = null;
        let periodos = {{ pro: "mensual", premium: "mensual" }};
        const precios = {{
            pro: {{ mensual: 4.99, anual: 49.99 }},
            premium: {{ mensual: 9.99, anual: 99.99 }}
        }};

        // Check if token comes from app via URL param
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get("token")) {{
            token = urlParams.get("token");
            document.getElementById("login-form").style.display = "none";
            document.getElementById("logged-info").style.display = "block";
            document.getElementById("user-name").textContent = "Sesion activa desde la app";
            document.getElementById("btn-pro").disabled = false;
            document.getElementById("btn-premium").disabled = false;
        }}

        async function iniciarSesion() {{
            const email = document.getElementById("login-email").value;
            const password = document.getElementById("login-password").value;
            const errorEl = document.getElementById("login-error");
            errorEl.style.display = "none";

            try {{
                const resp = await fetch(BASE + "/auth/login", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{ email, password }})
                }});
                const data = await resp.json();
                if (!resp.ok) {{
                    errorEl.textContent = data.detail || "Error al iniciar sesion";
                    errorEl.style.display = "block";
                    return;
                }}
                token = data.access_token;
                document.getElementById("login-form").style.display = "none";
                document.getElementById("logged-info").style.display = "block";
                document.getElementById("user-name").textContent = "Conectado como " + (data.perfil?.nombre || email);
                document.getElementById("btn-pro").disabled = false;
                document.getElementById("btn-premium").disabled = false;
            }} catch (e) {{
                errorEl.textContent = "Error de conexion";
                errorEl.style.display = "block";
            }}
        }}

        function setPeriodo(plan, periodo, btn) {{
            periodos[plan] = periodo;
            // Toggle active class
            btn.parentElement.querySelectorAll(".periodo-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            // Update price display
            const precio = precios[plan][periodo];
            const suffix = periodo === "anual" ? "/año" : "/mes";
            document.getElementById("precio-" + plan).innerHTML = "$" + precio + "<span>" + suffix + "</span>";
            // Show savings for annual
            const ahorroEl = document.getElementById("ahorro-" + plan);
            if (periodo === "anual") {{
                const ahorro = (precios[plan].mensual * 12 - precios[plan].anual).toFixed(2);
                ahorroEl.textContent = "Ahorras $" + ahorro + " al año";
                ahorroEl.style.display = "block";
            }} else {{
                ahorroEl.style.display = "none";
            }}
        }}

        async function suscribir(plan) {{
            if (!token) {{
                alert("Primero inicia sesion con tu cuenta de FiltroLlamadas");
                return;
            }}

            const btn = document.getElementById("btn-" + plan);
            btn.disabled = true;
            btn.textContent = "Procesando...";

            try {{
                const resp = await fetch(BASE + "/suscripcion/crear-pago", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{
                        plan: plan,
                        periodo: periodos[plan],
                        token: token,
                    }})
                }});
                const data = await resp.json();
                if (!resp.ok) {{
                    alert(data.detail || "Error al crear pago");
                    btn.disabled = false;
                    btn.textContent = "Suscribirme a " + plan.charAt(0).toUpperCase() + plan.slice(1);
                    return;
                }}
                // Redirigir a MercadoPago
                window.location.href = data.payment_url;
            }} catch (e) {{
                alert("Error de conexion. Intenta de nuevo.");
                btn.disabled = false;
                btn.textContent = "Suscribirme a " + plan.charAt(0).toUpperCase() + plan.slice(1);
            }}
        }}
    </script>
</body>
</html>"""


def _render_resultado_html(titulo: str, mensaje: str, color: str, icono: str) -> str:
    """Genera la página de resultado del pago."""
    # SVG icons
    icons = {
        "check-circle": f'<svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>',
        "clock": f'<svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "x-circle": f'<svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    }
    svg = icons.get(icono, "")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FiltroLlamadas - {titulo}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
        .card {{ background: #1e293b; border-radius: 20px; padding: 48px 36px; text-align: center; max-width: 420px; margin: 20px; border: 1px solid #334155; }}
        .icon {{ margin-bottom: 20px; }}
        h1 {{ color: {color}; font-size: 1.6rem; margin-bottom: 12px; }}
        p {{ color: #94a3b8; line-height: 1.6; margin-bottom: 24px; }}
        .btn {{ display: inline-block; padding: 12px 28px; border-radius: 10px; background: #6366f1; color: white; text-decoration: none; font-weight: 600; transition: opacity 0.2s; }}
        .btn:hover {{ opacity: 0.85; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">{svg}</div>
        <h1>{titulo}</h1>
        <p>{mensaje}</p>
        <a href="{settings.BASE_URL}/suscripcion/planes" class="btn">Volver a planes</a>
    </div>
</body>
</html>"""
