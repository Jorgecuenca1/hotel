#!/usr/bin/env python
"""
Script para probar las funcionalidades de consumos y pagos
"""
import requests
import json

def probar_apis():
    url_base = "http://127.0.0.1:8000"
    
    print("🧪 PROBANDO FUNCIONALIDADES DE RESERVA")
    print("=" * 50)
    
    try:
        # 1. Probar API de productos
        print("1. 📦 Probando API de productos...")
        response = requests.get(f"{url_base}/api/productos/")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            productos = response.json()
            print(f"   ✅ Productos encontrados: {len(productos.get('productos', []))}")
            if productos.get('productos'):
                primer_producto = productos['productos'][0]
                print(f"   📦 Ejemplo: {primer_producto['codigo']} - {primer_producto['nombre']}")
        else:
            print(f"   ❌ Error: {response.status_code}")
        
        print()
        
        # 2. Probar endpoint de registrar consumo
        print("2. 🛒 Probando endpoint de registrar consumo...")
        data_consumo = {
            'reserva_id': 1,  # Asumiendo que existe reserva con ID 1
            'producto_id': 1,  # Primer producto
            'cantidad': 2
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': 'test-token'
        }
        
        response = requests.post(
            f"{url_base}/consumos/registrar/",
            data=json.dumps(data_consumo),
            headers=headers
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Respuesta: {result}")
        else:
            print(f"   ⚠️  Endpoint disponible pero podría necesitar CSRF válido")
        
        print()
        
        # 3. Probar endpoint de registrar pago
        print("3. 💳 Probando endpoint de registrar pago...")
        data_pago = {
            'reserva_id': 1,
            'monto': 100.00,
            'metodo_pago': 'efectivo',
            'tipo_pago': 'abono'
        }
        
        response = requests.post(
            f"{url_base}/pagos/registrar/",
            data=json.dumps(data_pago),
            headers=headers
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Respuesta: {result}")
        else:
            print(f"   ⚠️  Endpoint disponible pero podría necesitar CSRF válido")
        
        print()
        
        # 4. Verificar que existe una reserva
        print("4. 📅 Verificando reservas...")
        response = requests.get(f"{url_base}/reservas/")
        print(f"   Status página reservas: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Página de reservas accesible")
            # Intentar acceder a detalle de reserva 1
            response_detalle = requests.get(f"{url_base}/reservas/1/")
            print(f"   Status detalle reserva 1: {response_detalle.status_code}")
            
            if response_detalle.status_code == 200:
                print("   ✅ Detalle de reserva accesible - ¡Los botones deberían funcionar!")
            else:
                print("   ⚠️  Necesitas crear una reserva primero")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor.")
        print("   Asegúrate de que el servidor Django esté ejecutándose:")
        print("   python manage.py runserver")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == '__main__':
    probar_apis()