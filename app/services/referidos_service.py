"""Servicio de Referidos y Códigos de Descuento.

Programa de referidos: invita amigo → 1 mes gratis para ambos.
Códigos de descuento: porcentaje, monto fijo, o meses gratis.

Flujo referido:
1. Usuario genera su link de referido (tiene código único)
2. Amigo se registra usando el link/código
3. Cuando el amigo paga su primer mes → ambos reciben 1 mes gratis
4. Se extiende plan_expira en 30 días para ambos

Métricas clave:
- Referral rate (% usuarios que invitan)
- Conversión referido → pago
- CAC savings vs referidos
"""
import logging
import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database import (
    Usuario, Referido, CodigoDescuento, DescuentoAplicado,
    EstadoReferido, Suscripcion, EstadoSuscripcion,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# GENERACIÓN DE CÓDIGOS
# ═══════════════════════════════════════════════════════════

def _generar_codigo_referido(longitud: int = 8) -> str:
    """Genera código alfanumérico único tipo DORA-XXXX."""
    chars = string.ascii_uppercase + string.digits
    sufijo = ''.join(secrets.choice(chars) for _ in range(longitud))
    return f"DORA-{sufijo}"


def _generar_codigo_descuento(prefijo: str = "FILTRO", longitud: int = 6) -> str:
    """Genera código de descuento tipo FILTRO-XXXXXX."""
    chars = string.ascii_uppercase + string.digits
    sufijo = ''.join(secrets.choice(chars) for _ in range(longitud))
    return f"{prefijo}-{sufijo}"


# ═══════════════════════════════════════════════════════════
# REFERIDOS
# ═══════════════════════════════════════════════════════════

def obtener_o_crear_codigo_usuario(db: Session, usuario: Usuario) -> str:
    """Obtiene o crea el código de referido personal del usuario."""
    if usuario.codigo_referido:
        return usuario.codigo_referido

    # Generar código único
    for _ in range(10):
        codigo = _generar_codigo_referido()
        existente = db.query(Usuario).filter(Usuario.codigo_referido == codigo).first()
        if not existente:
            usuario.codigo_referido = codigo
            db.commit()
            return codigo

    raise Exception("No se pudo generar código único después de 10 intentos")


def obtener_link_referido(db: Session, usuario: Usuario, base_url: str) -> dict:
    """Genera el link completo de referido del usuario."""
    codigo = obtener_o_crear_codigo_usuario(db, usuario)
    return {
        "codigo": codigo,
        "link": f"{base_url}/registro?ref={codigo}",
        "link_corto": f"{base_url}/r/{codigo}",
        "total_referidos": db.query(Referido).filter(
            Referido.referidor_id == usuario.id,
            Referido.estado == EstadoReferido.CONVERTIDO.value,
        ).count(),
        "referidos_pendientes": db.query(Referido).filter(
            Referido.referidor_id == usuario.id,
            Referido.estado.in_([EstadoReferido.PENDIENTE.value, EstadoReferido.REGISTRADO.value]),
        ).count(),
    }


def registrar_referido(db: Session, nuevo_usuario: Usuario, codigo_referido: str) -> Optional[Referido]:
    """Registra que un nuevo usuario fue referido por alguien.

    Se llama durante el registro cuando viene con ?ref=CODIGO.
    """
    # Buscar quién tiene ese código
    referidor = db.query(Usuario).filter(Usuario.codigo_referido == codigo_referido).first()
    if not referidor:
        logger.warning(f"Código de referido '{codigo_referido}' no encontrado")
        return None

    if referidor.id == nuevo_usuario.id:
        logger.warning("No puedes referirte a ti mismo")
        return None

    # Verificar que no exista ya este referido
    existente = db.query(Referido).filter(
        Referido.referidor_id == referidor.id,
        Referido.referido_id == nuevo_usuario.id,
    ).first()
    if existente:
        return existente

    referido = Referido(
        referidor_id=referidor.id,
        referido_id=nuevo_usuario.id,
        email_invitado=nuevo_usuario.email,
        codigo=_generar_codigo_referido(6),
        estado=EstadoReferido.REGISTRADO.value,
    )
    nuevo_usuario.referido_por_id = referidor.id
    db.add(referido)
    db.commit()

    logger.info(f"Referido registrado: {nuevo_usuario.email} invitado por {referidor.email}")
    return referido


def convertir_referido(db: Session, usuario_que_pago: Usuario) -> bool:
    """Convierte un referido cuando el invitado paga su primera suscripción.

    → Ambos (referidor + referido) reciben 1 mes gratis.
    Se extiende plan_expira en 30 días.

    Returns:
        True si se aplicó el beneficio, False si no aplica.
    """
    # Buscar si este usuario fue referido
    referido = db.query(Referido).filter(
        Referido.referido_id == usuario_que_pago.id,
        Referido.estado == EstadoReferido.REGISTRADO.value,
    ).first()

    if not referido:
        return False

    # Marcar como convertido
    referido.estado = EstadoReferido.CONVERTIDO.value
    referido.convertido_en = datetime.now(timezone.utc)

    # Aplicar 1 mes gratis al REFERIDO (quien fue invitado)
    if not referido.mes_gratis_aplicado_referido:
        _extender_plan(usuario_que_pago, dias=30)
        referido.mes_gratis_aplicado_referido = True
        logger.info(f"1 mes gratis aplicado a referido: {usuario_que_pago.email}")

    # Aplicar 1 mes gratis al REFERIDOR (quien invitó)
    referidor = db.query(Usuario).filter(Usuario.id == referido.referidor_id).first()
    if referidor and not referido.mes_gratis_aplicado_referidor:
        _extender_plan(referidor, dias=30)
        referido.mes_gratis_aplicado_referidor = True
        logger.info(f"1 mes gratis aplicado a referidor: {referidor.email}")

    db.commit()
    return True


def _extender_plan(usuario: Usuario, dias: int = 30):
    """Extiende la fecha de expiración del plan del usuario."""
    ahora = datetime.now(timezone.utc)
    base = usuario.plan_expira if usuario.plan_expira and usuario.plan_expira > ahora else ahora
    usuario.plan_expira = base + timedelta(days=dias)


def obtener_stats_referidos(db: Session, usuario: Usuario) -> dict:
    """Estadísticas del programa de referidos para un usuario."""
    total = db.query(Referido).filter(Referido.referidor_id == usuario.id).count()
    convertidos = db.query(Referido).filter(
        Referido.referidor_id == usuario.id,
        Referido.estado == EstadoReferido.CONVERTIDO.value,
    ).count()
    pendientes = db.query(Referido).filter(
        Referido.referidor_id == usuario.id,
        Referido.estado.in_([EstadoReferido.PENDIENTE.value, EstadoReferido.REGISTRADO.value]),
    ).count()

    return {
        "total_invitados": total,
        "convertidos": convertidos,
        "pendientes": pendientes,
        "meses_ganados": convertidos,  # 1 mes por cada conversión
        "tasa_conversion": round(convertidos / total * 100, 1) if total > 0 else 0,
    }


# ═══════════════════════════════════════════════════════════
# CÓDIGOS DE DESCUENTO
# ═══════════════════════════════════════════════════════════

def crear_codigo_descuento(
    db: Session,
    tipo: str = "porcentaje",
    valor: float = 50,
    meses_gratis: int = 0,
    plan_aplicable: Optional[str] = None,
    usos_maximos: int = 0,
    descripcion: str = "",
    dias_validez: int = 30,
    prefijo: str = "FILTRO",
) -> CodigoDescuento:
    """Crea un nuevo código de descuento.

    Tipos:
    - "porcentaje": valor = % descuento (ej: 50 = 50% off)
    - "monto_fijo": valor = monto en USD a descontar
    - "mes_gratis": meses_gratis = N meses gratis
    """
    codigo = CodigoDescuento(
        codigo=_generar_codigo_descuento(prefijo),
        descripcion=descripcion,
        tipo=tipo,
        valor=valor,
        meses_gratis=meses_gratis,
        plan_aplicable=plan_aplicable,
        usos_maximos=usos_maximos,
        fecha_fin=datetime.now(timezone.utc) + timedelta(days=dias_validez) if dias_validez > 0 else None,
    )
    db.add(codigo)
    db.commit()
    db.refresh(codigo)
    logger.info(f"Código descuento creado: {codigo.codigo} ({tipo} = {valor})")
    return codigo


def validar_codigo_descuento(
    db: Session, codigo_str: str, plan: str = None, usuario: Usuario = None,
) -> Optional[dict]:
    """Valida un código de descuento y retorna info del descuento.

    Para códigos personalizados (DORA50-{UID}-*), verifica que el usuario sea el dueño.

    Returns:
        dict con detalles del descuento o None si es inválido.
    """
    codigo = db.query(CodigoDescuento).filter(
        CodigoDescuento.codigo == codigo_str.upper().strip(),
        CodigoDescuento.activo == True,
    ).first()

    if not codigo:
        return None

    ahora = datetime.now(timezone.utc)

    # Verificar vigencia
    if codigo.fecha_fin and codigo.fecha_fin < ahora:
        return None

    # Verificar usos
    if codigo.usos_maximos > 0 and codigo.usos_actuales >= codigo.usos_maximos:
        return None

    # Verificar plan aplicable
    if codigo.plan_aplicable and plan and codigo.plan_aplicable != plan:
        return None

    # Códigos personalizados DORA50-{UID}-* solo válidos para su dueño
    if codigo.codigo.startswith("DORA50-") and "-" in codigo.codigo[7:]:
        if usuario:
            uid_en_codigo = codigo.codigo.split("-")[1].lower()
            if not usuario.uid.lower().startswith(uid_en_codigo.lower()):
                return None
        # Sin usuario, retornamos el info pero marcamos como personal
        return {
            "id": codigo.id,
            "codigo": codigo.codigo,
            "tipo": codigo.tipo,
            "valor": codigo.valor,
            "meses_gratis": codigo.meses_gratis,
            "descripcion": codigo.descripcion,
            "personal": True,
        }

    return {
        "id": codigo.id,
        "codigo": codigo.codigo,
        "tipo": codigo.tipo,
        "valor": codigo.valor,
        "meses_gratis": codigo.meses_gratis,
        "descripcion": codigo.descripcion,
    }


def crear_codigo_descuento_usuario(
    db: Session,
    usuario: Usuario,
    tipo: str = "porcentaje",
    valor: float = 50,
    descripcion: str = "50% off primer mes - oferta personalizada",
    dias_validez: int = 2,
) -> CodigoDescuento:
    """Crea un código de descuento ÚNICO vinculado a un usuario específico.

    El código incluye parte del UID del usuario para que sea intransferible.
    Solo puede ser usado una vez, por el usuario al que fue asignado.

    Args:
        db: Sesión de DB
        usuario: Usuario al que se le asigna el código
        tipo: Tipo de descuento
        valor: Valor del descuento
        descripcion: Descripción interna
        dias_validez: Días antes de que expire (default 2 = 48 horas)

    Returns:
        CodigoDescuento creado
    """
    # Generar código con uid del usuario (intransferible)
    uid_corto = usuario.uid[:6].upper()
    sufijo = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    codigo_str = f"DORA50-{uid_corto}-{sufijo}"

    # Verificar que no le hayamos creado uno antes
    existente = db.query(CodigoDescuento).filter(
        CodigoDescuento.codigo.like(f"DORA50-{uid_corto}-%"),
        CodigoDescuento.activo == True,
    ).first()
    if existente:
        return existente

    codigo = CodigoDescuento(
        codigo=codigo_str,
        descripcion=f"{descripcion} [usuario: {usuario.uid}]",
        tipo=tipo,
        valor=valor,
        usos_maximos=1,  # Solo un uso
        plan_aplicable=None,  # Cualquier plan
        fecha_fin=datetime.now(timezone.utc) + timedelta(days=dias_validez),
    )
    db.add(codigo)
    db.commit()
    db.refresh(codigo)
    logger.info(f"Código descuento personal creado: {codigo.codigo} para {usuario.email}")
    return codigo


def aplicar_codigo_descuento(
    db: Session,
    usuario: Usuario,
    codigo_str: str,
    monto_original: float,
    plan: str = None,
) -> Optional[dict]:
    """Aplica un código de descuento a una compra.

    Returns:
        dict con monto_final y detalles, o None si código inválido.
    """
    info = validar_codigo_descuento(db, codigo_str, plan)
    if not info:
        return None

    codigo = db.query(CodigoDescuento).filter(CodigoDescuento.id == info["id"]).first()

    # Códigos personalizados DORA50-{UID}- solo los puede usar su dueño
    if codigo.codigo.startswith("DORA50-") and "-" in codigo.codigo[7:]:
        uid_en_codigo = codigo.codigo.split("-")[1].lower()
        if not usuario.uid.lower().startswith(uid_en_codigo.lower()):
            logger.warning(
                f"Código {codigo.codigo} rechazado: pertenece a otro usuario "
                f"(esperado uid={uid_en_codigo}, recibido uid={usuario.uid[:6]})"
            )
            return None

    monto_descuento = 0.0
    monto_final = monto_original
    meses_gratis = 0

    if codigo.tipo == "porcentaje":
        monto_descuento = monto_original * (codigo.valor / 100)
        monto_final = monto_original - monto_descuento
    elif codigo.tipo == "monto_fijo":
        monto_descuento = min(codigo.valor, monto_original)
        monto_final = monto_original - monto_descuento
    elif codigo.tipo == "mes_gratis":
        meses_gratis = codigo.meses_gratis
        _extender_plan(usuario, dias=meses_gratis * 30)

    # Registrar uso
    aplicado = DescuentoAplicado(
        usuario_id=usuario.id,
        codigo_descuento_id=codigo.id,
        monto_descuento=monto_descuento,
    )
    db.add(aplicado)
    codigo.usos_actuales += 1
    db.commit()

    logger.info(f"Descuento {codigo.codigo} aplicado a {usuario.email}: "
                f"${monto_original} → ${monto_final} (ahorro: ${monto_descuento})")

    return {
        "codigo": codigo.codigo,
        "monto_original": monto_original,
        "monto_descuento": round(monto_descuento, 2),
        "monto_final": round(max(monto_final, 0), 2),
        "meses_gratis": meses_gratis,
    }
