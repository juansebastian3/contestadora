#!/usr/bin/env python
"""
Script de diagnóstico para identificar problemas con el registro de usuarios.
Ejecutar con: python diagnostico_registro.py
"""
import os
import sys
from pathlib import Path

# Agregar el proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.database import SessionLocal, Usuario, engine, Base
from app.models.schemas import RegistroRequest
from app.core.auth import _hash_password, _verify_password, create_access_token
from sqlalchemy import inspect, text
from datetime import datetime, timezone, timedelta

def check_database():
    """Verifica la conexión a la base de datos."""
    print("\n" + "="*60)
    print("1️⃣  VERIFICACIÓN DE BASE DE DATOS")
    print("="*60)

    try:
        with engine.connect() as conn:
            print("✅ Conexión a DB exitosa")

        inspector = inspect(engine)

        # Verificar tabla usuarios
        if "usuarios" not in inspector.get_table_names():
            print("❌ Tabla 'usuarios' NO existe")
            print("   Creándola...")
            Base.metadata.create_all(bind=engine)
            print("✅ Tabla creada")
        else:
            print("✅ Tabla 'usuarios' existe")

        # Contar usuarios
        db = SessionLocal()
        count = db.query(Usuario).count()
        print(f"📊 Usuarios en la DB: {count}")

        # Listar últimos usuarios
        if count > 0:
            usuarios = db.query(Usuario).order_by(Usuario.creado.desc()).limit(3).all()
            print("📋 Últimos 3 usuarios:")
            for u in usuarios:
                print(f"   • {u.nombre} ({u.email}) - {u.creado}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_password_hash():
    """Prueba el hash de contraseñas."""
    print("\n" + "="*60)
    print("2️⃣  VERIFICACIÓN DE HASH DE CONTRASEÑAS")
    print("="*60)

    try:
        pwd = "test123456"
        hashed = _hash_password(pwd)
        verified = _verify_password(pwd, hashed)

        print(f"✅ Password original: {pwd}")
        print(f"✅ Password hasheado: {hashed[:50]}...")
        print(f"✅ Verificación: {verified}")
        return True
    except Exception as e:
        print(f"❌ Error en hash: {e}")
        return False

def test_registro():
    """Prueba crear un usuario."""
    print("\n" + "="*60)
    print("3️⃣  PRUEBA DE REGISTRO")
    print("="*60)

    db = SessionLocal()
    try:
        # Generar datos únicos
        import uuid
        uid = str(uuid.uuid4())[:8]
        email = f"test_{uid}@example.com"
        telefono = f"+56987654{uid[-3:]}"

        print(f"📝 Intentando crear usuario:")
        print(f"   Email: {email}")
        print(f"   Teléfono: {telefono}")

        # Verificar que no existan
        if db.query(Usuario).filter(Usuario.email == email).first():
            print("⚠️  Email ya existe, usando otro")
            email = f"test_new_{uid}@example.com"

        if db.query(Usuario).filter(Usuario.telefono == telefono).first():
            print("⚠️  Teléfono ya existe, usando otro")
            telefono = f"+5699876543{uid[-2:]}"

        # Crear
        nuevo = Usuario(
            nombre="Test User",
            email=email,
            telefono=telefono,
            password_hash=_hash_password("password123"),
            plan="free",
            trial_expira=datetime.now(timezone.utc) + timedelta(days=7),
            trial_usado=False,
            modo_filtrado="desconocidos",
            voz_tipo="polly",
            voz_polly_id="Polly.Mia",
            nombre_asistente="Dora",
        )

        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)

        print(f"✅ Usuario creado exitosamente:")
        print(f"   ID: {nuevo.id}")
        print(f"   UID: {nuevo.uid}")
        print(f"   Email: {nuevo.email}")

        # Verificar que se pueda leer
        usuario_leido = db.query(Usuario).filter(Usuario.uid == nuevo.uid).first()
        if usuario_leido:
            print(f"✅ Usuario verificado en DB")
        else:
            print(f"❌ Usuario no se puede leer de la DB")
            return False

        # Generar token
        token = create_access_token(nuevo.uid)
        print(f"✅ Token generado: {token[:50]}...")

        return True

    except Exception as e:
        print(f"❌ Error en registro: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def check_env():
    """Verifica variables de entorno."""
    print("\n" + "="*60)
    print("4️⃣  VARIABLES DE ENTORNO")
    print("="*60)

    from app.core.config import settings

    print(f"🔐 DATABASE_URL: {settings.DATABASE_URL}")
    print(f"🔐 JWT_SECRET: {'*' * 20} (configurado)")
    print(f"📡 BASE_URL: {settings.BASE_URL}")
    print(f"🎯 APP_PORT: {settings.APP_PORT}")

def main():
    print("\n" + "🔧" * 30)
    print("DIAGNÓSTICO: SISTEMA DE REGISTRO DE USUARIOS")
    print("🔧" * 30)

    results = {
        "Base de datos": check_database(),
        "Hash de contraseñas": test_password_hash(),
        "Registro de usuario": test_registro(),
    }

    check_env()

    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)

    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check}")

    all_pass = all(results.values())

    if all_pass:
        print("\n✅ ¡TODO FUNCIONA CORRECTAMENTE!")
        print("\nSi aún tienes problemas en la web, verifica:")
        print("  1. El servidor está corriendo: uvicorn app.main:app --reload")
        print("  2. Usa el formato de teléfono correcto: +XXXXXXXXXXXX")
        print("  3. Revisa los logs del servidor para mensajes de error")
    else:
        print("\n❌ Hay problemas en el sistema")
        print("Revisa los errores arriba para saber qué arreglar")

if __name__ == "__main__":
    main()
