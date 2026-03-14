"""Router unificado de pagos — MercadoPago + Transbank + Flow.cl

Endpoints:
─────────────────────────────────────────────────────────────
  API (app móvil):
    POST /api/v1/pagos/crear       → Crea pago en la pasarela elegida
    GET  /api/v1/pagos/pasarelas   → Lista pasarelas disponibles

  Retornos (browser redirects después de pagar):
    GET  /pagos/transbank/retorno  → Confirma pago WebPay
    GET  /pagos/flow/retorno       → Confirma pago Flow

  Webhooks (notificaciones de las pasarelas):
    POST /webhooks/flow            → Webhook Flow.cl
    POST /webhooks/mercadopago     → (ya existe en suscripcion_web.py)
─────────────────────────────────────────────────────────────

La app móvil llama a POST /api/v1/pagos/crear con:
{
    "pasarela": "mercadopago" | "transbank" | "flow",
    "plan": "basico" | "pro" | "premium",
    "periodo": "mensual" | "anual"
}

Y recibe una URL de pago para abrir en el browser.
"""
import logging
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.models.database import get_db, Usuario
from app.core.auth import get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Pagos"])


# ═══════════════════════════════════════════════════════════
# PASARELAS DISPONIBLES
# ═══════════════════════════════════════════════════════════

@router.get("/api/v1/pagos/pasarelas")
async def listar_pasarelas():
    """Lista las pasarelas de pago configuradas y disponibles."""
    pasarelas = []

    if settings.MERCADOPAGO_ACCESS_TOKEN:
        pasarelas.append({
            "id": "mercadopago",
            "nombre": "MercadoPago",
            "moneda": "USD",
            "descripcion": "Tarjetas, transferencia, efectivo, wallet MercadoPago",
            "icono": "card",
        })

    if settings.TRANSBANK_COMMERCE_CODE or settings.TRANSBANK_SANDBOX:
        pasarelas.append({
            "id": "transbank",
            "nombre": "WebPay",
            "moneda": "CLP",
            "descripcion": "Tarjetas de credito/debito chilenas (Visa, Mastercard, Redcompra)",
            "icono": "card-outline",
        })

    if settings.FLOW_API_KEY or settings.FLOW_SANDBOX:
        pasarelas.append({
            "id": "flow",
            "nombre": "Flow.cl",
            "moneda": "CLP",
            "descripcion": "WebPay, Servipag, Multicaja, Mach, Khipu",
            "icono": "wallet-outline",
        })

    return {"pasarelas": pasarelas}


# ═══════════════════════════════════════════════════════════
# CREAR PAGO (endpoint unificado para la app)
# ═══════════════════════════════════════════════════════════

@router.post("/api/v1/pagos/crear")
async def crear_pago(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea un pago en la pasarela elegida. Retorna URL para pagar.

    Body: {pasarela: str, plan: str, periodo: str}
    """
    body = await request.json()
    pasarela = body.get("pasarela", "mercadopago")
    plan = body.get("plan", "")
    periodo = body.get("periodo", "mensual")

    if plan not in ("basico", "pro", "premium"):
        raise HTTPException(status_code=400, detail="Plan invalido")
    if periodo not in ("mensual", "anual"):
        raise HTTPException(status_code=400, detail="Periodo invalido")

    try:
        if pasarela == "mercadopago":
            return await _crear_pago_mercadopago(usuario, plan, periodo, db)
        elif pasarela == "transbank":
            return await _crear_pago_transbank(usuario, plan, periodo, db)
        elif pasarela == "flow":
            return await _crear_pago_flow(usuario, plan, periodo, db)
        else:
            raise HTTPException(status_code=400, detail=f"Pasarela '{pasarela}' no soportada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando pago ({pasarela}): {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando pago: {str(e)[:200]}")


async def _crear_pago_mercadopago(usuario, plan, periodo, db):
    from app.services.mercadopago_service import crear_preferencia_pago
    from app.models.database import Suscripcion

    resultado = crear_preferencia_pago(
        usuario_uid=usuario.uid,
        usuario_email=usuario.email,
        plan_codigo=plan,
        periodo=periodo,
    )

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

    use_sandbox = settings.MERCADOPAGO_SANDBOX
    payment_url = resultado["sandbox_init_point"] if use_sandbox else resultado["init_point"]

    return {
        "pasarela": "mercadopago",
        "payment_url": payment_url,
        "moneda": "USD",
    }


async def _crear_pago_transbank(usuario, plan, periodo, db):
    from app.services.transbank_service import crear_transaccion_webpay
    from app.models.database import Suscripcion

    resultado = crear_transaccion_webpay(
        usuario_uid=usuario.uid,
        plan_codigo=plan,
        periodo=periodo,
    )

    # Guardar datos en suscripción pendiente
    suscripcion = Suscripcion(
        usuario_id=usuario.id,
        plan_codigo=plan,
        origen="transbank",
        estado="pendiente",
        tbk_buy_order=resultado["buy_order"],
        periodo=periodo,
        monto=resultado["monto_clp"],
        moneda="CLP",
    )
    db.add(suscripcion)
    db.commit()

    # WebPay requiere POST al formulario con token
    # La app abre esta URL y WebPay maneja el pago
    payment_url = f"{resultado['url']}?token_ws={resultado['token']}"

    return {
        "pasarela": "transbank",
        "payment_url": payment_url,
        "token": resultado["token"],
        "moneda": "CLP",
        "monto_clp": resultado["monto_clp"],
    }


async def _crear_pago_flow(usuario, plan, periodo, db):
    from app.services.flow_service import crear_orden_flow

    resultado = crear_orden_flow(
        usuario_uid=usuario.uid,
        usuario_email=usuario.email,
        plan_codigo=plan,
        periodo=periodo,
    )

    return {
        "pasarela": "flow",
        "payment_url": resultado["url"],
        "moneda": "CLP",
        "monto_clp": resultado["monto_clp"],
    }


# ═══════════════════════════════════════════════════════════
# RETORNO TRANSBANK (redirect después de pagar)
# ═══════════════════════════════════════════════════════════

@router.get("/pagos/transbank/retorno", response_class=HTMLResponse)
@router.post("/pagos/transbank/retorno", response_class=HTMLResponse)
async def transbank_retorno(
    request: Request,
    db: Session = Depends(get_db),
):
    """Transbank redirige aquí después del pago.

    WebPay envía token_ws como GET param (aprobado) o TBK_TOKEN (rechazado).
    """
    params = dict(request.query_params)

    # También puede venir como form data (POST)
    if request.method == "POST":
        form = await request.form()
        params.update(dict(form))

    token_ws = params.get("token_ws", "")
    tbk_token = params.get("TBK_TOKEN", "")

    if tbk_token and not token_ws:
        # Pago cancelado o rechazado por el usuario
        return HTMLResponse(content=_resultado_html(
            "Pago Cancelado",
            "El pago fue cancelado. Puedes intentar de nuevo desde la app.",
            "#ef4444",
        ))

    if not token_ws:
        return HTMLResponse(content=_resultado_html(
            "Error",
            "No se recibio el token de pago.",
            "#ef4444",
        ))

    # Buscar la suscripción pendiente por buy_order
    from app.models.database import Suscripcion
    suscripcion = db.query(Suscripcion).filter(
        Suscripcion.origen == "transbank",
        Suscripcion.estado == "pendiente",
    ).order_by(Suscripcion.creado.desc()).first()

    if not suscripcion:
        return HTMLResponse(content=_resultado_html(
            "Error",
            "No se encontro la suscripcion asociada a este pago.",
            "#ef4444",
        ))

    # Obtener usuario
    usuario = db.query(Usuario).filter(Usuario.id == suscripcion.usuario_id).first()

    try:
        from app.services.transbank_service import procesar_pago_transbank
        resultado = procesar_pago_transbank(
            token_ws, db, usuario.uid, suscripcion.plan_codigo, suscripcion.periodo,
        )

        if resultado["status"] == "ok":
            return HTMLResponse(content=_resultado_html(
                "Pago Aprobado",
                f"Tu plan {suscripcion.plan_codigo.capitalize()} ha sido activado. Ya puedes volver a la app.",
                "#22c55e",
            ))
        else:
            return HTMLResponse(content=_resultado_html(
                "Pago Rechazado",
                "El pago no pudo ser procesado. Puedes intentar con otro medio de pago.",
                "#ef4444",
            ))
    except Exception as e:
        logger.error(f"Error procesando retorno Transbank: {e}")
        return HTMLResponse(content=_resultado_html(
            "Error",
            f"Hubo un error procesando tu pago. Contacta soporte.",
            "#ef4444",
        ))


# ═══════════════════════════════════════════════════════════
# RETORNO FLOW (redirect después de pagar)
# ═══════════════════════════════════════════════════════════

@router.get("/pagos/flow/retorno", response_class=HTMLResponse)
async def flow_retorno(
    token: str = Query(""),
    db: Session = Depends(get_db),
):
    """Flow redirige aquí después del pago."""
    if not token:
        return HTMLResponse(content=_resultado_html(
            "Error", "No se recibio el token de Flow.", "#ef4444",
        ))

    try:
        from app.services.flow_service import obtener_estado_pago
        estado = obtener_estado_pago(token)

        if not estado:
            return HTMLResponse(content=_resultado_html(
                "Error", "No se pudo consultar el estado del pago.", "#ef4444",
            ))

        flow_status = estado.get("status", 0)

        if flow_status == 2:
            return HTMLResponse(content=_resultado_html(
                "Pago Aprobado",
                "Tu suscripcion ha sido activada. Ya puedes volver a la app.",
                "#22c55e",
            ))
        elif flow_status == 1:
            return HTMLResponse(content=_resultado_html(
                "Pago Pendiente",
                "Tu pago esta siendo procesado. Te notificaremos cuando se confirme.",
                "#f59e0b",
            ))
        else:
            return HTMLResponse(content=_resultado_html(
                "Pago No Completado",
                "El pago no pudo ser procesado. Puedes intentar de nuevo.",
                "#ef4444",
            ))
    except Exception as e:
        logger.error(f"Error en retorno Flow: {e}")
        return HTMLResponse(content=_resultado_html(
            "Error", "Hubo un error procesando tu pago.", "#ef4444",
        ))


# ═══════════════════════════════════════════════════════════
# WEBHOOK FLOW.CL
# ═══════════════════════════════════════════════════════════

@router.post("/webhooks/flow")
async def webhook_flow(
    request: Request,
    db: Session = Depends(get_db),
):
    """Webhook de confirmación de Flow.cl.

    Flow envía un POST con el token cuando el pago cambia de estado.
    """
    form = await request.form()
    token = form.get("token", "")

    if not token:
        logger.warning("Webhook Flow sin token")
        return {"status": "error", "detail": "Token faltante"}

    logger.info(f"Webhook Flow recibido: token={token[:20]}...")

    try:
        from app.services.flow_service import procesar_pago_flow
        resultado = procesar_pago_flow(token, db)
        logger.info(f"Webhook Flow procesado: {resultado}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error procesando webhook Flow: {e}")
        return {"status": "error"}


# ═══════════════════════════════════════════════════════════
# HTML TEMPLATE (resultado de pago)
# ═══════════════════════════════════════════════════════════

def _resultado_html(titulo: str, mensaje: str, color: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ContestaDora - {titulo}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, sans-serif; background: #0f172a; color: #e2e8f0;
               display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
        .card {{ background: #1e293b; border-radius: 20px; padding: 48px 36px; text-align: center;
                 max-width: 420px; margin: 20px; border: 1px solid #334155; }}
        h1 {{ color: {color}; font-size: 1.6rem; margin-bottom: 12px; }}
        p {{ color: #94a3b8; line-height: 1.6; margin-bottom: 24px; }}
        .btn {{ display: inline-block; padding: 12px 28px; border-radius: 10px; background: #6366f1;
                color: white; text-decoration: none; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{titulo}</h1>
        <p>{mensaje}</p>
        <a href="{settings.BASE_URL}/suscripcion/planes" class="btn">Volver</a>
    </div>
</body>
</html>"""
