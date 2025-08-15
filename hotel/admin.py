from django.contrib import admin
from django.utils.html import format_html
from .models import (
    TipoHabitacion, Habitacion, Cliente, Reserva, 
    CategoriaProducto, Producto, ConsumoHabitacion, Pago, Factura
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


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'tipo_documento', 'numero_documento', 'telefono', 'email')
    list_filter = ('tipo_documento', 'fecha_registro')
    search_fields = ('nombre', 'apellido', 'numero_documento', 'email')
    date_hierarchy = 'fecha_registro'


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('numero_reserva', 'cliente', 'habitacion', 'fecha_entrada', 'fecha_salida', 'estado_badge', 'precio_total')
    list_filter = ('estado', 'fecha_entrada', 'habitacion__tipo')
    search_fields = ('numero_reserva', 'cliente__nombre', 'cliente__apellido', 'habitacion__numero')
    date_hierarchy = 'fecha_entrada'
    readonly_fields = ('numero_reserva', 'precio_total', 'fecha_creacion')
    
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
    list_display = ('reserva', 'producto', 'cantidad', 'precio_unitario', 'subtotal', 'fecha_consumo')
    list_filter = ('fecha_consumo', 'producto__categoria')
    search_fields = ('reserva__numero_reserva', 'producto__nombre')
    date_hierarchy = 'fecha_consumo'
    readonly_fields = ('precio_unitario', 'subtotal', 'fecha_consumo')


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('numero_pago', 'reserva', 'monto', 'metodo_pago', 'tipo_pago', 'fecha_pago')
    list_filter = ('metodo_pago', 'tipo_pago', 'fecha_pago')
    search_fields = ('numero_pago', 'reserva__numero_reserva', 'referencia')
    date_hierarchy = 'fecha_pago'
    readonly_fields = ('numero_pago', 'fecha_pago')


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero_factura', 'reserva', 'fecha_emision', 'subtotal_habitacion', 'subtotal_consumos', 'total')
    list_filter = ('fecha_emision',)
    search_fields = ('numero_factura', 'reserva__numero_reserva')
    date_hierarchy = 'fecha_emision'
    readonly_fields = ('numero_factura', 'fecha_emision', 'subtotal_habitacion', 'subtotal_consumos', 'impuestos', 'total')


# Configuración del sitio admin
admin.site.site_header = 'Sistema de Gestión Hotelera'
admin.site.site_title = 'Hotel Admin'
admin.site.index_title = 'Panel de Administración'