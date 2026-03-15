"""Servicio de Drip Campaigns para Retención.

Campañas automáticas de retención por cohorte:
- Día 1: Onboarding - bienvenida y setup
- Día 3: Resumen de valor - estadísticas de lo que ha filtrado
- Día 7: Weekly report - reporte semanal
- Día 14: Upgrade offer - 50% off para plan pago

Métricas objetivo:
- Retención D30 +15-20pp
- LTV +25-35%
- Retención D7/D30/D90 por cohorte
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.database import (
    Usuario, DripCampaignEnvio, TipoDrip, Llamada,
    PlanTipo, Suscripcion, EstadoSuscripcion,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# TEMPLATES DE MENSAJES
# ═══════════════════════════════════════════════════════════

def _template_dia1_onboarding(usuario: Usuario) -> str:
    """Día 1: Bienvenida y guía de configuración."""
    return (
        f"Hola {usuario.nombre.split()[0]}! Bienvenido/a a ContestaDora.\n\n"
        f"Tu asistente '{usuario.nombre_asistente}' ya está lista para contestar tus llamadas.\n\n"
        f"Para activarla, configura el desvío de llamadas en tu celular:\n"
        f"*iPhone*: Ajustes > Teléfono > Desvío de llamadas > {usuario.telefono_twilio or 'tu número asignado'}\n"
        f"*Android*: Teléfono > Ajustes > Desvío > {usuario.telefono_twilio or 'tu número asignado'}\n\n"
        f"Tu trial de 7 días incluye todas las funciones Pro. Aprovéchalas!"
    )


def _template_dia3_resumen_valor(usuario: Usuario, db: Session) -> str:
    """Día 3: Resumen del valor que ha recibido."""
    # Contar llamadas filtradas en los últimos 3 días
    hace_3_dias = datetime.now(timezone.utc) - timedelta(days=3)
    total_llamadas = db.query(Llamada).filter(
        Llamada.usuario_id == usuario.id,
        Llamada.fecha_inicio >= hace_3_dias,
    ).count()
    spam = db.query(Llamada).filter(
        Llamada.usuario_id == usuario.id,
        Llamada.fecha_inicio >= hace_3_dias,
        Llamada.categoria == "Marketing",
    ).count()
    importantes = db.query(Llamada).filter(
        Llamada.usuario_id == usuario.id,
        Llamada.fecha_inicio >= hace_3_dias,
        Llamada.prioridad == "Alta",
    ).count()

    if total_llamadas == 0:
        return (
            f"Hola {usuario.nombre.split()[0]}! Llevas 3 días con ContestaDora.\n\n"
            f"Aún no hemos recibido llamadas. Asegúrate de tener el desvío activo "
            f"a {usuario.telefono_twilio or 'tu número asignado'}.\n\n"
            f"Prueba llamándote desde otro teléfono para verificar que funciona."
        )

    minutos_ahorrados = round(total_llamadas * 1.5, 1)  # ~1.5 min por llamada spam evitada
    return (
        f"Hola {usuario.nombre.split()[0]}! Tu resumen de 3 días con ContestaDora:\n\n"
        f"Llamadas gestionadas: {total_llamadas}\n"
        f"Spam filtrado: {spam}\n"
        f"Llamadas importantes detectadas: {importantes}\n"
        f"Tiempo ahorrado: ~{minutos_ahorrados} minutos\n\n"
        f"ContestaDora está trabajando para ti. Te quedan "
        f"{_dias_restantes_trial(usuario)} días de trial."
    )


def _template_dia7_weekly(usuario: Usuario, db: Session) -> str:
    """Día 7: Reporte semanal completo."""
    hace_7_dias = datetime.now(timezone.utc) - timedelta(days=7)
    total = db.query(Llamada).filter(
        Llamada.usuario_id == usuario.id,
        Llamada.fecha_inicio >= hace_7_dias,
    ).count()

    por_categoria = {}
    for cat in ["Personal", "Trabajo", "Trámite", "Marketing", "Desconocido"]:
        count = db.query(Llamada).filter(
            Llamada.usuario_id == usuario.id,
            Llamada.fecha_inicio >= hace_7_dias,
            Llamada.categoria == cat,
        ).count()
        if count > 0:
            por_categoria[cat] = count

    cat_texto = "\n".join([f"  - {k}: {v}" for k, v in por_categoria.items()])
    if not cat_texto:
        cat_texto = "  Sin datos aún"

    return (
        f"Tu reporte semanal con ContestaDora:\n\n"
        f"Total llamadas: {total}\n"
        f"Por categoría:\n{cat_texto}\n\n"
        f"Tu trial termina hoy. Si te ha sido útil, elige un plan para seguir "
        f"protegido/a contra el spam y nunca perder una llamada importante."
    )


def _template_dia14_upgrade(usuario: Usuario, db: Session) -> str:
    """Día 14: Oferta de upgrade con 50% off, código único por usuario.

    Genera un código personal intransferible vinculado al UID del usuario.
    Vence en 48 horas y solo puede usarse una vez.
    """
    from app.services.referidos_service import crear_codigo_descuento_usuario

    codigo = crear_codigo_descuento_usuario(
        db, usuario,
        tipo="porcentaje",
        valor=50,
        descripcion="50% off primer mes - drip día 14",
        dias_validez=2,  # 48 horas
    )

    return (
        f"Hola {usuario.nombre.split()[0]}! Han pasado 2 semanas desde que probaste ContestaDora.\n\n"
        f"Oferta especial *solo para ti*:\n"
        f"*50% de descuento en tu primer mes* de cualquier plan.\n\n"
        f"Plan Estudiante: $4.99 → $2.49/mes\n"
        f"Plan Adulto: $6.99 → $3.49/mes\n"
        f"Plan Ejecutivo: $9.99 → $4.99/mes\n\n"
        f"Tu código personal: *{codigo.codigo}*\n"
        f"(Este código es exclusivo para ti y no puede ser transferido)\n\n"
        f"Esta oferta vence en 48 horas. No dejes que el spam vuelva a interrumpirte."
    )


def _dias_restantes_trial(usuario: Usuario) -> int:
    """Calcula días restantes del trial."""
    if not usuario.trial_expira:
        return 0
    restante = (usuario.trial_expira - datetime.now(timezone.utc)).days
    return max(restante, 0)


# ═══════════════════════════════════════════════════════════
# PROGRAMACIÓN Y ENVÍO
# ═══════════════════════════════════════════════════════════

def programar_drip_para_usuario(db: Session, usuario: Usuario):
    """Programa todos los drip emails para un usuario nuevo.

    Se llama al registrarse. Crea los 4 envíos programados.
    """
    ahora = datetime.now(timezone.utc)
    drips = [
        (TipoDrip.DIA_1_ONBOARDING.value, ahora + timedelta(days=1)),
        (TipoDrip.DIA_3_RESUMEN_VALOR.value, ahora + timedelta(days=3)),
        (TipoDrip.DIA_7_WEEKLY_REPORT.value, ahora + timedelta(days=7)),
        (TipoDrip.DIA_14_UPGRADE_OFFER.value, ahora + timedelta(days=14)),
    ]

    for tipo, fecha in drips:
        # No duplicar si ya existe
        existente = db.query(DripCampaignEnvio).filter(
            DripCampaignEnvio.usuario_id == usuario.id,
            DripCampaignEnvio.tipo == tipo,
        ).first()
        if not existente:
            envio = DripCampaignEnvio(
                usuario_id=usuario.id,
                tipo=tipo,
                fecha_programada=fecha,
                canal="whatsapp" if usuario.notif_whatsapp else "push",
            )
            db.add(envio)

    db.commit()
    logger.info(f"Drip campaigns programadas para {usuario.email}")


def procesar_drips_pendientes(db: Session) -> int:
    """Procesa y envía todos los drips programados que ya vencieron.

    Se ejecuta periódicamente (cron job cada hora o cada 15 min).

    Returns:
        Cantidad de drips enviados.
    """
    ahora = datetime.now(timezone.utc)
    pendientes = db.query(DripCampaignEnvio).filter(
        DripCampaignEnvio.enviado == False,
        DripCampaignEnvio.fecha_programada <= ahora,
    ).all()

    enviados = 0
    for drip in pendientes:
        usuario = db.query(Usuario).filter(Usuario.id == drip.usuario_id).first()
        if not usuario or not usuario.activo:
            drip.enviado = True  # Marcar para no reintentar
            continue

        # Si ya pagó, no enviar upgrade offer
        if drip.tipo == TipoDrip.DIA_14_UPGRADE_OFFER.value:
            tiene_suscripcion = db.query(Suscripcion).filter(
                Suscripcion.usuario_id == usuario.id,
                Suscripcion.estado == EstadoSuscripcion.ACTIVA.value,
            ).first()
            if tiene_suscripcion:
                drip.enviado = True
                continue

        # Generar contenido
        contenido = _generar_contenido_drip(drip.tipo, usuario, db)
        if not contenido:
            continue

        # Enviar por el canal configurado
        exito = _enviar_drip(usuario, contenido, drip.canal)
        if exito:
            drip.enviado = True
            drip.fecha_enviado = ahora
            drip.contenido = contenido
            enviados += 1

    db.commit()
    logger.info(f"Drip campaigns procesadas: {enviados}/{len(pendientes)} enviadas")
    return enviados


def _generar_contenido_drip(tipo: str, usuario: Usuario, db: Session) -> Optional[str]:
    """Genera el contenido personalizado para cada tipo de drip."""
    generadores = {
        TipoDrip.DIA_1_ONBOARDING.value: lambda: _template_dia1_onboarding(usuario),
        TipoDrip.DIA_3_RESUMEN_VALOR.value: lambda: _template_dia3_resumen_valor(usuario, db),
        TipoDrip.DIA_7_WEEKLY_REPORT.value: lambda: _template_dia7_weekly(usuario, db),
        TipoDrip.DIA_14_UPGRADE_OFFER.value: lambda: _template_dia14_upgrade(usuario, db),
    }
    gen = generadores.get(tipo)
    return gen() if gen else None


def _enviar_drip(usuario: Usuario, contenido: str, canal: str) -> bool:
    """Envía el drip por el canal correspondiente.

    Intenta WhatsApp primero, luego push como fallback.
    """
    try:
        if canal == "whatsapp" and usuario.notif_whatsapp:
            from app.services.whatsapp_service import enviar_mensaje_whatsapp
            enviar_mensaje_whatsapp(usuario.telefono, contenido)
            return True
        elif canal == "push" and usuario.expo_push_token:
            from app.services.push_service import enviar_push
            enviar_push(usuario.expo_push_token, "ContestaDora", contenido[:200])
            return True
        else:
            logger.warning(f"No se pudo enviar drip a {usuario.email}: canal {canal} no disponible")
            return False
    except Exception as e:
        logger.error(f"Error enviando drip a {usuario.email}: {e}")
        return False


# ═══════════════════════════════════════════════════════════
# MÉTRICAS DE RETENCIÓN POR COHORTE
# ═══════════════════════════════════════════════════════════

def obtener_metricas_retencion(db: Session) -> dict:
    """Calcula métricas de retención D7/D30/D90 por cohorte semanal.

    Returns:
        dict con cohortes y tasas de retención.
    """
    ahora = datetime.now(timezone.utc)
    metricas = {
        "cohortes": [],
        "global": {},
    }

    # Últimas 12 semanas de cohortes
    for semana in range(12):
        inicio_cohorte = ahora - timedelta(weeks=semana + 1)
        fin_cohorte = ahora - timedelta(weeks=semana)

        usuarios_cohorte = db.query(Usuario).filter(
            Usuario.creado >= inicio_cohorte,
            Usuario.creado < fin_cohorte,
        ).all()

        total = len(usuarios_cohorte)
        if total == 0:
            continue

        # Retención: usuarios activos (con al menos 1 llamada) en cada periodo
        activos_d7 = 0
        activos_d30 = 0
        activos_d90 = 0

        for u in usuarios_cohorte:
            dias_desde_registro = (ahora - u.creado).days

            # D7: ¿tuvo llamada entre día 5 y 9?
            if dias_desde_registro >= 7:
                d7_inicio = u.creado + timedelta(days=5)
                d7_fin = u.creado + timedelta(days=9)
                if db.query(Llamada).filter(
                    Llamada.usuario_id == u.id,
                    Llamada.fecha_inicio >= d7_inicio,
                    Llamada.fecha_inicio <= d7_fin,
                ).first():
                    activos_d7 += 1

            # D30: ¿tuvo llamada entre día 25 y 35?
            if dias_desde_registro >= 30:
                d30_inicio = u.creado + timedelta(days=25)
                d30_fin = u.creado + timedelta(days=35)
                if db.query(Llamada).filter(
                    Llamada.usuario_id == u.id,
                    Llamada.fecha_inicio >= d30_inicio,
                    Llamada.fecha_inicio <= d30_fin,
                ).first():
                    activos_d30 += 1

            # D90: ¿tuvo llamada entre día 85 y 95?
            if dias_desde_registro >= 90:
                d90_inicio = u.creado + timedelta(days=85)
                d90_fin = u.creado + timedelta(days=95)
                if db.query(Llamada).filter(
                    Llamada.usuario_id == u.id,
                    Llamada.fecha_inicio >= d90_inicio,
                    Llamada.fecha_inicio <= d90_fin,
                ).first():
                    activos_d90 += 1

        elegibles_d7 = sum(1 for u in usuarios_cohorte if (ahora - u.creado).days >= 7)
        elegibles_d30 = sum(1 for u in usuarios_cohorte if (ahora - u.creado).days >= 30)
        elegibles_d90 = sum(1 for u in usuarios_cohorte if (ahora - u.creado).days >= 90)

        metricas["cohortes"].append({
            "semana": f"W-{semana + 1}",
            "inicio": inicio_cohorte.strftime("%Y-%m-%d"),
            "total_usuarios": total,
            "retencion_d7": round(activos_d7 / elegibles_d7 * 100, 1) if elegibles_d7 > 0 else None,
            "retencion_d30": round(activos_d30 / elegibles_d30 * 100, 1) if elegibles_d30 > 0 else None,
            "retencion_d90": round(activos_d90 / elegibles_d90 * 100, 1) if elegibles_d90 > 0 else None,
        })

    return metricas
