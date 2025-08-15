from django.urls import path
from . import views

app_name = 'hotel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Habitaciones
    path('habitaciones/', views.habitaciones_list, name='habitaciones'),
    path('habitaciones/crear/', views.habitacion_create, name='habitacion_create'),
    path('habitaciones/<int:habitacion_id>/editar/', views.habitacion_edit, name='habitacion_edit'),
    path('habitaciones/<int:habitacion_id>/eliminar/', views.habitacion_delete, name='habitacion_delete'),
    path('habitaciones/<int:habitacion_id>/cambiar-estado/', views.cambiar_estado_habitacion, name='cambiar_estado_habitacion'),
    
    # Tipos de Habitación
    path('tipos-habitacion/', views.tipos_habitacion_list, name='tipos_habitacion'),
    path('tipos-habitacion/crear/', views.tipo_habitacion_create, name='tipo_habitacion_create'),
    path('tipos-habitacion/<int:tipo_id>/editar/', views.tipo_habitacion_edit, name='tipo_habitacion_edit'),
    path('tipos-habitacion/<int:tipo_id>/eliminar/', views.tipo_habitacion_delete, name='tipo_habitacion_delete'),
    
    # Clientes
    path('clientes/', views.clientes_list, name='clientes'),
    path('clientes/crear/', views.cliente_create, name='cliente_create'),
    
    # Reservas
    path('reservas/', views.reservas_list, name='reservas'),
    path('reservas/crear/', views.reserva_create, name='reserva_create'),
    path('reservas/<int:reserva_id>/', views.reserva_detail, name='reserva_detail'),
    path('reservas/<int:reserva_id>/agregar-consumo/', views.agregar_consumo, name='agregar_consumo'),
    path('reservas/<int:reserva_id>/agregar-pago/', views.agregar_pago, name='agregar_pago'),
    
    # Inventario
    path('inventario/', views.inventario_list, name='inventario'),
    path('consumos/registrar/', views.registrar_consumo, name='registrar_consumo'),
    
    # Gestión de Productos
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('productos/ajustar-stock/', views.ajustar_stock, name='ajustar_stock'),
    
    # Pagos
    path('pagos/registrar/', views.registrar_pago, name='registrar_pago'),
    
    # Facturación
    path('facturas/<int:reserva_id>/generar/', views.generar_factura, name='generar_factura'),
    path('facturas/<int:factura_id>/pdf/', views.factura_pdf, name='factura_pdf'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
    path('exportar-contabilidad/', views.exportar_contabilidad, name='exportar_contabilidad'),
    
    # API
    path('api/habitaciones-disponibles/', views.api_habitaciones_disponibles, name='api_habitaciones_disponibles'),
    path('api/buscar-cliente/', views.api_buscar_cliente, name='api_buscar_cliente'),
    path('api/productos/', views.api_productos, name='api_productos'),
]