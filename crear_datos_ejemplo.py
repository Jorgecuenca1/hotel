#!/usr/bin/env python
"""
Script para crear datos de ejemplo en el sistema hotelero
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_management.settings')
django.setup()

from hotel.models import TipoHabitacion, Habitacion, Cliente, CategoriaProducto, Producto
from django.contrib.auth.models import User

def crear_datos_ejemplo():
    print("Creando datos de ejemplo...")
    
    # Crear tipos de habitación
    tipos_habitacion = [
        {'nombre': 'Individual', 'precio_por_noche': 80.00, 'capacidad_personas': 1, 'descripcion': 'Habitación individual con cama sencilla'},
        {'nombre': 'Doble', 'precio_por_noche': 120.00, 'capacidad_personas': 2, 'descripcion': 'Habitación doble con cama matrimonial'},
        {'nombre': 'Suite', 'precio_por_noche': 200.00, 'capacidad_personas': 4, 'descripcion': 'Suite de lujo con sala y dormitorio separados'},
        {'nombre': 'Familiar', 'precio_por_noche': 150.00, 'capacidad_personas': 6, 'descripcion': 'Habitación familiar con literas y cama matrimonial'},
    ]
    
    print("Creando tipos de habitación...")
    for tipo_data in tipos_habitacion:
        tipo, created = TipoHabitacion.objects.get_or_create(
            nombre=tipo_data['nombre'],
            defaults=tipo_data
        )
        if created:
            print(f"- Creado tipo: {tipo.nombre}")
    
    # Crear habitaciones
    print("Creando habitaciones...")
    tipos = list(TipoHabitacion.objects.all())
    
    for piso in range(1, 4):  # 3 pisos
        for num in range(1, 6):  # 5 habitaciones por piso
            numero = f"{piso}0{num}"
            tipo = tipos[num % len(tipos)]  # Distribuir tipos
            
            habitacion, created = Habitacion.objects.get_or_create(
                numero=numero,
                defaults={
                    'tipo': tipo,
                    'piso': piso,
                    'estado': 'disponible',
                    'descripcion': f'Habitación {numero} en el piso {piso}'
                }
            )
            if created:
                print(f"- Creada habitación: {habitacion.numero}")
    
    # Crear categorías de productos
    categorias_productos = [
        {'nombre': 'Bebidas', 'descripcion': 'Bebidas alcohólicas y no alcohólicas'},
        {'nombre': 'Snacks', 'descripcion': 'Aperitivos y botanas'},
        {'nombre': 'Comidas', 'descripcion': 'Platos principales y comidas completas'},
        {'nombre': 'Amenidades', 'descripcion': 'Productos de aseo y comodidad'},
    ]
    
    print("Creando categorías de productos...")
    for cat_data in categorias_productos:
        categoria, created = CategoriaProducto.objects.get_or_create(
            nombre=cat_data['nombre'],
            defaults=cat_data
        )
        if created:
            print(f"- Creada categoría: {categoria.nombre}")
    
    # Crear productos
    productos_ejemplo = [
        # Bebidas
        {'codigo': 'BEB001', 'nombre': 'Agua Natural 500ml', 'categoria': 'Bebidas', 'precio': 2.50, 'stock_actual': 100, 'stock_minimo': 20},
        {'codigo': 'BEB002', 'nombre': 'Refresco de Cola 355ml', 'categoria': 'Bebidas', 'precio': 3.00, 'stock_actual': 80, 'stock_minimo': 15},
        {'codigo': 'BEB003', 'nombre': 'Cerveza Nacional', 'categoria': 'Bebidas', 'precio': 4.50, 'stock_actual': 60, 'stock_minimo': 12},
        {'codigo': 'BEB004', 'nombre': 'Jugo de Naranja 350ml', 'categoria': 'Bebidas', 'precio': 3.50, 'stock_actual': 40, 'stock_minimo': 10},
        
        # Snacks
        {'codigo': 'SNK001', 'nombre': 'Papas Fritas Originales', 'categoria': 'Snacks', 'precio': 2.00, 'stock_actual': 50, 'stock_minimo': 15},
        {'codigo': 'SNK002', 'nombre': 'Cacahuates Salados', 'categoria': 'Snacks', 'precio': 1.50, 'stock_actual': 30, 'stock_minimo': 10},
        {'codigo': 'SNK003', 'nombre': 'Chocolate con Almendras', 'categoria': 'Snacks', 'precio': 3.00, 'stock_actual': 25, 'stock_minimo': 8},
        
        # Comidas
        {'codigo': 'COM001', 'nombre': 'Sandwich Club', 'categoria': 'Comidas', 'precio': 8.50, 'stock_actual': 15, 'stock_minimo': 5},
        {'codigo': 'COM002', 'nombre': 'Ensalada César', 'categoria': 'Comidas', 'precio': 7.00, 'stock_actual': 20, 'stock_minimo': 5},
        {'codigo': 'COM003', 'nombre': 'Pizza Personal', 'categoria': 'Comidas', 'precio': 12.00, 'stock_actual': 10, 'stock_minimo': 3},
        
        # Amenidades
        {'codigo': 'AME001', 'nombre': 'Kit de Aseo Personal', 'categoria': 'Amenidades', 'precio': 5.00, 'stock_actual': 40, 'stock_minimo': 10},
        {'codigo': 'AME002', 'nombre': 'Toalla Extra', 'categoria': 'Amenidades', 'precio': 3.00, 'stock_actual': 30, 'stock_minimo': 8},
        {'codigo': 'AME003', 'nombre': 'Almohada Adicional', 'categoria': 'Amenidades', 'precio': 4.00, 'stock_actual': 20, 'stock_minimo': 5},
    ]
    
    print("Creando productos...")
    categorias_dict = {cat.nombre: cat for cat in CategoriaProducto.objects.all()}
    
    for prod_data in productos_ejemplo:
        categoria = categorias_dict[prod_data['categoria']]
        producto, created = Producto.objects.get_or_create(
            codigo=prod_data['codigo'],
            defaults={
                'nombre': prod_data['nombre'],
                'categoria': categoria,
                'precio': prod_data['precio'],
                'stock_actual': prod_data['stock_actual'],
                'stock_minimo': prod_data['stock_minimo'],
                'activo': True
            }
        )
        if created:
            print(f"- Creado producto: {producto.nombre}")
    
    # Crear algunos clientes de ejemplo
    clientes_ejemplo = [
        {
            'nombre': 'Juan Carlos',
            'apellido': 'Pérez García',
            'tipo_documento': 'cedula',
            'numero_documento': '12345678',
            'telefono': '555-0101',
            'email': 'juan.perez@email.com',
            'direccion': 'Calle Principal #123, Colonia Centro'
        },
        {
            'nombre': 'María Elena',
            'apellido': 'González López',
            'tipo_documento': 'cedula',
            'numero_documento': '87654321',
            'telefono': '555-0102',
            'email': 'maria.gonzalez@email.com',
            'direccion': 'Avenida Reforma #456, Colonia Norte'
        },
        {
            'nombre': 'Carlos Roberto',
            'apellido': 'Martínez Silva',
            'tipo_documento': 'pasaporte',
            'numero_documento': 'P123456789',
            'telefono': '555-0103',
            'email': 'carlos.martinez@email.com',
            'direccion': 'Boulevard del Sol #789, Zona Dorada'
        },
    ]
    
    print("Creando clientes de ejemplo...")
    for cliente_data in clientes_ejemplo:
        cliente, created = Cliente.objects.get_or_create(
            numero_documento=cliente_data['numero_documento'],
            defaults=cliente_data
        )
        if created:
            print(f"- Creado cliente: {cliente.nombre_completo}")
    
    print("\n¡Datos de ejemplo creados exitosamente!")
    print("\nResumen:")
    print(f"- Tipos de habitación: {TipoHabitacion.objects.count()}")
    print(f"- Habitaciones: {Habitacion.objects.count()}")
    print(f"- Categorías de productos: {CategoriaProducto.objects.count()}")
    print(f"- Productos: {Producto.objects.count()}")
    print(f"- Clientes: {Cliente.objects.count()}")

if __name__ == '__main__':
    crear_datos_ejemplo()