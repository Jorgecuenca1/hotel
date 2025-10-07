from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import PerfilUsuario


def requiere_rol(roles_permitidos):
    """
    Decorador que requiere que el usuario tenga uno de los roles especificados.

    Args:
        roles_permitidos: lista de roles que pueden acceder (ej: ['administrador', 'recepcionista'])
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            try:
                perfil = PerfilUsuario.objects.get(user=request.user)
                if perfil.activo and perfil.rol in roles_permitidos:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'No tienes permisos para acceder a esta sección.')
                    return redirect('hotel:dashboard')
            except PerfilUsuario.DoesNotExist:
                messages.error(request, 'Tu perfil de usuario no está configurado. Contacta al administrador.')
                return redirect('hotel:dashboard')
        return wrapper
    return decorator


def solo_administrador(view_func):
    """Decorador que solo permite acceso a administradores"""
    return requiere_rol(['administrador'])(view_func)


def administrador_o_recepcionista(view_func):
    """Decorador que permite acceso a administradores y recepcionistas"""
    return requiere_rol(['administrador', 'recepcionista'])(view_func)


def solo_recepcionista(view_func):
    """Decorador que solo permite acceso a recepcionistas"""
    return requiere_rol(['recepcionista'])(view_func)


def verificar_permisos_accion(accion):
    """
    Decorador que verifica permisos para acciones específicas.

    Permisos del recepcionista:
    - Puede agregar: hospedadas, clientes, empresas, reservas, inventario faltante
    - NO puede: editar, eliminar, ver reportes financieros, configuración
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            try:
                perfil = PerfilUsuario.objects.get(user=request.user)

                if not perfil.activo:
                    messages.error(request, 'Tu cuenta está inactiva.')
                    return redirect('hotel:dashboard')

                # Administradores tienen acceso completo
                if perfil.es_administrador():
                    return view_func(request, *args, **kwargs)

                # Recepcionistas solo pueden realizar ciertas acciones
                if perfil.es_recepcionista():
                    acciones_permitidas_recepcionista = [
                        'agregar_hospedada',
                        'agregar_cliente',
                        'agregar_empresa',
                        'agregar_reserva',
                        'agregar_inventario_faltante',
                        'ver_hospedadas',
                        'ver_clientes',
                        'ver_empresas',
                        'ver_reservas',
                        'ver_productos',
                        'cambiar_estado_habitacion'
                    ]

                    if accion in acciones_permitidas_recepcionista:
                        return view_func(request, *args, **kwargs)
                    else:
                        messages.error(request, 'No tienes permisos para realizar esta acción.')
                        return redirect('hotel:dashboard')

                messages.error(request, 'Rol de usuario no válido.')
                return redirect('hotel:dashboard')

            except PerfilUsuario.DoesNotExist:
                messages.error(request, 'Tu perfil de usuario no está configurado. Contacta al administrador.')
                return redirect('hotel:dashboard')
        return wrapper
    return decorator