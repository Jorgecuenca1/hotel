#!/usr/bin/env python
"""
Script para probar el cambio de estado de habitaciones
"""
import requests
import json

def probar_cambio_estado():
    url_base = "http://127.0.0.1:8000"
    
    # Primero obtener las habitaciones para ver cuáles están disponibles
    try:
        response = requests.get(f"{url_base}/habitaciones/")
        print(f"✅ Página de habitaciones accesible: {response.status_code}")
        
        # Probar cambio de estado (habitación ID 1 a 'ocupada')
        habitacion_id = 1
        nuevo_estado = "ocupada"
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': 'test-token'  # Para prueba
        }
        
        data = {
            'estado': nuevo_estado
        }
        
        response = requests.post(
            f"{url_base}/habitaciones/{habitacion_id}/cambiar-estado/",
            data=json.dumps(data),
            headers=headers
        )
        
        print(f"🧪 Prueba de cambio de estado:")
        print(f"   - Habitación ID: {habitacion_id}")
        print(f"   - Nuevo estado: {nuevo_estado}")
        print(f"   - Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   - Respuesta: {result}")
            if result.get('success'):
                print("✅ ¡Cambio de estado exitoso!")
            else:
                print(f"❌ Error: {result.get('error', 'Error desconocido')}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"   Contenido: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor.")
        print("   Asegúrate de que el servidor Django esté ejecutándose.")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == '__main__':
    print("🏨 Probando funcionalidad de cambio de estado de habitaciones...")
    print("=" * 60)
    probar_cambio_estado()