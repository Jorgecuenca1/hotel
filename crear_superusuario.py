#!/usr/bin/env python
"""
Script para crear un superusuario automáticamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_management.settings')
django.setup()

from django.contrib.auth.models import User

def crear_superusuario():
    # Verificar si ya existe un superusuario
    if User.objects.filter(is_superuser=True).exists():
        print("Ya existe un superusuario en el sistema.")
        superuser = User.objects.filter(is_superuser=True).first()
        print(f"Superusuario existente: {superuser.username}")
        return
    
    # Crear superusuario
    username = 'admin'
    email = 'admin@hotel.com'
    password = 'admin123'
    
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    
    print("✅ Superusuario creado exitosamente!")
    print(f"Usuario: {username}")
    print(f"Email: {email}")
    print(f"Contraseña: {password}")
    print("\n🔐 Accede al panel de administración en: http://127.0.0.1:8000/admin/")

if __name__ == '__main__':
    crear_superusuario()