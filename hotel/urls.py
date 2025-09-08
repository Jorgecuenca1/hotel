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
    
    # Empresas
    path('empresas/', views.empresas_list, name='empresas'),
    path('empresas/crear/', views.empresa_create, name='empresa_create'),
    path('empresas/<int:empresa_id>/editar/', views.empresa_edit, name='empresa_edit'),
    path('empresas/<int:empresa_id>/eliminar/', views.empresa_delete, name='empresa_delete'),
    
    # Hospedadas
    path('hospedadas/', views.hospedadas_list, name='hospedadas'),
    path('hospedadas/crear/', views.hospedada_create, name='hospedada_create'),
    path('hospedadas/<int:hospedada_id>/', views.hospedada_detail, name='hospedada_detail'),
    path('hospedadas/<int:hospedada_id>/agregar-consumo/', views.agregar_consumo, name='agregar_consumo'),
    path('hospedadas/<int:hospedada_id>/agregar-pago/', views.agregar_pago, name='agregar_pago'),
    path('hospedadas/<int:hospedada_id>/agregar-servicio/', views.agregar_servicio, name='agregar_servicio'),
    path('hospedadas/<int:hospedada_id>/checkout/', views.hospedada_checkout, name='hospedada_checkout'),
    
    # Reservas (Phone Bookings)
    path('reservas/', views.reservas_list, name='reservas'),
    path('reservas/crear/', views.reserva_create, name='reserva_create'),
    path('reservas/<int:reserva_id>/', views.reserva_detail, name='reserva_detail'),
    path('reservas/<int:reserva_id>/editar/', views.reserva_edit, name='reserva_edit'),
    path('reservas/<int:reserva_id>/cancelar/', views.reserva_cancelar, name='reserva_cancelar'),
    path('reservas/<int:reserva_id>/convertir/', views.reserva_convertir, name='reserva_convertir'),
    
    # Inventario
    path('inventario/', views.inventario_list, name='inventario'),
    path('habitaciones/<int:habitacion_id>/inventario/', views.habitacion_inventario, name='habitacion_inventario'),
    path('inventario/elementos/', views.gestionar_elementos_inventario, name='gestionar_elementos_inventario'),
    path('consumos/registrar/', views.registrar_consumo, name='registrar_consumo'),
    
    # Gestión de Productos
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('productos/ajustar-stock/', views.ajustar_stock, name='ajustar_stock'),
    
    # Pagos
    path('pagos/registrar/', views.registrar_pago, name='registrar_pago'),
    
    # Facturación
    path('facturas/<int:hospedada_id>/generar/', views.generar_factura, name='generar_factura'),
    path('facturas/<int:factura_id>/pdf/', views.factura_pdf, name='factura_pdf'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
    path('exportar-contabilidad/', views.exportar_contabilidad, name='exportar_contabilidad'),
    
    # Reportes PDF
    path('reportes/todas-reservas-pdf/', views.reporte_todas_reservas_pdf, name='reporte_todas_reservas_pdf'),
    path('reportes/por-cliente-pdf/', views.reporte_por_cliente_pdf, name='reporte_por_cliente_pdf'),
    path('reportes/por-fecha-pdf/', views.reporte_por_fecha_pdf, name='reporte_por_fecha_pdf'),
    
    # API
    path('api/habitaciones-disponibles/', views.api_habitaciones_disponibles, name='api_habitaciones_disponibles'),
    path('api/buscar-cliente/', views.api_buscar_cliente, name='api_buscar_cliente'),
    path('api/crear-cliente/', views.api_crear_cliente, name='api_crear_cliente'),
    path('api/buscar-empresa/', views.api_buscar_empresa, name='api_buscar_empresa'),
    path('api/crear-empresa/', views.api_crear_empresa, name='api_crear_empresa'),
    path('api/extender-hospedada/', views.api_extender_hospedada, name='api_extender_hospedada'),
    path('api/verificar-disponibilidad/', views.api_verificar_disponibilidad, name='api_verificar_disponibilidad'),
    path('api/agregar-ajuste/', views.api_agregar_ajuste, name='api_agregar_ajuste'),
    path('api/eliminar-ajuste/', views.api_eliminar_ajuste, name='api_eliminar_ajuste'),
    path('api/productos/', views.api_productos, name='api_productos'),
    path('api/agregar-servicio/', views.api_agregar_servicio, name='api_agregar_servicio'),
    path('api/tipos-servicio/', views.api_tipos_servicio, name='api_tipos_servicio'),
    path('api/actualizar-inventario/', views.api_actualizar_inventario, name='api_actualizar_inventario'),
]