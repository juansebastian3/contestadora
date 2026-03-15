"""Servicio de Auto-Release de Números Twilio Inactivos.

Si un usuario no recibe llamadas en 60 días → liberar su número Twilio.
Cuando el usuario quiera reactivar → asignar nuevo número.

Ahorro estimado: $1.15/mes por usuario dormido.
A 30% inactivos = $345/mes por cada 1,000 users.

Métricas clave:
- % números activos vs total
- Costo Twilio / usuario activo
- Tasa de reactivación post-release
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.database import Usuario, Llamada, TwilioAutoRelease
from app.services.twilio_numbers import liberar_numero, asignar_numero_a_usuario

logger = logging.getLogger(__name__)

DIAS_INACTIVIDAD_PARA_RELEASE = 60
COSTO_NUMERO_TWILIO_MES = 1.15  # USD/mes por número


# ═══════════════════════════════════════════════════════════
# DETECCIÓN DE INACTIVIDAD
# ═══════════════════════════════════════════════════════════

def detectar_usuarios_inactivos(db: Session, dias: int = DIAS_INACTIVIDAD_PARA_RELEASE) -> List[Usuario]:
    """Detecta usuarios con número Twilio que no han recibido llamadas en N días.

    Returns:
        Lista de usuarios candidatos para auto-release.
    """
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)

    # Usuarios con número Twilio asignado
    usuarios_con_numero = db.query(Usuario).filter(
        Usuario.telefono_twilio.isnot(None),
        Usuario.twilio_phone_sid.isnot(None),
        Usuario.twilio_numero_liberado == False,
        Usuario.activo == True,
    ).all()

    inactivos = []
    for usuario in usuarios_con_numero:
        # Verificar última llamada
        ultima_llamada = usuario.ultima_llamada_recibida

        # Si no tiene registro de última llamada, buscar en la tabla de llamadas
        if not ultima_llamada:
            ultima = db.query(Llamada).filter(
                Llamada.usuario_id == usuario.id,
            ).order_by(Llamada.fecha_inicio.desc()).first()
            if ultima:
                ultima_llamada = ultima.fecha_inicio
                usuario.ultima_llamada_recibida = ultima_llamada
            else:
                # Nunca ha recibido llamadas → usar fecha de creación
                ultima_llamada = usuario.creado

        if ultima_llamada and ultima_llamada < fecha_limite:
            inactivos.append(usuario)

    if inactivos:
        db.commit()  # Guardar las actualizaciones de ultima_llamada_recibida

    return inactivos


# ═══════════════════════════════════════════════════════════
# AUTO-RELEASE
# ═══════════════════════════════════════════════════════════

def ejecutar_auto_release(db: Session) -> dict:
    """Ejecuta el proceso de auto-release de números Twilio inactivos.

    Se ejecuta como cron job diario.

    Returns:
        dict con estadísticas del proceso.
    """
    inactivos = detectar_usuarios_inactivos(db)

    liberados = 0
    errores = 0
    ahorro_mensual = 0.0

    for usuario in inactivos:
        try:
            numero_anterior = usuario.telefono_twilio
            sid_anterior = usuario.twilio_phone_sid
            dias_inactivo = (datetime.now(timezone.utc) - (usuario.ultima_llamada_recibida or usuario.creado)).days

            # Liberar el número en Twilio
            exito = liberar_numero(db, usuario)
            if exito:
                # Registrar en log de auto-releases
                log = TwilioAutoRelease(
                    usuario_id=usuario.id,
                    numero_liberado=numero_anterior,
                    twilio_phone_sid=sid_anterior,
                    dias_inactivo=dias_inactivo,
                )
                db.add(log)

                # Marcar usuario
                usuario.twilio_numero_liberado = True
                liberados += 1
                ahorro_mensual += COSTO_NUMERO_TWILIO_MES

                logger.info(
                    f"Número auto-liberado: {numero_anterior} "
                    f"(usuario {usuario.uid}, {dias_inactivo} días inactivo)"
                )
            else:
                errores += 1
                logger.error(f"Error liberando número de usuario {usuario.uid}")

        except Exception as e:
            errores += 1
            logger.error(f"Error en auto-release para usuario {usuario.uid}: {e}")

    db.commit()

    resultado = {
        "candidatos": len(inactivos),
        "liberados": liberados,
        "errores": errores,
        "ahorro_mensual_usd": round(ahorro_mensual, 2),
        "ahorro_anual_usd": round(ahorro_mensual * 12, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(f"Auto-release completado: {resultado}")
    return resultado


# ═══════════════════════════════════════════════════════════
# REACTIVACIÓN
# ═══════════════════════════════════════════════════════════

def reactivar_numero(db: Session, usuario: Usuario, codigo_pais: str = "US") -> Optional[dict]:
    """Re-asigna un número Twilio a un usuario cuyo número fue auto-liberado.

    Se llama cuando el usuario quiere volver a usar el servicio.

    Returns:
        dict con info del nuevo número o None si falla.
    """
    if not usuario.twilio_numero_liberado:
        # Ya tiene número activo
        if usuario.telefono_twilio:
            return {
                "phone_number": usuario.telefono_twilio,
                "sid": usuario.twilio_phone_sid,
                "ya_asignado": True,
            }
        # No tenía número y no fue liberado → asignar normalmente

    # Asignar nuevo número
    resultado = asignar_numero_a_usuario(db, usuario, codigo_pais)
    if resultado:
        usuario.twilio_numero_liberado = False
        usuario.ultima_llamada_recibida = datetime.now(timezone.utc)

        # Actualizar log de auto-release
        ultimo_release = db.query(TwilioAutoRelease).filter(
            TwilioAutoRelease.usuario_id == usuario.id,
            TwilioAutoRelease.reasignado == False,
        ).order_by(TwilioAutoRelease.fecha_liberacion.desc()).first()

        if ultimo_release:
            ultimo_release.reasignado = True
            ultimo_release.fecha_reasignacion = datetime.now(timezone.utc)

        db.commit()
        logger.info(f"Número reactivado para usuario {usuario.uid}: {resultado['phone_number']}")

    return resultado


# ═══════════════════════════════════════════════════════════
# ACTUALIZAR TIMESTAMP DE ÚLTIMA LLAMADA
# ═══════════════════════════════════════════════════════════

def registrar_llamada_recibida(db: Session, usuario: Usuario):
    """Actualiza el timestamp de última llamada recibida.

    Se llama desde el webhook de incoming call.
    """
    usuario.ultima_llamada_recibida = datetime.now(timezone.utc)
    db.commit()


# ═══════════════════════════════════════════════════════════
# MÉTRICAS
# ═══════════════════════════════════════════════════════════

def obtener_metricas_twilio(db: Session) -> dict:
    """Métricas de uso y costo de números Twilio.

    Returns:
        dict con estadísticas de números activos, inactivos, costos.
    """
    total_usuarios = db.query(Usuario).filter(Usuario.activo == True).count()

    con_numero = db.query(Usuario).filter(
        Usuario.telefono_twilio.isnot(None),
        Usuario.activo == True,
    ).count()

    numeros_liberados = db.query(Usuario).filter(
        Usuario.twilio_numero_liberado == True,
        Usuario.activo == True,
    ).count()

    # Números activos (con llamada en últimos 30 días)
    hace_30_dias = datetime.now(timezone.utc) - timedelta(days=30)
    activos_30d = db.query(Usuario).filter(
        Usuario.telefono_twilio.isnot(None),
        Usuario.ultima_llamada_recibida >= hace_30_dias,
        Usuario.activo == True,
    ).count()

    # Candidatos para release (inactivos > 60 días pero con número)
    hace_60_dias = datetime.now(timezone.utc) - timedelta(days=DIAS_INACTIVIDAD_PARA_RELEASE)
    candidatos_release = db.query(Usuario).filter(
        Usuario.telefono_twilio.isnot(None),
        Usuario.twilio_numero_liberado == False,
        or_(
            Usuario.ultima_llamada_recibida < hace_60_dias,
            and_(
                Usuario.ultima_llamada_recibida.is_(None),
                Usuario.creado < hace_60_dias,
            ),
        ),
        Usuario.activo == True,
    ).count()

    # Reactivaciones históricas
    total_releases = db.query(TwilioAutoRelease).count()
    total_reactivaciones = db.query(TwilioAutoRelease).filter(
        TwilioAutoRelease.reasignado == True,
    ).count()

    costo_mensual_actual = con_numero * COSTO_NUMERO_TWILIO_MES
    ahorro_potencial = candidatos_release * COSTO_NUMERO_TWILIO_MES

    return {
        "total_usuarios": total_usuarios,
        "con_numero_twilio": con_numero,
        "numeros_activos_30d": activos_30d,
        "numeros_liberados": numeros_liberados,
        "candidatos_release": candidatos_release,
        "costo_twilio": {
            "mensual_actual": round(costo_mensual_actual, 2),
            "ahorro_potencial_mensual": round(ahorro_potencial, 2),
            "costo_por_usuario_activo": round(costo_mensual_actual / activos_30d, 2) if activos_30d > 0 else 0,
        },
        "reactivacion": {
            "total_releases": total_releases,
            "total_reactivaciones": total_reactivaciones,
            "tasa_reactivacion": round(total_reactivaciones / total_releases * 100, 1) if total_releases > 0 else 0,
        },
        "pct_numeros_activos": round(activos_30d / con_numero * 100, 1) if con_numero > 0 else 0,
    }
