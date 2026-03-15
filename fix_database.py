#!/usr/bin/env python
"""
Script para REPARAR la base de datos SQLite.
Este script elimina la BD vieja y crea una nueva con el schema correcto.

⚠️  ADVERTENCIA: Esto eliminará todos los datos existentes en SQLite local.
    Si necesitas preservar datos, primero haz backup del archivo .db
"""
import os
import sys
from pathlib import Path

# Agregar el proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.database import engine, Base, SessionLocal, Usuario, Llamada, seed_voces_y_planes
from sqlalchemy import text

def reset_database():
    """Elimina todas las tablas y las recrea desde cero."""
    print("\n" + "="*60)
    print("🗑️  ELIMINANDO TABLAS EXISTENTES")
    print("="*60)

    try:
        # Eliminar todas las tablas
        Base.metadata.drop_all(bind=engine)
        print("✅ Tablas eliminadas")
    except Exception as e:
        print(f"⚠️  Error al eliminar: {e}")

    print("\n" + "="*60)
    print("🏗️  CREANDO TABLAS NUEVAS")
    print("="*60)

    try:
        # Crear todas las tablas desde el modelo
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas correctamente")
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        return False

    print("\n" + "="*60)
    print("🌱 INICIALIZANDO DATOS")
    print("="*60)

    db = SessionLocal()
    try:
        seed_voces_y_planes(db)
        print("✅ Voces y planes inicializados")
    except Exception as e:
        print(f"❌ Error en seed: {e}")
        return False
    finally:
        db.close()

    return True

def verify_schema():
    """Verifica que el schema esté correcto."""
    print("\n" + "="*60)
    print("✔️  VERIFICANDO SCHEMA")
    print("="*60)

    from sqlalchemy import inspect

    inspector = inspect(engine)
    columnas = inspector.get_columns('usuarios')
    columnas_nombres = [col['name'] for col in columnas]

    print(f"📊 Columnas en tabla usuarios ({len(columnas_nombres)}):")
    for col in columnas_nombres:
        print(f"   ✓ {col}")

    # Verificar que existan las columnas críticas
    columnas_criticas = [
        'id', 'uid', 'email', 'telefono', 'password_hash',
        'plan', 'nombre_asistente', 'telefono_twilio', 'twilio_phone_sid'
    ]

    faltan = [col for col in columnas_criticas if col not in columnas_nombres]
    if faltan:
        print(f"\n❌ Faltan columnas críticas: {faltan}")
        return False
    else:
        print(f"\n✅ Todas las columnas críticas presentes")
        return True

def test_insert():
    """Prueba insertar un usuario."""
    print("\n" + "="*60)
    print("🧪 PRUEBA DE INSERCIÓN")
    print("="*60)

    from datetime import datetime, timezone, timedelta
    from app.core.auth import _hash_password
    import uuid

    db = SessionLocal()
    try:
        nuevo = Usuario(
            nombre="Test Usuario",
            email="test@example.com",
            telefono="+56987654321",
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

        print(f"✅ Usuario creado: {nuevo.uid}")
        print(f"   Email: {nuevo.email}")
        print(f"   ID: {nuevo.id}")

        # Verificar que se puede leer
        usuario_leido = db.query(Usuario).filter(Usuario.uid == nuevo.uid).first()
        if usuario_leido:
            print(f"✅ Usuario se puede leer correctamente")
            return True
        else:
            print(f"❌ No se puede leer el usuario")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    print("\n" + "🔧" * 30)
    print("REPARACIÓN DE BASE DE DATOS SQLite")
    print("🔧" * 30)

    print("\n⚠️  ADVERTENCIA:")
    print("   Este script ELIMINARÁ todos los datos en SQLite local")
    print("   y creará una nueva base de datos con el schema correcto.")
    print("\n   Si tienes datos importantes, presiona Ctrl+C ahora.")

    try:
        input("\nPresiona ENTER para continuar (o Ctrl+C para cancelar)...")
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada")
        sys.exit(1)

    # Ejecutar reparación
    if not reset_database():
        print("\n❌ Error en reset")
        sys.exit(1)

    # Verificar schema
    if not verify_schema():
        print("\n❌ Error en schema")
        sys.exit(1)

    # Probar inserción
    if not test_insert():
        print("\n❌ Error en prueba")
        sys.exit(1)

    print("\n" + "="*60)
    print("✅ ÉXITO - Base de datos reparada correctamente")
    print("="*60)
    print("\n📝 Pasos siguientes:")
    print("   1. Reinicia tu servidor FastAPI")
    print("   2. Prueba crear una nueva cuenta en la web")
    print("   3. Asegúrate de usar teléfono con formato +XXXXXXXXXXXX")
    print("\n")

if __name__ == "__main__":
    main()
