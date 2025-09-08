from django.contrib import admin
from django.utils.html import format_html
from .models import (
    TipoHabitacion, Habitacion, Cliente, Hospedada, Empresa, Reserva,
    CategoriaProducto, Producto, ConsumoHabitacion, Pago, Factura,
    ElementoInventario, InventarioHabitacion, TipoServicio, ServicioHospedada, FaltanteCheckout
)


@admin.register(TipoHabitacion)
class TipoHabitacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_por_noche', 'capacidad_personas')
    list_filter = ('capacidad_personas',)
    search_fields = ('nombre',)


@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo', 'piso', 'estado', 'estado_badge')
    list_filter = ('estado', 'tipo', 'piso')
    search_fields = ('numero',)
    list_editable = ('estado',)
    
    def estado_badge(self, obj):
        colors = {
            'disponible': 'green',
            'ocupada': 'red',
            'mantenimiento': 'orange',
            'limpieza': 'blue'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rfc', 'telefono', 'email', 'contacto', 'activa')
    list_filter = ('activa', 'fecha_registro')
    search_fields = ('nombre', 'rfc', 'email')
    date_hierarchy = 'fecha_registro'


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'tipo_documento', 'numero_documento', 'telefono', 'email', 'empresa')
    list_filter = ('tipo_documento', 'fecha_registro', 'empresa')
    search_fields = ('nombre', 'apellido', 'numero_documento', 'email')
    date_hierarchy = 'fecha_registro'


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('numero_reserva', 'cliente', 'empresa', 'habitacion', 'fecha_entrada_prevista', 'fecha_salida_prevista', 'estado_badge', 'precio_acordado')
    list_filter = ('estado', 'fecha_entrada_prevista', 'habitacion__tipo')
    search_fields = ('numero_reserva', 'cliente__nombre', 'cliente__apellido', 'habitacion__numero')
    date_hierarchy = 'fecha_entrada_prevista'
    readonly_fields = ('numero_reserva', 'fecha_creacion', 'hospedada_convertida')
    
    def estado_badge(self, obj):
        colors = {
            'pendiente': 'orange',
            'confirmada': 'blue',
            'cancelada': 'red',
            'convertida': 'green'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'


# Registramos para Hospedada pero mantenemos compatibilidad con el nombre anterior
@admin.register(Hospedada)
class HospedadaAdmin(admin.ModelAdmin):
    list_display = ('numero_hospedada', 'tipo_hospedada', 'cliente', 'empresa', 'habitacion', 'fecha_entrada', 'fecha_salida', 'estado_badge', 'precio_total')
    list_filter = ('estado', 'tipo_hospedada', 'fecha_entrada', 'habitacion__tipo')
    search_fields = ('numero_hospedada', 'cliente__nombre', 'cliente__apellido', 'habitacion__numero')
    date_hierarchy = 'fecha_entrada'
    readonly_fields = ('numero_hospedada', 'precio_total', 'fecha_creacion')
    
    def estado_badge(self, obj):
        colors = {
            'pendiente': 'orange',
            'confirmada': 'blue',
            'en_curso': 'green',
            'finalizada': 'gray',
            'cancelada': 'red'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'precio', 'stock_actual', 'stock_minimo', 'estado_stock', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre')
    list_editable = ('precio', 'stock_actual', 'activo')
    
    def estado_stock(self, obj):
        if obj.necesita_reposicion:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px;">Stock Bajo</span>'
            )
        else:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px;">Stock OK</span>'
            )
    estado_stock.short_description = 'Estado Stock'


@admin.register(ConsumoHabitacion)
class ConsumoHabitacionAdmin(admin.ModelAdmin):
    list_display = ('hospedada', 'producto', 'cantidad', 'precio_unitario', 'subtotal', 'fecha_consumo')
    list_filter = ('fecha_consumo', 'producto__categoria')
    search_fields = ('hospedada__numero_hospedada', 'producto__nombre')
    date_hierarchy = 'fecha_consumo'
    readonly_fields = ('precio_unitario', 'subtotal', 'fecha_consumo')


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('numero_pago', 'hospedada', 'monto', 'metodo_pago', 'tipo_pago', 'pagado_por', 'fecha_pago')
    list_filter = ('metodo_pago', 'tipo_pago', 'pagado_por', 'fecha_pago')
    search_fields = ('numero_pago', 'hospedada__numero_hospedada', 'referencia')
    date_hierarchy = 'fecha_pago'
    readonly_fields = ('numero_pago', 'fecha_pago')


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero_factura', 'hospedada', 'fecha_emision', 'subtotal_habitacion', 'subtotal_consumos', 'total')
    list_filter = ('fecha_emision',)
    search_fields = ('numero_factura', 'hospedada__numero_hospedada')
    date_hierarchy = 'fecha_emision'
    readonly_fields = ('numero_factura', 'fecha_emision', 'subtotal_habitacion', 'subtotal_consumos', 'impuestos', 'total')


@admin.register(ElementoInventario)
class ElementoInventarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'costo_reposicion', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre',)
    list_editable = ('costo_reposicion', 'activo')


@admin.register(InventarioHabitacion)
class InventarioHabitacionAdmin(admin.ModelAdmin):
    list_display = ('habitacion', 'elemento', 'cantidad', 'estado')
    list_filter = ('habitacion', 'estado', 'elemento__categoria')
    search_fields = ('habitacion__numero', 'elemento__nombre')
    list_editable = ('cantidad', 'estado')


@admin.register(TipoServicio)
class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_sugerido', 'requiere_precio', 'activo')
    list_filter = ('activo', 'requiere_precio')
    search_fields = ('nombre',)
    list_editable = ('precio_sugerido', 'activo')


@admin.register(ServicioHospedada)
class ServicioHospedadaAdmin(admin.ModelAdmin):
    list_display = ('hospedada', 'tipo_servicio', 'cantidad', 'precio', 'get_subtotal', 'fecha_servicio')
    list_filter = ('fecha_servicio', 'tipo_servicio')
    search_fields = ('hospedada__numero_hospedada', 'tipo_servicio__nombre')
    date_hierarchy = 'fecha_servicio'
    readonly_fields = ('fecha_servicio',)
    
    def get_subtotal(self, obj):
        return obj.subtotal
    get_subtotal.short_description = 'Subtotal'


@admin.register(FaltanteCheckout)
class FaltanteCheckoutAdmin(admin.ModelAdmin):
    list_display = ('hospedada', 'elemento', 'cantidad', 'costo_cobrado', 'fecha_registro')
    list_filter = ('fecha_registro',)
    search_fields = ('hospedada__numero_hospedada', 'elemento__nombre')
    date_hierarchy = 'fecha_registro'
    readonly_fields = ('fecha_registro',)


# Configuración del sitio admin
admin.site.site_header = 'Sistema de Gestión Hotelera'
admin.site.site_title = 'Hotel Admin'
admin.site.index_title = 'Panel de Administración'