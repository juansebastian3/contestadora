"""Servicio de filtrado de llamadas - Decide si Sofía contesta o no.

MODOS DE FILTRADO:
─────────────────────────────────────────────────────────────────
  DESCONOCIDOS (gratis):
    - Si el número está en contactos_conocidos → pasa directo (no filtra)
    - Si el número es desconocido → Sofía contesta y filtra

  LUNA (pro/premium):
    - Sofía contesta TODAS las llamadas, sin excepción
    - Ideal para cuando estás durmiendo, en reunión, o no quieres que nadie moleste
    - Puede tener horario programado (ej: 23:00 a 07:00 automático)

  DESACTIVADO:
    - Sofía no contesta nada, las llamadas pasan normal

LÓGICA DE HORARIO LUNA:
─────────────────────────────────────────────────────────────────
  Si el usuario tiene horario_luna_inicio y horario_luna_fin configurados,
  el modo luna se activa automáticamente en ese rango, aunque el modo
  seleccionado sea "desconocidos". Esto permite:
  - De día: solo filtrar desconocidos
  - De noche: filtrar todo automáticamente

INTEGRACIÓN CALENDARIO (Pro/Premium):
─────────────────────────────────────────────────────────────────
  Si el usuario tiene un calendario conectado y activado:
  - Revisa Google Calendar y/o Outlook Calendar
  - Si hay una reunión activa → activa la contestadora automáticamente
  - El modo calendario se combina con luna y desconocidos
  Prioridad: bloqueado > calendario > luna horario > modo base
"""
import logging
from datetime import datetime, timezone, timedelta

from app.models.database import (
    SessionLocal, Usuario, NumeroBloqueado,
    ModoFiltrado, PlanTipo
)

logger = logging.getLogger(__name__)


class ResultadoFiltrado:
    """Resultado de la decisión de filtrado."""

    def __init__(
        self,
        debe_filtrar: bool,
        motivo: str,
        modo_activo: str,
        numero_conocido: bool = False,
        numero_bloqueado: bool = False,
        evento_calendario: dict = None,
    ):
        self.debe_filtrar = debe_filtrar
        self.motivo = motivo
        self.modo_activo = modo_activo
        self.numero_conocido = numero_conocido
        self.numero_bloqueado = numero_bloqueado
        self.evento_calendario = evento_calendario


def decidir_filtrado(usuario: Usuario, numero_origen: str) -> ResultadoFiltrado:
    """Decide si Sofía debe contestar esta llamada.

    Args:
        usuario: El usuario dueño del número
        numero_origen: Número del llamante (formato +56...)

    Returns:
        ResultadoFiltrado con la decisión y motivos
    """
    # 1. ¿Número bloqueado? → Rechazar siempre
    db = SessionLocal()
    try:
        bloqueado = db.query(NumeroBloqueado).filter(
            NumeroBloqueado.usuario_id == usuario.id,
            NumeroBloqueado.numero == numero_origen,
        ).first()

        if bloqueado:
            return ResultadoFiltrado(
                debe_filtrar=True,
                motivo=f"Número bloqueado: {bloqueado.razon or 'manual'}",
                modo_activo="bloqueado",
                numero_bloqueado=True,
            )
    finally:
        db.close()

    # 2. ¿Es número conocido?
    contactos = usuario.contactos_conocidos or []
    # Normalizar números para comparación
    numero_limpio = numero_origen.replace(" ", "").replace("-", "")
    es_conocido = any(
        c.replace(" ", "").replace("-", "") == numero_limpio
        for c in contactos
    )

    # 3. ¿Está en reunión según calendario? (Pro/Premium)
    evento_calendario = None
    if usuario.plan in (PlanTipo.PRO.value, PlanTipo.PREMIUM.value):
        evento_calendario = _verificar_calendario(usuario)

    # 4. Determinar modo activo (incluyendo horario luna y calendario)
    modo = _obtener_modo_activo(usuario, evento_calendario)

    # 5. Aplicar lógica según modo
    if modo == ModoFiltrado.DESACTIVADO.value:
        return ResultadoFiltrado(
            debe_filtrar=False,
            motivo="Filtrado desactivado",
            modo_activo=modo,
            numero_conocido=es_conocido,
        )

    if modo == ModoFiltrado.LUNA.value:
        # Verificar que el usuario tenga plan que permita luna
        if usuario.plan not in (PlanTipo.PRO.value, PlanTipo.PREMIUM.value):
            # Fallback a modo desconocidos si no tiene plan
            modo = ModoFiltrado.DESCONOCIDOS.value
        else:
            motivo = "Modo Luna activo: filtrando todas las llamadas"
            if evento_calendario:
                motivo = f"En reunión '{evento_calendario['titulo']}' → contestadora activa"
            return ResultadoFiltrado(
                debe_filtrar=True,
                motivo=motivo,
                modo_activo=modo,
                numero_conocido=es_conocido,
                evento_calendario=evento_calendario,
            )

    if modo == ModoFiltrado.DESCONOCIDOS.value:
        if es_conocido:
            return ResultadoFiltrado(
                debe_filtrar=False,
                motivo="Número en lista de contactos conocidos",
                modo_activo=modo,
                numero_conocido=True,
            )
        else:
            return ResultadoFiltrado(
                debe_filtrar=True,
                motivo="Número desconocido → Sofía atiende",
                modo_activo=modo,
                numero_conocido=False,
            )

    # Default: filtrar por seguridad
    return ResultadoFiltrado(
        debe_filtrar=True,
        motivo="Modo no reconocido, filtrando por seguridad",
        modo_activo=modo,
    )


def _verificar_calendario(usuario: Usuario) -> dict | None:
    """Revisa si el usuario tiene una reunión activa en sus calendarios conectados."""
    try:
        from app.services.calendario_service import usuario_en_reunion
        return usuario_en_reunion(usuario)
    except Exception as e:
        logger.error(f"Error verificando calendario: {e}")
        return None


def _obtener_modo_activo(usuario: Usuario, evento_calendario: dict = None) -> str:
    """Determina el modo de filtrado activo considerando horarios y calendario.

    Prioridad:
    1. Si está en reunión (calendario) → modo luna (contestadora atiende todo)
    2. Si está en horario luna → modo luna
    3. Modo base del usuario
    """
    modo_base = usuario.modo_filtrado or ModoFiltrado.DESCONOCIDOS.value

    # Si ya está en modo luna manual, respetar
    if modo_base == ModoFiltrado.LUNA.value:
        return modo_base

    # Si está desactivado, respetar
    if modo_base == ModoFiltrado.DESACTIVADO.value:
        return modo_base

    # ¿Está en reunión según calendario? → Activar luna automático
    if evento_calendario:
        logger.info(f"📅 Calendario activa contestadora para {usuario.nombre}")
        return ModoFiltrado.LUNA.value

    # Verificar horario automático de luna
    if usuario.horario_luna_inicio and usuario.horario_luna_fin:
        if _esta_en_horario_luna(usuario.horario_luna_inicio, usuario.horario_luna_fin):
            logger.info(f"Horario luna automático activo para {usuario.nombre}")
            return ModoFiltrado.LUNA.value

    return modo_base


def _esta_en_horario_luna(inicio_str: str, fin_str: str) -> bool:
    """Verifica si la hora actual está dentro del rango de luna.

    Maneja rangos que cruzan medianoche (ej: 23:00 a 07:00).

    Args:
        inicio_str: Hora de inicio "HH:MM" (ej: "23:00")
        fin_str: Hora de fin "HH:MM" (ej: "07:00")
    """
    try:
        # Usar hora local de Chile (UTC-3 / UTC-4)
        # En producción: usar pytz con la timezone del usuario
        ahora = datetime.now(timezone(timedelta(hours=-3)))
        hora_actual = ahora.hour * 60 + ahora.minute

        h_ini, m_ini = map(int, inicio_str.split(":"))
        h_fin, m_fin = map(int, fin_str.split(":"))
        inicio = h_ini * 60 + m_ini
        fin = h_fin * 60 + m_fin

        if inicio <= fin:
            # Rango normal (ej: 09:00 a 17:00)
            return inicio <= hora_actual <= fin
        else:
            # Rango que cruza medianoche (ej: 23:00 a 07:00)
            return hora_actual >= inicio or hora_actual <= fin

    except (ValueError, AttributeError):
        logger.error(f"Error parseando horario luna: {inicio_str}-{fin_str}")
        return False
