#!/usr/bin/env python
"""
Script para probar el endpoint /auth/registro directamente
sin necesidad de usar la página web.
"""
import requests
import json
import sys
from pathlib import Path

# Agregar proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

def test_registro():
    """Prueba registrar un usuario vía HTTP."""
    
    # URL del servidor (ajusta si es diferente)
    BASE_URL = "http://localhost:8000"
    
    # Datos de prueba
    data = {
        "nombre": "Juan Test",
        "email": "juan.test@example.com",
        "telefono": "+56987654321",
        "password": "MiPassword123"
    }
    
    print("\n" + "="*60)
    print("🧪 PRUEBA DE REGISTRO VÍA API")
    print("="*60)
    print(f"\n📡 URL: {BASE_URL}/auth/registro")
    print(f"📝 Datos:")
    for k, v in data.items():
        print(f"   {k}: {v}")
    
    try:
        print(f"\n⏳ Enviando request...")
        response = requests.post(
            f"{BASE_URL}/auth/registro",
            json=data,
            timeout=10
        )
        
        print(f"\n✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            resultado = response.json()
            print(f"\n✅ ¡ÉXITO! Usuario registrado correctamente")
            print(f"\n📊 Respuesta:")
            print(f"   access_token: {resultado['access_token'][:50]}...")
            print(f"   refresh_token: {resultado['refresh_token'][:50]}...")
            print(f"   token_type: {resultado['token_type']}")
            print(f"   expires_in: {resultado['expires_in']} segundos")
            print(f"\n👤 Perfil del usuario:")
            perfil = resultado['perfil']
            print(f"   UID: {perfil['uid']}")
            print(f"   Nombre: {perfil['nombre']}")
            print(f"   Email: {perfil['email']}")
            print(f"   Plan: {perfil['plan']}")
            return True
            
        else:
            print(f"\n❌ Error HTTP {response.status_code}")
            print(f"📋 Response:")
            try:
                print(json.dumps(response.json(), indent=2))
            except:
                print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: No se puede conectar a {BASE_URL}")
        print(f"   ¿El servidor está corriendo?")
        print(f"   Ejecuta: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_registro()
