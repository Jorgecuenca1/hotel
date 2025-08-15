from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator
import json
import csv
from datetime import datetime, date
from decimal import Decimal

from .models import (
    TipoHabitacion, Habitacion, Cliente, Reserva, 
    CategoriaProducto, Producto, ConsumoHabitacion, Pago, Factura
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
            fecha_salida = datetime.strptime(data['fecha_salida'], '%Y-%m-%d').date()
            
            conflictos = Reserva.objects.filter(
                habitacion=habitacion,
                estado__in=['confirmada', 'en_curso'],
                fecha_entrada__lt=fecha_salida,
                fecha_salida__gt=fecha_entrada
            )
            
            if conflictos.exists():
                return JsonResponse({'success': False, 'error': 'Habitación no disponible en esas fechas'})
            
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
    """Detalle de reserva con consumos y pagos"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    consumos = ConsumoHabitacion.objects.filter(reserva=reserva).select_related('producto')
    pagos = Pago.objects.filter(reserva=reserva)
    
    total_consumos = sum(consumo.subtotal for consumo in consumos)
    total_pagado = sum(pago.monto for pago in pagos)
    total_reserva = (reserva.precio_total or 0) + total_consumos
    saldo_pendiente = total_reserva - total_pagado
    
    context = {
        'reserva': reserva,
        'consumos': consumos,
        'pagos': pagos,
        'total_consumos': total_consumos,
        'total_pagado': total_pagado,
        'total_reserva': total_reserva,
        'saldo_pendiente': saldo_pendiente,
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
    
    # Calcular saldo pendiente
    consumos = ConsumoHabitacion.objects.filter(reserva=reserva)
    pagos = Pago.objects.filter(reserva=reserva)
    total_consumos = sum(consumo.subtotal for consumo in consumos)
    total_pagado = sum(pago.monto for pago in pagos)
    total_reserva = (reserva.precio_total or 0) + total_consumos
    saldo_pendiente = total_reserva - total_pagado
    
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
    
    # Calcular total pagado
    pagos = Pago.objects.filter(reserva=reserva)
    total_pagado = sum(pago.monto for pago in pagos)
    
    context = {
        'factura': factura,
        'total_pagado': total_pagado
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
    }
    return render(request, 'hotel/reportes.html', context)


# === API ENDPOINTS ===
def api_habitaciones_disponibles(request):
    """API para obtener habitaciones disponibles"""
    fecha_entrada = request.GET.get('fecha_entrada')
    fecha_salida = request.GET.get('fecha_salida')
    
    if not fecha_entrada or not fecha_salida:
        return JsonResponse({'habitaciones': []})
    
    fecha_entrada = datetime.strptime(fecha_entrada, '%Y-%m-%d').date()
    fecha_salida = datetime.strptime(fecha_salida, '%Y-%m-%d').date()
    
    # Habitaciones ocupadas en esas fechas
    ocupadas = Reserva.objects.filter(
        estado__in=['confirmada', 'en_curso'],
        fecha_entrada__lt=fecha_salida,
        fecha_salida__gt=fecha_entrada
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