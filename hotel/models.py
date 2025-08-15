from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class TipoHabitacion(models.Model):
    """Tipos de habitación disponibles en el hotel"""
    nombre = models.CharField(max_length=50, verbose_name="Tipo de Habitación")
    precio_por_noche = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio por Noche"
    )
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    capacidad_personas = models.PositiveIntegerField(default=1, verbose_name="Capacidad de Personas")
    
    class Meta:
        verbose_name = "Tipo de Habitación"
        verbose_name_plural = "Tipos de Habitación"
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio_por_noche}"


class Habitacion(models.Model):
    """Habitaciones del hotel"""
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('mantenimiento', 'En Mantenimiento'),
        ('limpieza', 'En Limpieza'),
    ]
    
    numero = models.CharField(max_length=10, unique=True, verbose_name="Número de Habitación")
    tipo = models.ForeignKey(TipoHabitacion, on_delete=models.CASCADE, verbose_name="Tipo")
    piso = models.PositiveIntegerField(verbose_name="Piso")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible', verbose_name="Estado")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    
    class Meta:
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"
        ordering = ['numero']
    
    def __str__(self):
        return f"Habitación {self.numero} - {self.tipo.nombre}"


class Cliente(models.Model):
    """Clientes del hotel"""
    TIPOS_DOCUMENTO = [
        ('cedula', 'Cédula'),
        ('pasaporte', 'Pasaporte'),
        ('tarjeta_identidad', 'Tarjeta de Identidad'),
    ]
    
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    tipo_documento = models.CharField(max_length=20, choices=TIPOS_DOCUMENTO, verbose_name="Tipo de Documento")
    numero_documento = models.CharField(max_length=50, unique=True, verbose_name="Número de Documento")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de Nacimiento")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['apellido', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.numero_documento}"
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


class Reserva(models.Model):
    """Reservas de habitaciones"""
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('en_curso', 'En Curso'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]
    
    numero_reserva = models.CharField(max_length=20, unique=True, verbose_name="Número de Reserva")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE, verbose_name="Habitación")
    fecha_entrada = models.DateField(verbose_name="Fecha de Entrada")
    fecha_salida = models.DateField(verbose_name="Fecha de Salida")
    numero_huespedes = models.PositiveIntegerField(default=1, verbose_name="Número de Huéspedes")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente', verbose_name="Estado")
    precio_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Precio Total"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario que Creó")
    
    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Reserva {self.numero_reserva} - {self.cliente.nombre_completo}"
    
    def save(self, *args, **kwargs):
        if not self.numero_reserva:
            self.numero_reserva = f"RES{uuid.uuid4().hex[:8].upper()}"
        
        # Calcular precio total basado en días de estancia
        if self.fecha_entrada and self.fecha_salida:
            dias = (self.fecha_salida - self.fecha_entrada).days
            if dias > 0:
                self.precio_total = self.habitacion.tipo.precio_por_noche * dias
        
        super().save(*args, **kwargs)
    
    @property
    def dias_estancia(self):
        if self.fecha_entrada and self.fecha_salida:
            return (self.fecha_salida - self.fecha_entrada).days
        return 0


class CategoriaProducto(models.Model):
    """Categorías de productos del inventario"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    
    class Meta:
        verbose_name = "Categoría de Producto"
        verbose_name_plural = "Categorías de Productos"
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Productos del inventario del hotel"""
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    categoria = models.ForeignKey(CategoriaProducto, on_delete=models.CASCADE, verbose_name="Categoría")
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio"
    )
    stock_actual = models.PositiveIntegerField(default=0, verbose_name="Stock Actual")
    stock_minimo = models.PositiveIntegerField(default=1, verbose_name="Stock Mínimo")
    unidad_medida = models.CharField(max_length=20, default='unidad', verbose_name="Unidad de Medida")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def necesita_reposicion(self):
        return self.stock_actual <= self.stock_minimo


class ConsumoHabitacion(models.Model):
    """Consumos registrados en las habitaciones"""
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, verbose_name="Reserva")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")
    fecha_consumo = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Consumo")
    usuario_registro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario que Registró")
    
    class Meta:
        verbose_name = "Consumo de Habitación"
        verbose_name_plural = "Consumos de Habitación"
        ordering = ['-fecha_consumo']
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.reserva.numero_reserva}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal
        self.precio_unitario = self.producto.precio
        self.subtotal = self.cantidad * self.precio_unitario
        
        # Descontar del inventario
        if self.pk is None:  # Solo al crear, no al actualizar
            self.producto.stock_actual -= self.cantidad
            self.producto.save()
        
        super().save(*args, **kwargs)


class Pago(models.Model):
    """Pagos realizados por las reservas"""
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('cheque', 'Cheque'),
    ]
    
    TIPOS_PAGO = [
        ('abono', 'Abono'),
        ('pago_total', 'Pago Total'),
    ]
    
    numero_pago = models.CharField(max_length=20, unique=True, verbose_name="Número de Pago")
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, verbose_name="Reserva")
    monto = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Monto"
    )
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, verbose_name="Método de Pago")
    tipo_pago = models.CharField(max_length=20, choices=TIPOS_PAGO, verbose_name="Tipo de Pago")
    fecha_pago = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Pago")
    referencia = models.CharField(max_length=100, blank=True, verbose_name="Referencia")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    usuario_registro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario que Registró")
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_pago']
    
    def __str__(self):
        return f"Pago {self.numero_pago} - ${self.monto}"
    
    def save(self, *args, **kwargs):
        if not self.numero_pago:
            self.numero_pago = f"PAG{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class Factura(models.Model):
    """Facturas generadas"""
    numero_factura = models.CharField(max_length=20, unique=True, verbose_name="Número de Factura")
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, verbose_name="Reserva")
    fecha_emision = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Emisión")
    subtotal_habitacion = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal Habitación")
    subtotal_consumos = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Subtotal Consumos")
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Impuestos")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    usuario_emision = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario que Emitió")
    
    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Factura {self.numero_factura} - ${self.total}"
    
    def save(self, *args, **kwargs):
        if not self.numero_factura:
            self.numero_factura = f"FAC{uuid.uuid4().hex[:8].upper()}"
        
        # Calcular totales
        self.subtotal_habitacion = self.reserva.precio_total or 0
        
        # Sumar consumos
        consumos = ConsumoHabitacion.objects.filter(reserva=self.reserva)
        self.subtotal_consumos = sum(consumo.subtotal for consumo in consumos)
        
        # Calcular impuestos (ejemplo: 16% IVA)
        subtotal_antes_impuestos = self.subtotal_habitacion + self.subtotal_consumos
        self.impuestos = subtotal_antes_impuestos * Decimal('0.16')
        
        self.total = subtotal_antes_impuestos + self.impuestos
        
        super().save(*args, **kwargs)