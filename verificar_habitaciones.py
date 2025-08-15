#!/usr/bin/env python
"""
Script para verificar el estado de las habitaciones
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_management.settings')
django.setup()

from hotel.models import Habitacion, TipoHabitacion

def verificar_habitaciones():
    print("🏨 VERIFICACIÓN DE HABITACIONES")
    print("=" * 50)
    
    # Contar habitaciones por estado
    total = Habitacion.objects.count()
    disponibles = Habitacion.objects.filter(estado='disponible').count()
    ocupadas = Habitacion.objects.filter(estado='ocupada').count()
    mantenimiento = Habitacion.objects.filter(estado='mantenimiento').count()
    limpieza = Habitacion.objects.filter(estado='limpieza').count()
    
    print(f"📊 ESTADÍSTICAS:")
    print(f"   Total de habitaciones: {total}")
    print(f"   🟢 Disponibles: {disponibles}")
    print(f"   🔴 Ocupadas: {ocupadas}")
    print(f"   🟡 Mantenimiento: {mantenimiento}")
    print(f"   🔵 Limpieza: {limpieza}")
    print()
    
    # Mostrar detalles de todas las habitaciones
    print("🏠 DETALLE DE HABITACIONES:")
    print("-" * 50)
    
    for habitacion in Habitacion.objects.all().order_by('numero'):
        estado_emoji = {
            'disponible': '🟢',
            'ocupada': '🔴',
            'mantenimiento': '🟡',
            'limpieza': '🔵'
        }.get(habitacion.estado, '⚪')
        
        print(f"   {estado_emoji} Habitación {habitacion.numero} ({habitacion.tipo.nombre}) - {habitacion.get_estado_display()}")
    
    print()
    print("📋 TIPOS DE HABITACIÓN:")
    print("-" * 30)
    for tipo in TipoHabitacion.objects.all():
        count = Habitacion.objects.filter(tipo=tipo).count()
        print(f"   💰 {tipo.nombre}: ${tipo.precio_por_noche}/noche ({count} habitaciones)")

if __name__ == '__main__':
    verificar_habitaciones()