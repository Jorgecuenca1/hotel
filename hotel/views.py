from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
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
    TipoHabitacion, Habitacion, Cliente, Reserva, 
    CategoriaProducto, Producto, ConsumoHabitacion, Pago, Factura, AjustePrecio
)


def dashboard(request):
    """Vista principal del dashboard"""
    context = {
        'total_habitaciones': Habitacion.objects.count(),
        'habitaciones_disponibles': Habitacion.objects.filter(estado='disponible').count(),
        'habitaciones_ocupadas': Habitacion.objects.filter(estado='ocupada').count(),
        'reservas_hoy': Reserva.objects.filter(fecha_entrada=date.today()).count(),
        'productos_bajo_stock': Producto.objects.filter(stock_actual__lte=F('stock_minimo')).count(),
        'ingresos_mes': Pago.objects.filter(
            fecha_pago__month=timezone.now().month,
            fecha_pago__year=timezone.now().year
        ).aggregate(total=Sum('monto'))['total'] or 0,
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


# === RESERVAS ===
def reservas_list(request):
    """Lista de reservas"""
    reservas = Reserva.objects.select_related('cliente', 'habitacion').all()
    
    # Filtros
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if estado:
        reservas = reservas.filter(estado=estado)
    if fecha_desde:
        reservas = reservas.filter(fecha_entrada__gte=fecha_desde)
    if fecha_hasta:
        reservas = reservas.filter(fecha_salida__lte=fecha_hasta)
    
    paginator = Paginator(reservas, 20)
    page = request.GET.get('page')
    reservas = paginator.get_page(page)
    
    context = {
        'reservas': reservas,
        'filtros': {'estado': estado, 'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta}
    }
    return render(request, 'hotel/reservas.html', context)


@csrf_exempt
def reserva_create(request):
    """Crear nueva reserva"""
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
                conflictos = Reserva.objects.filter(
                    habitacion=habitacion,
                    estado__in=['confirmada', 'en_curso'],
                    fecha_entrada__lt=fecha_salida,
                    fecha_salida__gt=fecha_entrada
                ).exclude(fecha_salida__isnull=True)
                
                if conflictos.exists():
                    return JsonResponse({'success': False, 'error': 'Habitación no disponible en esas fechas'})
            else:
                # Para reservas indefinidas, verificar que no haya conflictos actuales
                conflictos_actuales = Reserva.objects.filter(
                    habitacion=habitacion,
                    estado__in=['confirmada', 'en_curso'],
                    fecha_entrada__lte=fecha_entrada
                ).filter(
                    models.Q(fecha_salida__isnull=True) | 
                    models.Q(fecha_salida__gt=fecha_entrada)
                )
                
                if conflictos_actuales.exists():
                    return JsonResponse({'success': False, 'error': 'Habitación no disponible para reserva indefinida'})
            
            reserva = Reserva.objects.create(
                cliente=cliente,
                habitacion=habitacion,
                fecha_entrada=fecha_entrada,
                fecha_salida=fecha_salida,
                numero_huespedes=data.get('numero_huespedes', 1),
                observaciones=data.get('observaciones', ''),
                usuario_creacion=request.user if request.user.is_authenticated else None
            )
            
            # Cambiar estado de habitación si la reserva es para hoy
            if fecha_entrada == date.today():
                habitacion.estado = 'ocupada'
                habitacion.save()
                reserva.estado = 'en_curso'
                reserva.save()
            
            return JsonResponse({
                'success': True,
                'reserva': {
                    'id': reserva.id,
                    'numero_reserva': reserva.numero_reserva,
                    'precio_total': float(reserva.precio_total or 0)
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})


def reserva_detail(request, reserva_id):
    """Detalle de reserva con consumos, pagos y ajustes"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    consumos = ConsumoHabitacion.objects.filter(reserva=reserva).select_related('producto')
    pagos = Pago.objects.filter(reserva=reserva)
    ajustes = AjustePrecio.objects.filter(reserva=reserva, activo=True)
    
    total_consumos = reserva.subtotal_consumos
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
        'reserva': reserva,
        'consumos': consumos,
        'pagos': pagos,
        'ajustes': ajustes,
        'ajustes_json': json.dumps(ajustes_json),
        'total_consumos': total_consumos,
        'total_pagado': total_pagado,
    }
    return render(request, 'hotel/reserva_detail.html', context)


def agregar_consumo(request, reserva_id):
    """Página para agregar consumo a una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
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
                        reserva=reserva,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio,
                        fecha_consumo=timezone.now()
                    )
                    
                    # Actualizar stock
                    producto.stock_actual -= cantidad
                    producto.save()
                    
                    messages.success(request, f'Consumo registrado: {cantidad}x {producto.nombre}')
                    return redirect('hotel:reserva_detail', reserva_id=reserva.id)
                else:
                    messages.error(request, f'Stock insuficiente. Solo hay {producto.stock_actual} unidades disponibles.')
            except (ValueError, Producto.DoesNotExist):
                messages.error(request, 'Error al procesar el consumo. Verifique los datos.')
        else:
            messages.error(request, 'Por favor complete todos los campos.')
    
    # Obtener productos disponibles
    productos = Producto.objects.filter(activo=True, stock_actual__gt=0).order_by('codigo')
    
    context = {
        'reserva': reserva,
        'productos': productos,
    }
    return render(request, 'hotel/agregar_consumo.html', context)


def agregar_pago(request, reserva_id):
    """Página para agregar pago a una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Calcular saldo pendiente usando los nuevos métodos que incluyen ajustes
    pagos = Pago.objects.filter(reserva=reserva)
    total_pagado = sum(pago.monto for pago in pagos)
    total_reserva = reserva.total_con_ajustes  # Incluye habitación + consumos + ajustes
    saldo_pendiente = reserva.saldo_pendiente  # Usa el método que incluye ajustes
    
    if request.method == 'POST':
        monto = request.POST.get('monto')
        metodo_pago = request.POST.get('metodo_pago')
        tipo_pago = request.POST.get('tipo_pago')
        referencia = request.POST.get('referencia', '')
        observaciones = request.POST.get('observaciones', '')
        
        if monto and metodo_pago:
            try:
                monto = float(monto)
                
                # Validar que el monto no sea mayor al saldo pendiente
                if monto <= saldo_pendiente:
                    # Crear el pago
                    Pago.objects.create(
                        reserva=reserva,
                        monto=monto,
                        metodo_pago=metodo_pago,
                        tipo_pago=tipo_pago or 'abono',
                        referencia=referencia,
                        observaciones=observaciones,
                        fecha_pago=timezone.now()
                    )
                    
                    messages.success(request, f'Pago registrado: ${monto:.2f} por {dict(Pago.METODOS_PAGO)[metodo_pago]}')
                    return redirect('hotel:reserva_detail', reserva_id=reserva.id)
                else:
                    messages.error(request, f'El monto no puede ser mayor al saldo pendiente (${saldo_pendiente:.2f})')
            except ValueError:
                messages.error(request, 'El monto debe ser un número válido.')
        else:
            messages.error(request, 'Por favor complete todos los campos obligatorios.')
    
    context = {
        'reserva': reserva,
        'saldo_pendiente': saldo_pendiente,
        'total_reserva': total_reserva,
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
            reserva = get_object_or_404(Reserva, id=data['reserva_id'])
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
            reserva = get_object_or_404(Reserva, id=data['reserva_id'])
            
            pago = Pago.objects.create(
                reserva=reserva,
                monto=Decimal(data['monto']),
                metodo_pago=data['metodo_pago'],
                tipo_pago=data['tipo_pago'],
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
def generar_factura(request, reserva_id):
    """Generar factura para una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar si ya existe factura
    try:
        factura = Factura.objects.get(reserva=reserva)
    except Factura.DoesNotExist:
        factura = Factura.objects.create(
            reserva=reserva,
            usuario_emision=request.user if request.user.is_authenticated else None
        )
    
    # Calcular totales y estado de pago
    pagos = Pago.objects.filter(reserva=reserva)
    ajustes = AjustePrecio.objects.filter(reserva=reserva, activo=True)
    total_pagado = sum(pago.monto for pago in pagos)
    saldo_pendiente = reserva.saldo_pendiente
    
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
    factura = get_object_or_404(Factura, id=factura_id)
    
    # Aquí puedes implementar la generación de PDF
    # Por ahora retornamos la vista HTML
    return render(request, 'hotel/factura_pdf.html', {'factura': factura})


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
    ).select_related('reserva__cliente')
    
    for factura in facturas:
        writer.writerow([
            factura.fecha_emision.strftime('%Y-%m-%d'),
            'Factura',
            factura.numero_factura,
            factura.reserva.cliente.nombre_completo,
            f'Reserva {factura.reserva.numero_reserva}',
            factura.total,
            ''
        ])
    
    # Pagos
    pagos = Pago.objects.filter(
        fecha_pago__date__range=[fecha_desde, fecha_hasta]
    ).select_related('reserva__cliente')
    
    for pago in pagos:
        writer.writerow([
            pago.fecha_pago.strftime('%Y-%m-%d'),
            'Pago',
            pago.numero_pago,
            pago.reserva.cliente.nombre_completo,
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
            fecha_entrada__month=timezone.now().month,
            fecha_entrada__year=timezone.now().year
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
    
    # Obtener reservas en el rango de fechas
    reservas = Reserva.objects.filter(
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
    <b>Total de reservas:</b> {reservas.count()}
    """
    
    story.append(Paragraph(info_general, styles['Normal']))
    story.append(Spacer(1, 20))
    
    if not reservas:
        story.append(Paragraph("No se encontraron reservas en el período especificado.", styles['Normal']))
    else:
        # Estadísticas del período
        total_ingresos = sum(r.total_con_ajustes for r in reservas)
        total_pagado = sum(sum(p.monto for p in r.pago_set.all()) for r in reservas)
        saldo_pendiente_total = total_ingresos - total_pagado
        
        # Contar por estado
        estados_count = {}
        for reserva in reservas:
            estado = reserva.get_estado_display()
            estados_count[estado] = estados_count.get(estado, 0) + 1
        
        estadisticas_data = [
            ['<b>ESTADÍSTICAS DEL PERÍODO</b>', ''],
            ['Total de ingresos:', f"${total_ingresos:,.2f}"],
            ['Total pagado:', f"${total_pagado:,.2f}"],
            ['Saldo pendiente:', f"${saldo_pendiente_total:,.2f}"],
        ]
        
        # Agregar estadísticas por estado
        for estado, count in estados_count.items():
            estadisticas_data.append([f"Reservas {estado}:", str(count)])
        
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
        
        # Tabla resumen de reservas
        story.append(Paragraph("<b>DETALLE DE RESERVAS</b>", styles['Heading2']))
        
        reservas_data = [['Reserva', 'Cliente', 'Habitación', 'Entrada', 'Salida', 'Estado', 'Total', 'Pagado', 'Pendiente']]
        
        for reserva in reservas:
            fecha_salida = reserva.fecha_salida.strftime('%d/%m/%Y') if reserva.fecha_salida else 'Indefinida'
            total_pagado_reserva = sum(p.monto for p in reserva.pago_set.all())
            
            reservas_data.append([
                reserva.numero_reserva,
                reserva.cliente.nombre_completo,
                f"{reserva.habitacion.numero}",
                reserva.fecha_entrada.strftime('%d/%m/%Y'),
                fecha_salida,
                reserva.get_estado_display(),
                f"${reserva.total_con_ajustes:,.0f}",
                f"${total_pagado_reserva:,.0f}",
                f"${reserva.saldo_pendiente:,.0f}"
            ])
        
        reservas_table = Table(reservas_data, colWidths=[0.8*inch, 1.2*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.7*inch])
        reservas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightsteelblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(reservas_table)
    
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
        
        # Habitaciones ocupadas en esas fechas
        ocupadas = Reserva.objects.filter(
            estado__in=['confirmada', 'en_curso'],
            fecha_entrada__lt=fecha_salida,
            fecha_salida__gt=fecha_entrada
        ).exclude(fecha_salida__isnull=True).values_list('habitacion_id', flat=True)
    else:
        # Para reservas indefinidas, verificar habitaciones que no estén ocupadas actualmente
        # o que tengan reservas indefinidas activas
        ocupadas = Reserva.objects.filter(
            estado__in=['confirmada', 'en_curso'],
            fecha_entrada__lte=fecha_entrada
        ).filter(
            models.Q(fecha_salida__isnull=True) | 
            models.Q(fecha_salida__gt=fecha_entrada)
        ).values_list('habitacion_id', flat=True)
    
    habitaciones = Habitacion.objects.exclude(
        id__in=ocupadas
    ).filter(estado='disponible').select_related('tipo')
    
    data = [{
        'id': h.id,
        'numero': h.numero,
        'tipo': h.tipo.nombre,
        'precio': float(h.tipo.precio_por_noche)
    } for h in habitaciones]
    
    return JsonResponse({'habitaciones': data})


def api_buscar_cliente(request):
    """API para buscar clientes"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'clientes': []})
    
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
    
    return JsonResponse({'clientes': data})


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
def api_extender_reserva(request):
    """API para extender o definir fecha de salida de una reserva"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            reserva = get_object_or_404(Reserva, id=data['reserva_id'])
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
            reserva = get_object_or_404(Reserva, id=data['reserva_id'])
            
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
                reserva=reserva,
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