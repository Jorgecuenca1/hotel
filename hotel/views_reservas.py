# === RESERVAS (PHONE BOOKINGS) ===
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import json
from datetime import datetime
from .models import Reserva, Cliente, Habitacion, Empresa, Hospedada


def reservas_list(request):
    """Lista de reservas telefónicas"""
    reservas = Reserva.objects.select_related('cliente', 'habitacion', 'empresa').all()
    
    # Filtros
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if estado:
        reservas = reservas.filter(estado=estado)
    if fecha_desde:
        reservas = reservas.filter(fecha_entrada_prevista__gte=fecha_desde)
    if fecha_hasta:
        reservas = reservas.filter(fecha_salida_prevista__lte=fecha_hasta)
    
    # Ordenar por fecha de entrada prevista
    reservas = reservas.order_by('fecha_entrada_prevista')
    
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
    """Crear nueva reserva telefónica"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            cliente = get_object_or_404(Cliente, id=data['cliente_id'])
            habitacion = get_object_or_404(Habitacion, id=data['habitacion_id'])
            
            # Obtener empresa si se proporciona
            empresa = None
            if data.get('empresa_id'):
                empresa = get_object_or_404(Empresa, id=data['empresa_id'])
            
            # Crear la reserva
            reserva = Reserva.objects.create(
                cliente=cliente,
                empresa=empresa,
                habitacion=habitacion,
                fecha_entrada_prevista=datetime.strptime(data['fecha_entrada'], '%Y-%m-%d').date(),
                fecha_salida_prevista=datetime.strptime(data['fecha_salida'], '%Y-%m-%d').date(),
                numero_huespedes=data.get('numero_huespedes', 1),
                precio_acordado=data.get('precio_acordado'),
                observaciones=data.get('observaciones', ''),
                usuario_creacion=request.user if request.user.is_authenticated else None
            )
            
            # Verificar disponibilidad
            disponible, mensaje = reserva.verificar_disponibilidad()
            if not disponible:
                reserva.delete()
                return JsonResponse({'success': False, 'error': mensaje})
            
            # Confirmar la reserva si se solicita
            if data.get('confirmar'):
                reserva.estado = 'confirmada'
                reserva.save()
            
            return JsonResponse({
                'success': True,
                'reserva': {
                    'id': reserva.id,
                    'numero_reserva': reserva.numero_reserva,
                    'precio_acordado': float(reserva.precio_acordado or 0)
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})


def reserva_detail(request, reserva_id):
    """Detalle de una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar disponibilidad actual
    disponible, mensaje = reserva.verificar_disponibilidad()
    
    context = {
        'reserva': reserva,
        'disponible': disponible,
        'mensaje_disponibilidad': mensaje
    }
    return render(request, 'hotel/reserva_detail.html', context)


def reserva_edit(request, reserva_id):
    """Editar una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if request.method == 'POST':
        try:
            # Actualizar datos de la reserva
            reserva.fecha_entrada_prevista = datetime.strptime(request.POST['fecha_entrada'], '%Y-%m-%d').date()
            reserva.fecha_salida_prevista = datetime.strptime(request.POST['fecha_salida'], '%Y-%m-%d').date()
            reserva.numero_huespedes = request.POST.get('numero_huespedes', 1)
            reserva.precio_acordado = request.POST.get('precio_acordado')
            reserva.observaciones = request.POST.get('observaciones', '')
            
            # Verificar disponibilidad con las nuevas fechas
            disponible, mensaje = reserva.verificar_disponibilidad()
            if not disponible:
                messages.error(request, mensaje)
                return redirect('hotel:reserva_edit', reserva_id=reserva.id)
            
            reserva.save()
            messages.success(request, 'Reserva actualizada exitosamente')
            return redirect('hotel:reserva_detail', reserva_id=reserva.id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar reserva: {str(e)}')
    
    context = {
        'reserva': reserva,
        'habitaciones': Habitacion.objects.all(),
        'clientes': Cliente.objects.all(),
        'empresas': Empresa.objects.filter(activa=True)
    }
    return render(request, 'hotel/reserva_edit.html', context)


def reserva_cancelar(request, reserva_id):
    """Cancelar una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if request.method == 'POST':
        if reserva.estado == 'convertida':
            messages.error(request, 'No se puede cancelar una reserva que ya fue convertida a hospedada')
        else:
            reserva.estado = 'cancelada'
            reserva.save()
            messages.success(request, f'Reserva {reserva.numero_reserva} cancelada exitosamente')
        
        return redirect('hotel:reservas')
    
    return redirect('hotel:reserva_detail', reserva_id=reserva.id)


@csrf_exempt
def reserva_convertir(request, reserva_id):
    """Convertir una reserva en hospedada"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else {}
            tipo_hospedada = data.get('tipo_hospedada', 'continua')
            
            # Verificar que la reserva no haya sido convertida
            if reserva.estado == 'convertida':
                return JsonResponse({'success': False, 'error': 'Esta reserva ya fue convertida'})
            
            # Verificar que la reserva esté confirmada
            if reserva.estado != 'confirmada':
                return JsonResponse({'success': False, 'error': 'Solo se pueden convertir reservas confirmadas'})
            
            # Convertir a hospedada
            hospedada = reserva.convertir_a_hospedada(
                tipo_hospedada=tipo_hospedada,
                usuario=request.user if request.user.is_authenticated else None
            )
            
            return JsonResponse({
                'success': True,
                'hospedada': {
                    'id': hospedada.id,
                    'numero_hospedada': hospedada.numero_hospedada,
                    'redirect_url': f'/hotel/hospedadas/{hospedada.id}/'
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def api_verificar_disponibilidad(request):
    """API para verificar disponibilidad de habitación"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            habitacion = get_object_or_404(Habitacion, id=data['habitacion_id'])
            fecha_entrada = datetime.strptime(data['fecha_entrada'], '%Y-%m-%d').date()
            fecha_salida = datetime.strptime(data['fecha_salida'], '%Y-%m-%d').date()
            
            # Crear una reserva temporal para verificar
            reserva_temp = Reserva(
                habitacion=habitacion,
                fecha_entrada_prevista=fecha_entrada,
                fecha_salida_prevista=fecha_salida
            )
            
            disponible, mensaje = reserva_temp.verificar_disponibilidad()
            
            return JsonResponse({
                'success': True,
                'disponible': disponible,
                'mensaje': mensaje
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})