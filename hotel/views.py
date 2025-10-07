from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator
import json
import csv
from datetime import datetime, date
from decimal import Decimal

from .models import (
    TipoHabitacion, Habitacion, Cliente, Hospedada, Empresa, Reserva,
    CategoriaProducto, Producto, ConsumoHabitacion, Pago, Factura, AjustePrecio,
    ElementoInventario, InventarioHabitacion, TipoServicio, ServicioHospedada, FaltanteCheckout,
    PerfilUsuario
)
from .decorators import (
    solo_administrador, administrador_o_recepcionista, verificar_permisos_accion
)


@administrador_o_recepcionista
def dashboard(request):
    """Vista principal del dashboard"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Tu perfil no está configurado.')
        return redirect('hotel:login')

    context = {
        'total_habitaciones': Habitacion.objects.count(),
        'habitaciones_disponibles': Habitacion.objects.filter(estado='disponible').count(),
        'habitaciones_ocupadas': Habitacion.objects.filter(estado='ocupada').count(),
        'hospedadas_hoy': Hospedada.objects.filter(fecha_entrada=date.today()).count(),
        'reservas_pendientes': Reserva.objects.filter(estado='pendiente').count(),
        'productos_bajo_stock': Producto.objects.filter(stock_actual__lte=F('stock_minimo')).count(),
        'ingresos_mes': Pago.objects.filter(
            fecha_pago__month=timezone.now().month,
            fecha_pago__year=timezone.now().year
        ).aggregate(total=Sum('monto'))['total'] or 0,
        'perfil': perfil,
    }
    return render(request, 'hotel/dashboard.html', context)


# === HABITACIONES ===
def habitaciones_list(request):
    """Lista de habitaciones con filtros"""
    habitaciones = Habitacion.objects.select_related('tipo').all()
    
    # Filtros
    estado = request.GET.get('estado')
    tipo_id = request.GET.get('tipo')
    piso = request.GET.get('piso')
    
    if estado:
        habitaciones = habitaciones.filter(estado=estado)
    if tipo_id:
        habitaciones = habitaciones.filter(tipo_id=tipo_id)
    if piso:
        habitaciones = habitaciones.filter(piso=piso)
    
    context = {
        'habitaciones': habitaciones,
        'tipos_habitacion': TipoHabitacion.objects.all(),
        'pisos': Habitacion.objects.values_list('piso', flat=True).distinct().order_by('piso'),
        'filtros': {'estado': estado, 'tipo_id': tipo_id, 'piso': piso}
    }
    return render(request, 'hotel/habitaciones.html', context)


def habitacion_create(request):
    """Crear nueva habitación"""
    if request.method == 'POST':
        numero = request.POST.get('numero')
        tipo_id = request.POST.get('tipo_id')
        piso = request.POST.get('piso')
        descripcion = request.POST.get('descripcion', '')
        
        if numero and tipo_id and piso:
            try:
                # Verificar que no exista una habitación con el mismo número
                if Habitacion.objects.filter(numero=numero).exists():
                    messages.error(request, f'Ya existe una habitación con el número {numero}')
                else:
                    tipo = get_object_or_404(TipoHabitacion, id=tipo_id)
                    Habitacion.objects.create(
                        numero=numero,
                        tipo=tipo,
                        piso=int(piso),
                        descripcion=descripcion,
                        estado='disponible'
                    )
                    messages.success(request, f'Habitación {numero} creada exitosamente')
                    return redirect('hotel:habitaciones')
            except (ValueError, TipoHabitacion.DoesNotExist):
                messages.error(request, 'Error al crear la habitación. Verifique los datos.')
        else:
            messages.error(request, 'Por favor complete todos los campos obligatorios.')
    
    context = {
        'tipos_habitacion': TipoHabitacion.objects.all(),
        'pisos_disponibles': range(1, 11),  # Pisos del 1 al 10
    }
    return render(request, 'hotel/habitacion_create.html', context)


def habitacion_edit(request, habitacion_id):
    """Editar habitación existente"""
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    
    if request.method == 'POST':
        numero = request.POST.get('numero')
        tipo_id = request.POST.get('tipo_id')
        piso = request.POST.get('piso')
        descripcion = request.POST.get('descripcion', '')
        estado = request.POST.get('estado')
        
        if numero and tipo_id and piso and estado:
            try:
                # Verificar que no exista otra habitación con el mismo número
                habitacion_existente = Habitacion.objects.filter(numero=numero).exclude(id=habitacion.id)
                if habitacion_existente.exists():
                    messages.error(request, f'Ya existe otra habitación con el número {numero}')
                else:
                    tipo = get_object_or_404(TipoHabitacion, id=tipo_id)
                    habitacion.numero = numero
                    habitacion.tipo = tipo
                    habitacion.piso = int(piso)
                    habitacion.descripcion = descripcion
                    habitacion.estado = estado
                    habitacion.save()
                    messages.success(request, f'Habitación {numero} actualizada exitosamente')
                    return redirect('hotel:habitaciones')
            except (ValueError, TipoHabitacion.DoesNotExist):
                messages.error(request, 'Error al actualizar la habitación. Verifique los datos.')
        else:
            messages.error(request, 'Por favor complete todos los campos obligatorios.')
    
    # Calcular reservas activas
    reservas_activas = Reserva.objects.filter(
        habitacion=habitacion,
        estado__in=['confirmada', 'en_curso']
    ).count()
    
    context = {
        'habitacion': habitacion,
        'tipos_habitacion': TipoHabitacion.objects.all(),
        'pisos_disponibles': range(1, 11),
        'estados_habitacion': Habitacion.ESTADOS,
        'reservas_activas': reservas_activas,
    }
    return render(request, 'hotel/habitacion_edit.html', context)


def habitacion_delete(request, habitacion_id):
    """Eliminar habitación"""
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    
    if request.method == 'POST':
        # Verificar si la habitación tiene reservas activas
        reservas_activas = Reserva.objects.filter(
            habitacion=habitacion,
            estado__in=['confirmada', 'en_curso']
        )
        
        if reservas_activas.exists():
            messages.error(request, f'No se puede eliminar la habitación {habitacion.numero}. Tiene reservas activas.')
        else:
            numero = habitacion.numero
            habitacion.delete()
            messages.success(request, f'Habitación {numero} eliminada exitosamente')
        
        return redirect('hotel:habitaciones')
    
    # Obtener información para mostrar en la confirmación
    reservas_totales = Reserva.objects.filter(habitacion=habitacion).count()
    reservas_activas = Reserva.objects.filter(
        habitacion=habitacion,
        estado__in=['confirmada', 'en_curso']
    ).count()
    
    context = {
        'habitacion': habitacion,
        'reservas_totales': reservas_totales,
        'reservas_activas': reservas_activas,
    }
    return render(request, 'hotel/habitacion_delete.html', context)


# === TIPOS DE HABITACIÓN ===
def tipos_habitacion_list(request):
    """Lista de tipos de habitación"""
    tipos = TipoHabitacion.objects.all().order_by('nombre')
    context = {
        'tipos_habitacion': tipos,
    }
    return render(request, 'hotel/tipos_habitacion.html', context)


def tipo_habitacion_create(request):
    """Crear nuevo tipo de habitación"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        precio_por_noche = request.POST.get('precio_por_noche')
        capacidad_personas = request.POST.get('capacidad_personas')
        
        if nombre and precio_por_noche and capacidad_personas:
            try:
                # Verificar que no exista un tipo con el mismo nombre
                if TipoHabitacion.objects.filter(nombre__iexact=nombre).exists():
                    messages.error(request, f'Ya existe un tipo de habitación llamado "{nombre}"')
                else:
                    TipoHabitacion.objects.create(
                        nombre=nombre,
                        descripcion=descripcion,
                        precio_por_noche=float(precio_por_noche),
                        capacidad_personas=int(capacidad_personas)
                    )
                    messages.success(request, f'Tipo de habitación "{nombre}" creado exitosamente')
                    return redirect('hotel:tipos_habitacion')
            except (ValueError, TypeError):
                messages.error(request, 'Error en los datos. Verifique precio y capacidad.')
        else:
            messages.error(request, 'Por favor complete todos los campos obligatorios.')
    
    return render(request, 'hotel/tipo_habitacion_create.html')


def tipo_habitacion_edit(request, tipo_id):
    """Editar tipo de habitación existente"""
    tipo = get_object_or_404(TipoHabitacion, id=tipo_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        precio_por_noche = request.POST.get('precio_por_noche')
        capacidad_personas = request.POST.get('capacidad_personas')
        
        if nombre and precio_por_noche and capacidad_personas:
            try:
                # Verificar que no exista otro tipo con el mismo nombre
                tipo_existente = TipoHabitacion.objects.filter(nombre__iexact=nombre).exclude(id=tipo.id)
                if tipo_existente.exists():
                    messages.error(request, f'Ya existe otro tipo de habitación llamado "{nombre}"')
                else:
                    tipo.nombre = nombre
                    tipo.descripcion = descripcion
                    tipo.precio_por_noche = float(precio_por_noche)
                    tipo.capacidad_personas = int(capacidad_personas)
                    tipo.save()
                    messages.success(request, f'Tipo de habitación "{nombre}" actualizado exitosamente')
                    return redirect('hotel:tipos_habitacion')
            except (ValueError, TypeError):
                messages.error(request, 'Error en los datos. Verifique precio y capacidad.')
        else:
            messages.error(request, 'Por favor complete todos los campos obligatorios.')
    
    context = {
        'tipo_habitacion': tipo,
    }
    return render(request, 'hotel/tipo_habitacion_edit.html', context)


def tipo_habitacion_delete(request, tipo_id):
    """Eliminar tipo de habitación"""
    tipo = get_object_or_404(TipoHabitacion, id=tipo_id)
    
    if request.method == 'POST':
        # Verificar si el tipo tiene habitaciones asociadas
        habitaciones_asociadas = Habitacion.objects.filter(tipo=tipo)
        
        if habitaciones_asociadas.exists():
            messages.error(request, f'No se puede eliminar el tipo "{tipo.nombre}". Tiene {habitaciones_asociadas.count()} habitación(es) asociada(s).')
        else:
            nombre = tipo.nombre
            tipo.delete()
            messages.success(request, f'Tipo de habitación "{nombre}" eliminado exitosamente')
        
        return redirect('hotel:tipos_habitacion')
    
    # Obtener información para mostrar en la confirmación
    habitaciones_count = Habitacion.objects.filter(tipo=tipo).count()
    
    context = {
        'tipo_habitacion': tipo,
        'habitaciones_count': habitaciones_count,
    }
    return render(request, 'hotel/tipo_habitacion_delete.html', context)


@csrf_exempt
def cambiar_estado_habitacion(request, habitacion_id):
    """Cambiar estado de habitación via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')
            
            # Validar que el estado sea válido
            estados_validos = ['disponible', 'ocupada', 'mantenimiento', 'limpieza']
            if nuevo_estado not in estados_validos:
                return JsonResponse({
                    'success': False, 
                    'error': 'Estado no válido'
                })
            
            habitacion = get_object_or_404(Habitacion, id=habitacion_id)
            estado_anterior = habitacion.estado
            habitacion.estado = nuevo_estado
            habitacion.save()
            
            return JsonResponse({
                'success': True,
                'mensaje': f'Estado cambiado de {estado_anterior} a {nuevo_estado}',
                'nuevo_estado': nuevo_estado
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Datos JSON inválidos'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })


# === CLIENTES ===
def clientes_list(request):
    """Lista de clientes"""
    query = request.GET.get('q', '')
    clientes = Cliente.objects.all()
    
    if query:
        clientes = clientes.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(numero_documento__icontains=query) |
            Q(email__icontains=query)
        )
    
    paginator = Paginator(clientes, 20)
    page = request.GET.get('page')
    clientes = paginator.get_page(page)
    
    return render(request, 'hotel/clientes.html', {'clientes': clientes, 'query': query})


@csrf_exempt
def cliente_create(request):
    """Crear nuevo cliente via AJAX"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            cliente = Cliente.objects.create(
                nombre=data['nombre'],
                apellido=data['apellido'],
                tipo_documento=data['tipo_documento'],
                numero_documento=data['numero_documento'],
                telefono=data.get('telefono', ''),
                email=data.get('email', ''),
                direccion=data.get('direccion', ''),
                fecha_nacimiento=data.get('fecha_nacimiento') or None
            )
            return JsonResponse({
                'success': True,
                'cliente': {
                    'id': cliente.id,
                    'nombre_completo': cliente.nombre_completo,
                    'numero_documento': cliente.numero_documento
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})


# === EMPRESAS ===
def empresas_list(request):
    """Lista de empresas"""
    query = request.GET.get('q', '')
    empresas = Empresa.objects.all()
    
    if query:
        empresas = empresas.filter(
            Q(nombre__icontains=query) |
            Q(rfc__icontains=query) |
            Q(email__icontains=query)
        )
    
    paginator = Paginator(empresas, 20)
    page = request.GET.get('page')
    empresas = paginator.get_page(page)
    
    return render(request, 'hotel/empresas.html', {'empresas': empresas, 'query': query})


def empresa_create(request):
    """Crear nueva empresa"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        rfc = request.POST.get('rfc')
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')
        email = request.POST.get('email')
        contacto = request.POST.get('contacto', '')
        
        if nombre and rfc and direccion and telefono and email:
            try:
                empresa = Empresa.objects.create(
                    nombre=nombre,
                    rfc=rfc,
                    direccion=direccion,
                    telefono=telefono,
                    email=email,
                    contacto=contacto
                )
                messages.success(request, f'Empresa {nombre} creada exitosamente')
                return redirect('hotel:empresas')
            except Exception as e:
                messages.error(request, f'Error al crear la empresa: {str(e)}')
        else:
            messages.error(request, 'Por favor complete todos los campos obligatorios')
    
    return render(request, 'hotel/empresa_create.html')


def empresa_edit(request, empresa_id):
    """Editar empresa"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    if request.method == 'POST':
        empresa.nombre = request.POST.get('nombre')
        empresa.rfc = request.POST.get('rfc')
        empresa.direccion = request.POST.get('direccion')
        empresa.telefono = request.POST.get('telefono')
        empresa.email = request.POST.get('email')
        empresa.contacto = request.POST.get('contacto', '')
        empresa.activa = request.POST.get('activa') == 'on'
        
        try:
            empresa.save()
            messages.success(request, f'Empresa {empresa.nombre} actualizada exitosamente')
            return redirect('hotel:empresas')
        except Exception as e:
            messages.error(request, f'Error al actualizar la empresa: {str(e)}')
    
    return render(request, 'hotel/empresa_edit.html', {'empresa': empresa})


def empresa_delete(request, empresa_id):
    """Eliminar empresa"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    if request.method == 'POST':
        # Verificar si hay clientes asociados
        clientes_asociados = Cliente.objects.filter(empresa=empresa).count()
        
        if clientes_asociados > 0:
            messages.error(request, f'No se puede eliminar la empresa. Tiene {clientes_asociados} cliente(s) asociado(s).')
        else:
            nombre = empresa.nombre
            empresa.delete()
            messages.success(request, f'Empresa {nombre} eliminada exitosamente')
        
        return redirect('hotel:empresas')
    
    clientes_count = Cliente.objects.filter(empresa=empresa).count()
    context = {
        'empresa': empresa,
        'clientes_count': clientes_count
    }
    return render(request, 'hotel/empresa_delete.html', context)


@csrf_exempt
def api_buscar_empresa(request):
    """Buscar empresa via AJAX"""
    query = request.GET.get('q', '')
    empresas = Empresa.objects.filter(activa=True)

    if query:
        empresas = empresas.filter(
            Q(nombre__icontains=query) |
            Q(rfc__icontains=query)
        )[:10]

    data = [{
        'id': e.id,
        'nombre': e.nombre,
        'rfc': e.rfc,
        'text': f"{e.nombre} - {e.rfc}"
    } for e in empresas]

    return JsonResponse({'success': True, 'empresas': data})


@csrf_exempt
def api_crear_empresa(request):
    """Crear nueva empresa via AJAX"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            empresa = Empresa.objects.create(
                nombre=data['nombre'],
                rfc=data['rfc'],
                direccion=data['direccion'],
                telefono=data['telefono'],
                email=data['email'],
                contacto=data.get('contacto', '')
            )
            return JsonResponse({
                'success': True,
                'empresa': {
                    'id': empresa.id,
                    'nombre': empresa.nombre,
                    'rfc': empresa.rfc,
                    'email': empresa.email
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})


# === HOSPEDADAS ===
def hospedadas_list(request):
    """Lista de hospedadas"""
    hospedadas = Hospedada.objects.select_related('cliente', 'habitacion').all()
    
    # Filtros
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if estado:
        hospedadas = hospedadas.filter(estado=estado)
    if fecha_desde:
        hospedadas = hospedadas.filter(fecha_entrada__gte=fecha_desde)
    if fecha_hasta:
        hospedadas = hospedadas.filter(fecha_salida__lte=fecha_hasta)
    
    paginator = Paginator(hospedadas, 20)
    page = request.GET.get('page')
    hospedadas = paginator.get_page(page)
    
    context = {
        'hospedadas': hospedadas,
        'filtros': {'estado': estado, 'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta}
    }
    return render(request, 'hotel/hospedadas.html', context)


@csrf_exempt
def hospedada_create(request):
    """Crear nueva hospedada"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            cliente = get_object_or_404(Cliente, id=data['cliente_id'])
            habitacion = get_object_or_404(Habitacion, id=data['habitacion_id'])
            
            # Verificar disponibilidad
            fecha_entrada = datetime.strptime(data['fecha_entrada'], '%Y-%m-%d').date()
            fecha_salida = None
            
            # Manejar fecha de salida (puede ser indefinida)
            if data.get('fecha_salida') and data['fecha_salida'].strip():
                fecha_salida = datetime.strptime(data['fecha_salida'], '%Y-%m-%d').date()
                
                # Verificar conflictos solo si hay fecha de salida definida
                conflictos = Hospedada.objects.filter(
                    habitacion=habitacion,
                    estado__in=['confirmada', 'en_curso'],
                    fecha_entrada__lt=fecha_salida,
                    fecha_salida__gt=fecha_entrada
                ).exclude(fecha_salida__isnull=True)
                
                if conflictos.exists():
                    return JsonResponse({'success': False, 'error': 'Habitación no disponible en esas fechas'})
            else:
                # Para hospedadas indefinidas, verificar que no haya conflictos actuales
                conflictos_actuales = Hospedada.objects.filter(
                    habitacion=habitacion,
                    estado__in=['confirmada', 'en_curso'],
                    fecha_entrada__lte=fecha_entrada
                ).filter(
                    models.Q(fecha_salida__isnull=True) | 
                    models.Q(fecha_salida__gt=fecha_entrada)
                )
                
                if conflictos_actuales.exists():
                    return JsonResponse({'success': False, 'error': 'Habitación no disponible para hospedada indefinida'})
            
            # Obtener empresa si se proporciona
            empresa = None
            if data.get('empresa_id'):
                empresa = get_object_or_404(Empresa, id=data['empresa_id'])
            
            hospedada = Hospedada.objects.create(
                tipo_hospedada=data.get('tipo_hospedada', 'continua'),
                cliente=cliente,
                empresa=empresa,
                habitacion=habitacion,
                fecha_entrada=fecha_entrada,
                fecha_salida=fecha_salida,
                numero_huespedes=data.get('numero_huespedes', 1),
                observaciones=data.get('observaciones', ''),
                usuario_creacion=request.user if request.user.is_authenticated else None
            )
            
            # Cambiar estado de habitación si la hospedada es para hoy
            if fecha_entrada == date.today():
                habitacion.estado = 'ocupada'
                habitacion.save()
                hospedada.estado = 'en_curso'
                hospedada.save()
            
            return JsonResponse({
                'success': True,
                'hospedada': {
                    'id': hospedada.id,
                    'numero_hospedada': hospedada.numero_hospedada,
                    'precio_total': float(hospedada.precio_total or 0)
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # GET request - mostrar formulario
    context = {
        'tipos_hospedada': Hospedada.TIPOS_HOSPEDADA,
    }
    return render(request, 'hotel/hospedada_create.html', context)


def hospedada_detail(request, hospedada_id):
    """Detalle de hospedada con consumos, pagos, servicios y ajustes"""
    hospedada = get_object_or_404(Hospedada, id=hospedada_id)
    consumos = ConsumoHabitacion.objects.filter(hospedada=hospedada).select_related('producto')
    pagos = Pago.objects.filter(hospedada=hospedada)
    ajustes = AjustePrecio.objects.filter(hospedada=hospedada, activo=True)
    servicios = ServicioHospedada.objects.filter(hospedada=hospedada).select_related('tipo_servicio')
    
    total_consumos = hospedada.subtotal_consumos
    total_servicios = hospedada.subtotal_servicios
    total_pagado = sum(pago.monto for pago in pagos)
    
    # Serializar ajustes para JavaScript
    ajustes_json = []
    for ajuste in ajustes:
        ajustes_json.append({
            'id': ajuste.id,
            'tipo': ajuste.tipo,
            'concepto': ajuste.concepto,
            'monto': float(ajuste.monto),
            'porcentaje': float(ajuste.porcentaje) if ajuste.porcentaje else None,
            'es_porcentaje': ajuste.es_porcentaje,
            'monto_calculado': float(ajuste.monto_calculado),
            'fecha_creacion': ajuste.fecha_creacion.strftime('%d/%m/%Y %H:%M')
        })
    
    context = {
        'hospedada': hospedada,
        'consumos': consumos,
        'pagos': pagos,
        'ajustes': ajustes,
        'servicios': servicios,
        'ajustes_json': json.dumps(ajustes_json),
        'total_consumos': total_consumos,
        'total_servicios': total_servicios,
        'total_pagado': total_pagado,
    }
    return render(request, 'hotel/hospedada_detail.html', context)


def agregar_consumo(request, hospedada_id):
    """Página para agregar consumo a una hospedada"""
    hospedada = get_object_or_404(Hospedada, id=hospedada_id)
    
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        cantidad = request.POST.get('cantidad')
        
        if producto_id and cantidad:
            try:
                producto = get_object_or_404(Producto, id=producto_id)
                cantidad = int(cantidad)
                
                # Verificar stock disponible
                if producto.stock_actual >= cantidad:
                    # Crear el consumo
                    ConsumoHabitacion.objects.create(
                        hospedada=hospedada,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio,
                        fecha_consumo=timezone.now()
                    )
                    
                    # Actualizar stock
                    producto.stock_actual -= cantidad
                    producto.save()
                    
                    messages.success(request, f'Consumo registrado: {cantidad}x {producto.nombre}')
                    return redirect('hotel:hospedada_detail', hospedada_id=hospedada.id)
                else:
                    messages.error(request, f'Stock insuficiente. Solo hay {producto.stock_actual} unidades disponibles.')
            except (ValueError, Producto.DoesNotExist):
                messages.error(request, 'Error al procesar el consumo. Verifique los datos.')
        else:
            messages.error(request, 'Por favor complete todos los campos.')
    
    # Obtener productos disponibles
    productos = Producto.objects.filter(activo=True, stock_actual__gt=0).order_by('codigo')
    
    # Ensure we provide safe context for any potential reserva references
    try:
        # Check if this hospedada was created from a reserva (reverse relationship)
        related_reserva = getattr(hospedada, 'reserva_origen', None)
    except:
        related_reserva = None

    context = {
        'hospedada': hospedada,
        'productos': productos,
        'reserva': related_reserva,  # Safe reserva reference - will be None if no related reserva
    }
    return render(request, 'hotel/agregar_consumo.html', context)


def agregar_pago(request, hospedada_id):
    """Página para agregar pago a una hospedada"""
    hospedada = get_object_or_404(Hospedada, id=hospedada_id)
    
    # Calcular saldo pendiente usando los nuevos métodos que incluyen ajustes
    pagos = Pago.objects.filter(hospedada=hospedada)
    total_pagado = sum(pago.monto for pago in pagos)
    total_hospedada = hospedada.total_con_ajustes  # Incluye habitación + consumos + ajustes
    saldo_pendiente = hospedada.saldo_pendiente  # Usa el método que incluye ajustes
    
    if request.method == 'POST':
        monto = request.POST.get('monto')
        metodo_pago = request.POST.get('metodo_pago')
        tipo_pago = request.POST.get('tipo_pago')
        pagado_por = request.POST.get('pagado_por', 'cliente')
        referencia = request.POST.get('referencia', '')
        observaciones = request.POST.get('observaciones', '')
        
        if monto and metodo_pago:
            try:
                monto = float(monto)
                
                # Validar que el monto no sea mayor al saldo pendiente
                if monto <= saldo_pendiente:
                    # Crear el pago
                    Pago.objects.create(
                        hospedada=hospedada,
                        monto=monto,
                        metodo_pago=metodo_pago,
                        tipo_pago=tipo_pago or 'abono',
                        pagado_por=pagado_por,
                        referencia=referencia,
                        observaciones=observaciones,
                        fecha_pago=timezone.now()
                    )
                    
                    messages.success(request, f'Pago registrado: ${monto:.2f} por {dict(Pago.METODOS_PAGO)[metodo_pago]}')
                    return redirect('hotel:hospedada_detail', hospedada_id=hospedada.id)
                else:
                    messages.error(request, f'El monto no puede ser mayor al saldo pendiente (${saldo_pendiente:.2f})')
            except ValueError:
                messages.error(request, 'El monto debe ser un número válido.')
        else:
            messages.error(request, 'Por favor complete todos los campos obligatorios.')
    
    context = {
        'hospedada': hospedada,
        'saldo_pendiente': saldo_pendiente,
        'total_hospedada': total_hospedada,
        'metodos_pago': Pago.METODOS_PAGO,
        'tipos_pago': Pago.TIPOS_PAGO,
    }
    return render(request, 'hotel/agregar_pago.html', context)


# === INVENTARIO ===
def inventario_list(request):
    """Lista de productos del inventario"""
    productos = Producto.objects.select_related('categoria').filter(activo=True)
    
    categoria_id = request.GET.get('categoria')
    query = request.GET.get('q', '')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(codigo__icontains=query)
        )
    
    context = {
        'productos': productos,
        'categorias': CategoriaProducto.objects.all(),
        'filtros': {'categoria_id': categoria_id, 'query': query}
    }
    return render(request, 'hotel/inventario.html', context)


@csrf_exempt
def registrar_consumo(request):
    """Registrar consumo en habitación"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            hospedada = get_object_or_404(Hospedada, id=data['hospedada_id'])
            producto = get_object_or_404(Producto, id=data['producto_id'])
            cantidad = int(data['cantidad'])
            
            if producto.stock_actual < cantidad:
                return JsonResponse({'success': False, 'error': 'Stock insuficiente'})
            
            consumo = ConsumoHabitacion.objects.create(
                reserva=reserva,
                producto=producto,
                cantidad=cantidad,
                usuario_registro=request.user if request.user.is_authenticated else None
            )
            
            return JsonResponse({
                'success': True,
                'consumo': {
                    'id': consumo.id,
                    'producto': producto.nombre,
                    'cantidad': cantidad,
                    'subtotal': float(consumo.subtotal)
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})


# === PAGOS ===
@csrf_exempt
def registrar_pago(request):
    """Registrar pago de reserva"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            hospedada = get_object_or_404(Hospedada, id=data['hospedada_id'])
            
            pago = Pago.objects.create(
                hospedada=reserva,
                monto=Decimal(data['monto']),
                metodo_pago=data['metodo_pago'],
                tipo_pago=data['tipo_pago'],
                pagado_por=data.get('pagado_por', 'cliente'),
                referencia=data.get('referencia', ''),
                observaciones=data.get('observaciones', ''),
                usuario_registro=request.user if request.user.is_authenticated else None
            )
            
            return JsonResponse({
                'success': True,
                'pago': {
                    'id': pago.id,
                    'numero_pago': pago.numero_pago,
                    'monto': float(pago.monto)
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})


# === FACTURACIÓN ===
def generar_factura(request, hospedada_id):
    """Generar factura para una hospedada"""
    hospedada = get_object_or_404(Hospedada, id=hospedada_id)

    # Verificar si ya existe factura
    try:
        factura = Factura.objects.get(hospedada=hospedada)
    except Factura.DoesNotExist:
        factura = Factura.objects.create(
            hospedada=hospedada,
            usuario_emision=request.user if request.user.is_authenticated else None
        )
    
    # Calcular totales y estado de pago
    pagos = Pago.objects.filter(hospedada=hospedada)
    ajustes = AjustePrecio.objects.filter(hospedada=hospedada, activo=True)
    total_pagado = sum(pago.monto for pago in pagos)
    saldo_pendiente = hospedada.saldo_pendiente
    
    # Determinar estado de pago
    if saldo_pendiente <= 0:
        estado_pago = 'pagado'
        estado_texto = 'PAGADO COMPLETAMENTE'
        estado_clase = 'success'
    elif total_pagado > 0:
        estado_pago = 'parcial'
        estado_texto = 'PAGO PARCIAL'
        estado_clase = 'warning'
    else:
        estado_pago = 'no_pagado'
        estado_texto = 'NO PAGADO'
        estado_clase = 'danger'
    
    context = {
        'factura': factura,
        'ajustes': ajustes,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo_pendiente,
        'estado_pago': estado_pago,
        'estado_texto': estado_texto,
        'estado_clase': estado_clase,
    }
    
    return render(request, 'hotel/factura.html', context)


def factura_pdf(request, factura_id):
    """Generar PDF de factura"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from io import BytesIO

    factura = get_object_or_404(Factura, id=factura_id)
    hospedada = factura.hospedada

    # Crear buffer para el PDF
    buffer = BytesIO()

    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=1  # Centrado
    )

    # Contenido del PDF
    story = []

    # Título
    title = Paragraph(f"FACTURA {factura.numero_factura}", title_style)
    story.append(title)
    story.append(Spacer(1, 20))

    # Información del hotel y cliente
    header_data = [
        ['<b>Hotel Manager</b>', '<b>FACTURA</b>'],
        ['Calle Principal #123', f'Número: {factura.numero_factura}'],
        ['Ciudad, Estado 12345', f'Fecha: {factura.fecha_emision.strftime("%d/%m/%Y")}'],
        ['Tel: (555) 123-4567', f'Hospedada: {hospedada.numero_hospedada}'],
        ['', ''],
        ['<b>CLIENTE</b>', ''],
        [f'{hospedada.cliente.nombre_completo}', ''],
        [f'Habitación: {hospedada.habitacion.numero}', ''],
    ]

    header_table = Table(header_data, colWidths=[3.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    story.append(header_table)
    story.append(Spacer(1, 20))

    # Detalle de la factura
    detalle_data = [
        ['<b>CONCEPTO</b>', '<b>SUBTOTAL</b>'],
        ['Habitación', f'${factura.subtotal_habitacion:,.2f}'],
        ['Consumos', f'${factura.subtotal_consumos:,.2f}'],
        ['Servicios', f'${hospedada.subtotal_servicios:,.2f}'],
        ['Ajustes', f'${factura.subtotal_ajustes:,.2f}'],
        ['Impuestos (IVA)', f'${factura.impuestos:,.2f}'],
        ['<b>TOTAL</b>', f'<b>${factura.total:,.2f}</b>'],
    ]

    detalle_table = Table(detalle_data, colWidths=[4*inch, 2*inch])
    detalle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))

    story.append(detalle_table)
    story.append(Spacer(1, 20))

    # Observaciones
    if factura.observaciones:
        story.append(Paragraph(f"<b>Observaciones:</b> {factura.observaciones}", styles['Normal']))

    # Generar PDF
    doc.build(story)

    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{factura.numero_factura}.pdf"'

    return response


# === RESERVAS ===
def reserva_detail(request, reserva_id):
    """Vista de detalle de una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)

    context = {
        'reserva': reserva,
    }

    return render(request, 'hotel/reserva_detail.html', context)


def reserva_convertir(request, reserva_id):
    """Convertir una reserva a hospedada"""
    reserva = get_object_or_404(Reserva, id=reserva_id)

    # Verificar que la reserva se puede convertir
    if reserva.estado == 'convertida':
        messages.error(request, 'Esta reserva ya ha sido convertida a hospedada.')
        return redirect('hotel:reserva_detail', reserva_id=reserva.id)

    if reserva.estado == 'cancelada':
        messages.error(request, 'No se puede convertir una reserva cancelada.')
        return redirect('hotel:reserva_detail', reserva_id=reserva.id)

    try:
        # Verificar si la habitación está disponible
        if reserva.habitacion.estado != 'disponible':
            messages.error(request, f'La habitación {reserva.habitacion.numero} no está disponible. Estado actual: {reserva.habitacion.get_estado_display()}')
            return redirect('hotel:reserva_detail', reserva_id=reserva.id)

        # Convertir la reserva a hospedada
        hospedada = reserva.convertir_a_hospedada(
            tipo_hospedada='continua',
            usuario=request.user if request.user.is_authenticated else None
        )

        messages.success(request, f'Reserva convertida exitosamente a hospedada {hospedada.numero_hospedada}')
        return redirect('hotel:hospedada_detail', hospedada_id=hospedada.id)

    except Exception as e:
        messages.error(request, f'Error al convertir la reserva: {str(e)}')
        return redirect('hotel:reserva_detail', reserva_id=reserva.id)


# === REPORTES Y EXPORTACIÓN ===
def exportar_contabilidad(request):
    """Exportar datos para contabilidad"""
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if not fecha_desde or not fecha_hasta:
        fecha_desde = date.today().replace(day=1)  # Primer día del mes
        fecha_hasta = date.today()
    else:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    
    # Crear archivo CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="contabilidad_{fecha_desde}_{fecha_hasta}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Tipo', 'Número', 'Cliente', 'Descripción', 'Monto', 'Método Pago'
    ])
    
    # Facturas
    facturas = Factura.objects.filter(
        fecha_emision__date__range=[fecha_desde, fecha_hasta]
    ).select_related('hospedada__cliente')

    for factura in facturas:
        writer.writerow([
            factura.fecha_emision.strftime('%Y-%m-%d'),
            'Factura',
            factura.numero_factura,
            factura.hospedada.cliente.nombre_completo,
            f'Hospedada {factura.hospedada.numero_hospedada}',
            factura.total,
            ''
        ])
    
    # Pagos
    pagos = Pago.objects.filter(
        fecha_pago__date__range=[fecha_desde, fecha_hasta]
    ).select_related('hospedada__cliente')

    for pago in pagos:
        writer.writerow([
            pago.fecha_pago.strftime('%Y-%m-%d'),
            'Pago',
            pago.numero_pago,
            pago.hospedada.cliente.nombre_completo,
            f'Pago {pago.get_tipo_pago_display()}',
            pago.monto,
            pago.get_metodo_pago_display()
        ])
    
    return response


def reportes(request):
    """Vista de reportes"""
    # Datos para gráficos y estadísticas
    clientes = Cliente.objects.all().order_by('nombre', 'apellido')
    
    context = {
        'ocupacion_hoy': Habitacion.objects.filter(estado='ocupada').count(),
        'total_habitaciones': Habitacion.objects.count(),
        'reservas_mes': Reserva.objects.filter(
            fecha_entrada_prevista__month=timezone.now().month,
            fecha_entrada_prevista__year=timezone.now().year
        ).count(),
        'ingresos_mes': Pago.objects.filter(
            fecha_pago__month=timezone.now().month,
            fecha_pago__year=timezone.now().year
        ).aggregate(total=Sum('monto'))['total'] or 0,
        'clientes': clientes,
    }
    return render(request, 'hotel/reportes.html', context)


# === REPORTES PDF ===
def reporte_todas_reservas_pdf(request):
    """Generar PDF con todas las reservas e información completa"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from io import BytesIO
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Obtener todas las reservas con información relacionada
    reservas = Reserva.objects.select_related(
        'cliente', 'habitacion__tipo'
    ).prefetch_related(
        'pago_set', 'consumohabitacion_set__producto', 'ajustes_precio'
    ).order_by('-fecha_creacion')
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    
    # Contenido del PDF
    story = []
    
    # Título
    title = Paragraph("REPORTE COMPLETO DE RESERVAS", title_style)
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Información general
    fecha_reporte = timezone.now().strftime('%d/%m/%Y %H:%M')
    info_general = Paragraph(f"<b>Fecha del reporte:</b> {fecha_reporte}<br/><b>Total de reservas:</b> {reservas.count()}", styles['Normal'])
    story.append(info_general)
    story.append(Spacer(1, 20))
    
    # Procesar cada reserva
    for reserva in reservas:
        # Información básica de la reserva
        story.append(Paragraph(f"<b>RESERVA {reserva.numero_reserva}</b>", styles['Heading2']))
        
        # Datos del cliente
        cliente_data = [
            ['<b>INFORMACIÓN DEL CLIENTE</b>', ''],
            ['Nombre completo:', reserva.cliente.nombre_completo],
            ['Documento:', f"{reserva.cliente.get_tipo_documento_display()}: {reserva.cliente.numero_documento}"],
            ['Teléfono:', reserva.cliente.telefono or 'No registrado'],
            ['Email:', reserva.cliente.email or 'No registrado'],
            ['Dirección:', reserva.cliente.direccion or 'No registrada'],
        ]
        
        cliente_table = Table(cliente_data, colWidths=[2*inch, 3*inch])
        cliente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(cliente_table)
        story.append(Spacer(1, 12))
        
        # Datos de la reserva
        fecha_salida = reserva.fecha_salida.strftime('%d/%m/%Y') if reserva.fecha_salida else 'Indefinida'
        dias_estancia = reserva.dias_estancia if reserva.fecha_salida else 'Por definir'
        
        reserva_data = [
            ['<b>INFORMACIÓN DE LA RESERVA</b>', ''],
            ['Habitación:', f"{reserva.habitacion.numero} - {reserva.habitacion.tipo.nombre}"],
            ['Fecha entrada:', reserva.fecha_entrada.strftime('%d/%m/%Y')],
            ['Fecha salida:', fecha_salida],
            ['Días de estancia:', str(dias_estancia)],
            ['Número de huéspedes:', str(reserva.numero_huespedes)],
            ['Estado:', reserva.get_estado_display()],
            ['Precio habitación:', f"${reserva.precio_total or 0:,.2f}"],
        ]
        
        reserva_table = Table(reserva_data, colWidths=[2*inch, 3*inch])
        reserva_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(reserva_table)
        story.append(Spacer(1, 12))
        
        # Consumos
        consumos = reserva.consumohabitacion_set.all()
        if consumos:
            story.append(Paragraph("<b>CONSUMOS</b>", styles['Heading3']))
            consumos_data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal', 'Fecha']]
            
            for consumo in consumos:
                consumos_data.append([
                    consumo.producto.nombre,
                    str(consumo.cantidad),
                    f"${consumo.precio_unitario:,.2f}",
                    f"${consumo.subtotal:,.2f}",
                    consumo.fecha_consumo.strftime('%d/%m/%Y')
                ])
            
            consumos_table = Table(consumos_data, colWidths=[1.5*inch, 0.8*inch, 1*inch, 1*inch, 1*inch])
            consumos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(consumos_table)
            story.append(Spacer(1, 12))
        
        # Ajustes de precio
        ajustes = reserva.ajustes_precio.filter(activo=True)
        if ajustes:
            story.append(Paragraph("<b>AJUSTES DE PRECIO</b>", styles['Heading3']))
            ajustes_data = [['Tipo', 'Concepto', 'Valor', 'Monto', 'Fecha']]
            
            for ajuste in ajustes:
                tipo_display = 'Extra' if ajuste.tipo == 'extra' else 'Descuento'
                valor_display = f"{ajuste.porcentaje}%" if ajuste.es_porcentaje else f"${ajuste.monto:,.2f}"
                
                ajustes_data.append([
                    tipo_display,
                    ajuste.concepto,
                    valor_display,
                    f"${ajuste.monto_calculado:,.2f}",
                    ajuste.fecha_creacion.strftime('%d/%m/%Y')
                ])
            
            ajustes_table = Table(ajustes_data, colWidths=[1*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
            ajustes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(ajustes_table)
            story.append(Spacer(1, 12))
        
        # Información financiera
        pagos = reserva.pago_set.all()
        total_pagado = sum(p.monto for p in pagos)
        
        financiera_data = [
            ['<b>RESUMEN FINANCIERO</b>', ''],
            ['Subtotal habitación:', f"${reserva.precio_total or 0:,.2f}"],
            ['Subtotal consumos:', f"${reserva.subtotal_consumos:,.2f}"],
            ['Subtotal ajustes:', f"${reserva.subtotal_ajustes:,.2f}"],
            ['<b>Total con ajustes:</b>', f"<b>${reserva.total_con_ajustes:,.2f}</b>"],
            ['Total pagado:', f"${total_pagado:,.2f}"],
            ['<b>Saldo pendiente:</b>', f"<b>${reserva.saldo_pendiente:,.2f}</b>"],
        ]
        
        financiera_table = Table(financiera_data, colWidths=[2*inch, 3*inch])
        financiera_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightcoral),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(financiera_table)
        story.append(Spacer(1, 12))
        
        # Pagos realizados
        if pagos:
            story.append(Paragraph("<b>HISTORIAL DE PAGOS</b>", styles['Heading3']))
            pagos_data = [['Fecha', 'Método', 'Tipo', 'Monto', 'Referencia']]
            
            for pago in pagos:
                pagos_data.append([
                    pago.fecha_pago.strftime('%d/%m/%Y'),
                    pago.get_metodo_pago_display(),
                    pago.get_tipo_pago_display(),
                    f"${pago.monto:,.2f}",
                    pago.referencia or 'N/A'
                ])
            
            pagos_table = Table(pagos_data, colWidths=[1*inch, 1.2*inch, 1*inch, 1*inch, 1.3*inch])
            pagos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightsteelblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(pagos_table)
        
        # Separador entre reservas
        story.append(Spacer(1, 30))
        story.append(Paragraph("─" * 80, styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Generar PDF
    doc.build(story)
    
    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_todas_reservas_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf"'
    
    return response


def reporte_por_cliente_pdf(request):
    """Generar PDF filtrado por cliente específico"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from io import BytesIO
    
    cliente_id = request.GET.get('cliente_id')
    if not cliente_id:
        return HttpResponse("Cliente no especificado", status=400)
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return HttpResponse("Cliente no encontrado", status=404)
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Obtener reservas del cliente
    reservas = Reserva.objects.filter(cliente=cliente).select_related(
        'habitacion__tipo'
    ).prefetch_related(
        'pago_set', 'consumohabitacion_set__producto', 'ajustes_precio'
    ).order_by('-fecha_creacion')
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    
    # Contenido del PDF
    story = []
    
    # Título
    title = Paragraph(f"REPORTE DE RESERVAS - {cliente.nombre_completo.upper()}", title_style)
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Información del cliente
    fecha_reporte = timezone.now().strftime('%d/%m/%Y %H:%M')
    info_cliente = f"""
    <b>Fecha del reporte:</b> {fecha_reporte}<br/>
    <b>Cliente:</b> {cliente.nombre_completo}<br/>
    <b>Documento:</b> {cliente.get_tipo_documento_display()}: {cliente.numero_documento}<br/>
    <b>Teléfono:</b> {cliente.telefono or 'No registrado'}<br/>
    <b>Email:</b> {cliente.email or 'No registrado'}<br/>
    <b>Total de reservas:</b> {reservas.count()}
    """
    
    story.append(Paragraph(info_cliente, styles['Normal']))
    story.append(Spacer(1, 20))
    
    if not reservas:
        story.append(Paragraph("No se encontraron reservas para este cliente.", styles['Normal']))
    else:
        # Resumen financiero del cliente
        total_gastado = sum(r.total_con_ajustes for r in reservas)
        total_pagado = sum(sum(p.monto for p in r.pago_set.all()) for r in reservas)
        saldo_pendiente_total = total_gastado - total_pagado
        
        resumen_data = [
            ['<b>RESUMEN FINANCIERO DEL CLIENTE</b>', ''],
            ['Total gastado:', f"${total_gastado:,.2f}"],
            ['Total pagado:', f"${total_pagado:,.2f}"],
            ['Saldo pendiente total:', f"${saldo_pendiente_total:,.2f}"],
        ]
        
        resumen_table = Table(resumen_data, colWidths=[3*inch, 2*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightcoral),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(resumen_table)
        story.append(Spacer(1, 20))
        
        # Procesar cada reserva (versión resumida)
        for reserva in reservas:
            story.append(Paragraph(f"<b>RESERVA {reserva.numero_reserva}</b>", styles['Heading2']))
            
            fecha_salida = reserva.fecha_salida.strftime('%d/%m/%Y') if reserva.fecha_salida else 'Indefinida'
            pagos = reserva.pago_set.all()
            total_pagado_reserva = sum(p.monto for p in pagos)
            
            reserva_data = [
                ['Habitación:', f"{reserva.habitacion.numero} - {reserva.habitacion.tipo.nombre}"],
                ['Fechas:', f"{reserva.fecha_entrada.strftime('%d/%m/%Y')} - {fecha_salida}"],
                ['Estado:', reserva.get_estado_display()],
                ['Total:', f"${reserva.total_con_ajustes:,.2f}"],
                ['Pagado:', f"${total_pagado_reserva:,.2f}"],
                ['Pendiente:', f"${reserva.saldo_pendiente:,.2f}"],
            ]
            
            reserva_table = Table(reserva_data, colWidths=[1.5*inch, 3.5*inch])
            reserva_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(reserva_table)
            story.append(Spacer(1, 15))
    
    # Generar PDF
    doc.build(story)
    
    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_cliente_{cliente.numero_documento}_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf"'
    
    return response


def reporte_por_fecha_pdf(request):
    """Generar PDF filtrado por rango de fechas"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from io import BytesIO
    from datetime import datetime
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if not fecha_desde or not fecha_hasta:
        return HttpResponse("Fechas no especificadas", status=400)
    
    try:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Formato de fecha inválido", status=400)
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Obtener hospedadas en el rango de fechas
    hospedadas = Hospedada.objects.filter(
        fecha_entrada__range=[fecha_desde, fecha_hasta]
    ).select_related(
        'cliente', 'habitacion__tipo'
    ).prefetch_related(
        'pago_set', 'consumohabitacion_set__producto', 'ajustes_precio'
    ).order_by('-fecha_creacion')
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    
    # Contenido del PDF
    story = []
    
    # Título
    title = Paragraph(f"REPORTE POR FECHAS: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}", title_style)
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Información general
    fecha_reporte = timezone.now().strftime('%d/%m/%Y %H:%M')
    info_general = f"""
    <b>Fecha del reporte:</b> {fecha_reporte}<br/>
    <b>Período:</b> {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}<br/>
    <b>Total de hospedadas:</b> {hospedadas.count()}
    """

    story.append(Paragraph(info_general, styles['Normal']))
    story.append(Spacer(1, 20))

    if not hospedadas:
        story.append(Paragraph("No se encontraron hospedadas en el período especificado.", styles['Normal']))
    else:
        # Estadísticas del período
        total_ingresos = sum(h.total_con_ajustes for h in hospedadas)
        total_pagado = sum(sum(p.monto for p in h.pago_set.all()) for h in hospedadas)
        saldo_pendiente_total = total_ingresos - total_pagado
        
        # Contar por estado
        estados_count = {}
        for hospedada in hospedadas:
            estado = hospedada.get_estado_display()
            estados_count[estado] = estados_count.get(estado, 0) + 1

        estadisticas_data = [
            ['<b>ESTADÍSTICAS DEL PERÍODO</b>', ''],
            ['Total de ingresos:', f"${total_ingresos:,.2f}"],
            ['Total pagado:', f"${total_pagado:,.2f}"],
            ['Saldo pendiente:', f"${saldo_pendiente_total:,.2f}"],
        ]

        # Agregar estadísticas por estado
        for estado, count in estados_count.items():
            estadisticas_data.append([f"Hospedadas {estado}:", str(count)])
        
        estadisticas_table = Table(estadisticas_data, colWidths=[3*inch, 2*inch])
        estadisticas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(estadisticas_table)
        story.append(Spacer(1, 20))
        
        # Tabla resumen de hospedadas
        story.append(Paragraph("<b>DETALLE DE HOSPEDADAS</b>", styles['Heading2']))

        hospedadas_data = [['Hospedada', 'Cliente', 'Habitación', 'Entrada', 'Salida', 'Estado', 'Total', 'Pagado', 'Pendiente']]

        for hospedada in hospedadas:
            fecha_salida = hospedada.fecha_salida.strftime('%d/%m/%Y') if hospedada.fecha_salida else 'Indefinida'
            total_pagado_hospedada = sum(p.monto for p in hospedada.pago_set.all())

            hospedadas_data.append([
                hospedada.numero_hospedada,
                hospedada.cliente.nombre_completo,
                f"{hospedada.habitacion.numero}",
                hospedada.fecha_entrada.strftime('%d/%m/%Y'),
                fecha_salida,
                hospedada.get_estado_display(),
                f"${hospedada.total_con_ajustes:,.0f}",
                f"${total_pagado_hospedada:,.0f}",
                f"${hospedada.saldo_pendiente:,.0f}"
            ])

        hospedadas_table = Table(hospedadas_data, colWidths=[0.8*inch, 1.2*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.7*inch])
        hospedadas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightsteelblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(hospedadas_table)
    
    # Generar PDF
    doc.build(story)
    
    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_fechas_{fecha_desde.strftime("%Y%m%d")}_{fecha_hasta.strftime("%Y%m%d")}.pdf"'
    
    return response


# === API ENDPOINTS ===
def api_habitaciones_disponibles(request):
    """API para obtener habitaciones disponibles"""
    fecha_entrada = request.GET.get('fecha_entrada')
    fecha_salida = request.GET.get('fecha_salida')
    
    if not fecha_entrada:
        return JsonResponse({'habitaciones': []})
    
    fecha_entrada = datetime.strptime(fecha_entrada, '%Y-%m-%d').date()
    
    # Si hay fecha de salida, verificar conflictos normalmente
    if fecha_salida:
        fecha_salida = datetime.strptime(fecha_salida, '%Y-%m-%d').date()

        # Habitaciones ocupadas por reservas confirmadas o pendientes
        ocupadas_reservas = Reserva.objects.filter(
            estado__in=['pendiente', 'confirmada'],
            fecha_entrada_prevista__lt=fecha_salida,
            fecha_salida_prevista__gt=fecha_entrada
        ).values_list('habitacion_id', flat=True)

        # Habitaciones ocupadas por hospedadas activas
        ocupadas_hospedadas = Hospedada.objects.filter(
            estado__in=['confirmada', 'en_curso'],
            fecha_entrada__lt=fecha_salida,
            fecha_salida__gt=fecha_entrada
        ).exclude(fecha_salida__isnull=True).values_list('habitacion_id', flat=True)

        ocupadas = list(ocupadas_reservas) + list(ocupadas_hospedadas)
    else:
        # Para hospedadas indefinidas, verificar habitaciones que no estén ocupadas actualmente
        ocupadas_reservas = Reserva.objects.filter(
            estado__in=['pendiente', 'confirmada'],
            fecha_entrada_prevista__lte=fecha_entrada
        ).filter(
            fecha_salida_prevista__gt=fecha_entrada
        ).values_list('habitacion_id', flat=True)

        ocupadas_hospedadas = Hospedada.objects.filter(
            estado__in=['confirmada', 'en_curso'],
            fecha_entrada__lte=fecha_entrada
        ).filter(
            models.Q(fecha_salida__isnull=True) |
            models.Q(fecha_salida__gt=fecha_entrada)
        ).values_list('habitacion_id', flat=True)

        ocupadas = list(ocupadas_reservas) + list(ocupadas_hospedadas)
    
    habitaciones = Habitacion.objects.exclude(
        id__in=ocupadas
    ).filter(estado='disponible').select_related('tipo')

    data = [{
        'id': h.id,
        'numero': h.numero,
        'tipo': h.tipo.nombre,
        'precio': float(h.tipo.precio_por_noche)
    } for h in habitaciones]

    return JsonResponse({'success': True, 'habitaciones': data})


def api_buscar_cliente(request):
    """API para buscar clientes"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'success': True, 'clientes': []})

    clientes = Cliente.objects.filter(
        Q(nombre__icontains=query) |
        Q(apellido__icontains=query) |
        Q(numero_documento__icontains=query)
    )[:10]

    data = [{
        'id': c.id,
        'nombre_completo': c.nombre_completo,
        'numero_documento': c.numero_documento,
        'telefono': c.telefono
    } for c in clientes]

    return JsonResponse({'success': True, 'clientes': data})


@csrf_exempt
def api_crear_cliente(request):
    """API para crear un nuevo cliente desde modal"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            cliente = Cliente.objects.create(
                nombre=data['nombre'],
                apellido=data['apellido'],
                numero_documento=data['numero_documento'],
                tipo_documento=data.get('tipo_documento', 'cedula'),
                telefono=data.get('telefono', ''),
                email=data.get('email', ''),
                direccion=data.get('direccion', '')
            )
            
            return JsonResponse({
                'success': True,
                'cliente': {
                    'id': cliente.id,
                    'nombre_completo': cliente.nombre_completo,
                    'numero_documento': cliente.numero_documento,
                    'telefono': cliente.telefono
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def api_extender_hospedada(request):
    """API para extender o definir fecha de salida de una reserva"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            hospedada = get_object_or_404(Hospedada, id=data['hospedada_id'])
            nueva_fecha_salida = None
            
            if data.get('fecha_salida') and data['fecha_salida'].strip():
                nueva_fecha_salida = datetime.strptime(data['fecha_salida'], '%Y-%m-%d').date()
                
                # Verificar que la nueva fecha sea posterior a la entrada
                if nueva_fecha_salida <= reserva.fecha_entrada:
                    return JsonResponse({'success': False, 'error': 'La fecha de salida debe ser posterior a la fecha de entrada'})
                
                # Verificar conflictos con otras reservas
                conflictos = Reserva.objects.filter(
                    habitacion=reserva.habitacion,
                    estado__in=['confirmada', 'en_curso'],
                    fecha_entrada__lt=nueva_fecha_salida,
                    fecha_salida__gt=reserva.fecha_entrada
                ).exclude(id=reserva.id).exclude(fecha_salida__isnull=True)
                
                if conflictos.exists():
                    return JsonResponse({'success': False, 'error': 'No se puede extender: hay conflictos con otras reservas'})
            
            # Actualizar la reserva
            reserva.fecha_salida = nueva_fecha_salida
            reserva.save()  # Esto recalculará el precio automáticamente
            
            return JsonResponse({
                'success': True,
                'reserva': {
                    'id': reserva.id,
                    'numero_reserva': reserva.numero_reserva,
                    'fecha_salida': reserva.fecha_salida.strftime('%Y-%m-%d') if reserva.fecha_salida else None,
                    'precio_total': float(reserva.precio_total or 0),
                    'es_indefinida': reserva.es_indefinida
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def api_agregar_ajuste(request):
    """API para agregar ajustes de precio (extras o descuentos)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            hospedada = get_object_or_404(Hospedada, id=data['hospedada_id'])
            
            # Validaciones
            if not data.get('concepto') or not data.get('tipo'):
                return JsonResponse({'success': False, 'error': 'Concepto y tipo son requeridos'})
            
            es_porcentaje = data.get('es_porcentaje', False)
            
            if es_porcentaje:
                if not data.get('porcentaje') or float(data['porcentaje']) <= 0:
                    return JsonResponse({'success': False, 'error': 'Porcentaje debe ser mayor a 0'})
                monto = Decimal('0.01')  # Valor mínimo requerido
                porcentaje = Decimal(str(data['porcentaje']))
            else:
                if not data.get('monto') or float(data['monto']) <= 0:
                    return JsonResponse({'success': False, 'error': 'Monto debe ser mayor a 0'})
                monto = Decimal(str(data['monto']))
                porcentaje = None
            
            ajuste = AjustePrecio.objects.create(
                hospedada=hospedada,
                tipo=data['tipo'],
                concepto=data['concepto'],
                monto=monto,
                porcentaje=porcentaje,
                es_porcentaje=es_porcentaje,
                usuario_creacion=request.user if request.user.is_authenticated else None
            )
            
            return JsonResponse({
                'success': True,
                'ajuste': {
                    'id': ajuste.id,
                    'tipo': ajuste.tipo,
                    'concepto': ajuste.concepto,
                    'monto': float(ajuste.monto),
                    'porcentaje': float(ajuste.porcentaje) if ajuste.porcentaje else None,
                    'es_porcentaje': ajuste.es_porcentaje,
                    'monto_calculado': float(ajuste.monto_calculado),
                    'fecha_creacion': ajuste.fecha_creacion.strftime('%d/%m/%Y %H:%M')
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def api_eliminar_ajuste(request):
    """API para eliminar ajustes de precio"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            ajuste = get_object_or_404(AjustePrecio, id=data['ajuste_id'])
            ajuste.delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def api_productos(request):
    """API para obtener productos disponibles"""
    query = request.GET.get('q', '')
    
    productos = Producto.objects.filter(activo=True, stock_actual__gt=0)
    
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(codigo__icontains=query)
        )
    
    data = [{
        'id': p.id,
        'codigo': p.codigo,
        'nombre': p.nombre,
        'precio': float(p.precio),
        'stock_actual': p.stock_actual,
        'categoria': p.categoria.nombre
    } for p in productos]
    
    return JsonResponse({'productos': data})


# === GESTIÓN DE PRODUCTOS ===

@csrf_exempt
def crear_producto(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            codigo = request.POST.get('codigo_producto')
            nombre = request.POST.get('nombre_producto')
            descripcion = request.POST.get('descripcion_producto', '')
            categoria_id = request.POST.get('categoria_producto')
            precio = request.POST.get('precio_producto')
            stock_inicial = request.POST.get('stock_inicial')
            stock_minimo = request.POST.get('stock_minimo')
            unidad_medida = request.POST.get('unidad_medida', 'unidad')
            activo = request.POST.get('activo_producto', 'true') == 'true'
            
            # Validaciones
            if not all([codigo, nombre, categoria_id, precio, stock_inicial, stock_minimo]):
                messages.error(request, 'Todos los campos obligatorios deben ser completados')
                return redirect('hotel:inventario')
            
            # Verificar que el código no exista
            if Producto.objects.filter(codigo=codigo).exists():
                messages.error(request, f'Ya existe un producto con el código "{codigo}"')
                return redirect('hotel:inventario')
            
            # Crear producto
            producto = Producto.objects.create(
                codigo=codigo,
                nombre=nombre,
                descripcion=descripcion,
                categoria_id=categoria_id,
                precio=Decimal(precio),
                stock_actual=int(stock_inicial),
                stock_minimo=int(stock_minimo),
                unidad_medida=unidad_medida,
                activo=activo
            )
            
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente')
            return redirect('hotel:inventario')
            
        except Exception as e:
            messages.error(request, f'Error al crear producto: {str(e)}')
            return redirect('hotel:inventario')
    
    return redirect('hotel:inventario')


@csrf_exempt
def editar_producto(request):
    """Editar producto existente"""
    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto_id')
            if not producto_id:
                messages.error(request, 'ID de producto no proporcionado')
                return redirect('hotel:inventario')
            
            producto = get_object_or_404(Producto, id=producto_id)
            
            # Obtener datos del formulario
            codigo = request.POST.get('codigo_producto')
            nombre = request.POST.get('nombre_producto')
            descripcion = request.POST.get('descripcion_producto', '')
            categoria_id = request.POST.get('categoria_producto')
            precio = request.POST.get('precio_producto')
            stock_inicial = request.POST.get('stock_inicial')
            stock_minimo = request.POST.get('stock_minimo')
            unidad_medida = request.POST.get('unidad_medida', 'unidad')
            activo = request.POST.get('activo_producto', 'true') == 'true'
            
            # Validaciones
            if not all([codigo, nombre, categoria_id, precio, stock_inicial, stock_minimo]):
                messages.error(request, 'Todos los campos obligatorios deben ser completados')
                return redirect('hotel:inventario')
            
            # Verificar que el código no exista en otro producto
            if Producto.objects.filter(codigo=codigo).exclude(id=producto_id).exists():
                messages.error(request, f'Ya existe otro producto con el código "{codigo}"')
                return redirect('hotel:inventario')
            
            # Actualizar producto
            producto.codigo = codigo
            producto.nombre = nombre
            producto.descripcion = descripcion
            producto.categoria_id = categoria_id
            producto.precio = Decimal(precio)
            producto.stock_actual = int(stock_inicial)
            producto.stock_minimo = int(stock_minimo)
            producto.unidad_medida = unidad_medida
            producto.activo = activo
            producto.save()
            
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente')
            return redirect('hotel:inventario')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar producto: {str(e)}')
            return redirect('hotel:inventario')
    
    return redirect('hotel:inventario')


@csrf_exempt
def eliminar_producto(request):
    """Eliminar producto"""
    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto_id')
            if not producto_id:
                messages.error(request, 'ID de producto no proporcionado')
                return redirect('hotel:inventario')
            
            producto = get_object_or_404(Producto, id=producto_id)
            
            # Verificar si tiene consumos asociados
            if ConsumoHabitacion.objects.filter(producto=producto).exists():
                # No eliminar, solo marcar como inactivo
                producto.activo = False
                producto.save()
                messages.warning(request, f'Producto "{producto.nombre}" desactivado (tenía consumos asociados)')
            else:
                # Eliminar completamente
                nombre_producto = producto.nombre
                producto.delete()
                messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente')
            
            return redirect('hotel:inventario')
            
        except Exception as e:
            messages.error(request, f'Error al eliminar producto: {str(e)}')
            return redirect('hotel:inventario')
    
    return redirect('hotel:inventario')


@csrf_exempt
def ajustar_stock(request):
    """Ajustar stock de producto"""
    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto_id')
            nuevo_stock = request.POST.get('nuevo_stock')
            motivo = request.POST.get('motivo')
            
            if not all([producto_id, nuevo_stock, motivo]):
                messages.error(request, 'Todos los campos son obligatorios')
                return redirect('hotel:inventario')
            
            producto = get_object_or_404(Producto, id=producto_id)
            stock_anterior = producto.stock_actual
            
            # Actualizar stock
            producto.stock_actual = int(nuevo_stock)
            producto.save()
            
            diferencia = int(nuevo_stock) - stock_anterior
            tipo_ajuste = "Aumento" if diferencia > 0 else "Disminución"
            
            messages.success(request, 
                f'Stock ajustado para "{producto.nombre}": {stock_anterior} → {nuevo_stock} '
                f'({tipo_ajuste} de {abs(diferencia)} unidades)'
            )
            
            return redirect('hotel:inventario')
            
        except Exception as e:
            messages.error(request, f'Error al ajustar stock: {str(e)}')
            return redirect('hotel:inventario')
    
    return redirect('hotel:inventario')


# === SERVICIOS ===
def agregar_servicio(request, hospedada_id):
    """Página para agregar servicio a una hospedada"""
    hospedada = get_object_or_404(Hospedada, id=hospedada_id)
    tipos_servicio = TipoServicio.objects.filter(activo=True)
    
    if request.method == 'POST':
        tipo_servicio_id = request.POST.get('tipo_servicio_id')
        cantidad = request.POST.get('cantidad')
        precio = request.POST.get('precio')
        observaciones = request.POST.get('observaciones', '')
        
        if tipo_servicio_id and cantidad and precio:
            try:
                tipo_servicio = get_object_or_404(TipoServicio, id=tipo_servicio_id)
                cantidad = int(cantidad)
                precio = float(precio)
                
                # Crear el servicio
                ServicioHospedada.objects.create(
                    hospedada=hospedada,
                    tipo_servicio=tipo_servicio,
                    cantidad=cantidad,
                    precio=precio,
                    observaciones=observaciones,
                    registrado_por=request.user if request.user.is_authenticated else None
                )
                
                messages.success(request, f'Servicio registrado: {cantidad}x {tipo_servicio.nombre}')
                return redirect('hotel:hospedada_detail', hospedada_id=hospedada.id)
            except ValueError:
                messages.error(request, 'Error en los valores ingresados')
    
    context = {
        'hospedada': hospedada,
        'tipos_servicio': tipos_servicio,
    }
    return render(request, 'hotel/agregar_servicio.html', context)


@csrf_exempt
def api_agregar_servicio(request):
    """API para agregar servicio desde el detalle de hospedada"""
    if request.method == 'POST':
        data = json.loads(request.body)

        hospedada_id = data.get('hospedada_id')
        tipo_servicio_id = data.get('tipo_servicio_id')
        cantidad = data.get('cantidad', 1)
        precio = data.get('precio')
        observaciones = data.get('observaciones', '')

        try:
            hospedada = Hospedada.objects.get(id=hospedada_id)
            tipo_servicio = TipoServicio.objects.get(id=tipo_servicio_id)

            # Convertir cantidad y precio explícitamente
            cantidad = int(cantidad)
            from decimal import Decimal
            precio = Decimal(str(precio))

            servicio = ServicioHospedada.objects.create(
                hospedada=hospedada,
                tipo_servicio=tipo_servicio,
                cantidad=cantidad,
                precio=precio,
                observaciones=observaciones,
                registrado_por=request.user if request.user.is_authenticated else None
            )

            return JsonResponse({
                'success': True,
                'message': f'Servicio agregado: {tipo_servicio.nombre}',
                'servicio': {
                    'id': servicio.id,
                    'nombre': tipo_servicio.nombre,
                    'cantidad': cantidad,
                    'precio': str(precio),
                    'subtotal': str(servicio.subtotal),
                    'fecha': servicio.fecha_servicio.strftime('%d/%m/%Y %H:%M')
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@csrf_exempt 
def api_tipos_servicio(request):
    """API para obtener tipos de servicio disponibles"""
    tipos = TipoServicio.objects.filter(activo=True).values(
        'id', 'nombre', 'descripcion', 'precio_sugerido', 'requiere_precio'
    )
    return JsonResponse({'tipos': list(tipos)})


# === INVENTARIO ===
def habitacion_inventario(request, habitacion_id):
    """Ver y gestionar inventario de una habitación"""
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    inventario = InventarioHabitacion.objects.filter(habitacion=habitacion).select_related('elemento')
    elementos_disponibles = ElementoInventario.objects.filter(activo=True)
    
    context = {
        'habitacion': habitacion,
        'inventario': inventario,
        'elementos_disponibles': elementos_disponibles,
    }
    return render(request, 'hotel/habitacion_inventario.html', context)


@csrf_exempt
def api_actualizar_inventario(request):
    """API para actualizar inventario de habitación"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        habitacion_id = data.get('habitacion_id')
        elemento_id = data.get('elemento_id')
        cantidad = data.get('cantidad', 0)
        estado = data.get('estado', 'bueno')
        accion = data.get('accion', 'actualizar')  # actualizar, agregar, eliminar
        
        try:
            habitacion = Habitacion.objects.get(id=habitacion_id)
            
            if accion == 'agregar':
                elemento = ElementoInventario.objects.get(id=elemento_id)
                inventario, created = InventarioHabitacion.objects.get_or_create(
                    habitacion=habitacion,
                    elemento=elemento,
                    defaults={'cantidad': cantidad, 'estado': estado}
                )
                if not created:
                    inventario.cantidad = cantidad
                    inventario.estado = estado
                    inventario.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Elemento {elemento.nombre} agregado/actualizado',
                    'inventario': {
                        'id': inventario.id,
                        'elemento': elemento.nombre,
                        'cantidad': inventario.cantidad,
                        'estado': inventario.estado
                    }
                })
            
            elif accion == 'actualizar':
                inventario = InventarioHabitacion.objects.get(
                    habitacion=habitacion,
                    elemento__id=elemento_id
                )
                inventario.cantidad = cantidad
                inventario.estado = estado
                inventario.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Inventario actualizado'
                })
            
            elif accion == 'eliminar':
                InventarioHabitacion.objects.filter(
                    habitacion=habitacion,
                    elemento__id=elemento_id
                ).delete()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Elemento eliminado del inventario'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


def gestionar_elementos_inventario(request):
    """Gestionar catálogo de elementos de inventario"""
    elementos = ElementoInventario.objects.all().order_by('categoria', 'nombre')
    
    if request.method == 'POST':
        # Crear nuevo elemento
        nombre = request.POST.get('nombre')
        categoria = request.POST.get('categoria')
        costo_reposicion = request.POST.get('costo_reposicion')
        descripcion = request.POST.get('descripcion', '')
        
        if nombre and categoria and costo_reposicion:
            try:
                ElementoInventario.objects.create(
                    nombre=nombre,
                    categoria=categoria,
                    costo_reposicion=float(costo_reposicion),
                    descripcion=descripcion
                )
                messages.success(request, f'Elemento "{nombre}" creado exitosamente')
                return redirect('hotel:gestionar_elementos_inventario')
            except Exception as e:
                messages.error(request, f'Error al crear elemento: {str(e)}')
    
    context = {
        'elementos': elementos,
        'categorias': ElementoInventario.CATEGORIAS,
    }
    return render(request, 'hotel/gestionar_elementos_inventario.html', context)


# === CHECKOUT ===
@csrf_exempt
def hospedada_checkout(request, hospedada_id):
    """Realizar checkout de una hospedada"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            hospedada = get_object_or_404(Hospedada, id=hospedada_id)
            
            # Verificar que esté en estado correcto
            if hospedada.estado not in ['en_curso', 'confirmada']:
                return JsonResponse({
                    'success': False, 
                    'error': 'La hospedada no está en estado válido para checkout'
                })
            
            # Obtener parámetros del checkout
            accion = data.get('accion')  # 'pagar_todo', 'dejar_deuda', 'sin_deuda'
            deudor = data.get('deudor', 'cliente')  # 'cliente' o 'empresa'
            observaciones_deuda = data.get('observaciones_deuda', '')
            
            # Calcular saldo pendiente
            saldo_pendiente = hospedada.saldo_pendiente
            
            # Si hay saldo pendiente y se quiere pagar todo
            if accion == 'pagar_todo' and saldo_pendiente > 0:
                # Crear pago completo
                pago = Pago.objects.create(
                    hospedada=hospedada,
                    monto=saldo_pendiente,
                    metodo_pago=data.get('metodo_pago', 'efectivo'),
                    tipo_pago='pago_total',
                    pagado_por=deudor,
                    observaciones='Pago completo en checkout',
                    usuario_registro=request.user if request.user.is_authenticated else None
                )
                # Realizar checkout sin deuda
                hospedada.realizar_checkout(pagar_todo=True)
                mensaje = f'Checkout realizado. Se pagó el total de ${saldo_pendiente:.2f}'
                
            elif accion == 'dejar_deuda' and saldo_pendiente > 0:
                # Realizar checkout con deuda
                hospedada.realizar_checkout(
                    pagar_todo=False, 
                    deudor=deudor,
                    observaciones_deuda=observaciones_deuda
                )
                deudor_texto = 'La empresa' if deudor == 'empresa' else 'El cliente'
                mensaje = f'Checkout realizado. {deudor_texto} quedó debiendo ${saldo_pendiente:.2f}'
                
            else:
                # Sin saldo pendiente o checkout normal
                hospedada.realizar_checkout(pagar_todo=True)
                mensaje = 'Checkout realizado exitosamente'
            
            return JsonResponse({
                'success': True,
                'mensaje': mensaje,
                'tiene_deuda': hospedada.tiene_deuda,
                'monto_deuda': float(hospedada.monto_deuda),
                'deudor': hospedada.deudor
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# Import views for the new Reservas module
from .views_reservas import (
    reservas_list,
    reserva_create,
    reserva_detail,
    reserva_edit,
    reserva_cancelar,
    reserva_convertir,
    api_verificar_disponibilidad
)


# === AUTENTICACIÓN ===
def usuario_login(request):
    """Vista de login personalizada"""
    if request.user.is_authenticated:
        return redirect('hotel:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                try:
                    perfil = PerfilUsuario.objects.get(user=user)
                    if perfil.activo:
                        login(request, user)
                        messages.success(request, f'Bienvenido, {user.first_name or user.username}!')

                        # Redirigir según el rol
                        next_url = request.GET.get('next', 'hotel:dashboard')
                        return redirect(next_url)
                    else:
                        messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador.')
                except PerfilUsuario.DoesNotExist:
                    messages.error(request, 'Tu perfil de usuario no está configurado. Contacta al administrador.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor, ingresa usuario y contraseña.')

    return render(request, 'hotel/login.html')


def usuario_logout(request):
    """Vista de logout"""
    if request.user.is_authenticated:
        messages.success(request, 'Has cerrado sesión exitosamente.')
    logout(request)
    return redirect('hotel:login')


@login_required
def perfil_usuario(request):
    """Vista del perfil del usuario actual"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Tu perfil no está configurado. Contacta al administrador.')
        return redirect('hotel:dashboard')

    context = {
        'perfil': perfil,
        'user': request.user
    }
    return render(request, 'hotel/perfil_usuario.html', context)


@solo_administrador
def gestionar_usuarios(request):
    """Vista para gestionar usuarios (solo administradores)"""
    usuarios = PerfilUsuario.objects.select_related('user').all().order_by('user__username')

    context = {
        'usuarios': usuarios
    }
    return render(request, 'hotel/gestionar_usuarios.html', context)