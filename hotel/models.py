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


class Empresa(models.Model):
    """Empresas asociadas a clientes"""
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Empresa")
    rfc = models.CharField(max_length=20, unique=True, verbose_name="RFC")
    direccion = models.TextField(verbose_name="Dirección")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Email")
    contacto = models.CharField(max_length=100, blank=True, verbose_name="Persona de Contacto")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.rfc}"


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
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Empresa Asociada")
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


class Hospedada(models.Model):
    """Hospedadas de habitaciones"""
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('en_curso', 'En Curso'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]
    
    TIPOS_HOSPEDADA = [
        ('continua', 'Hospedada Continua'),
        ('por_rato', 'Hospedada Por Rato'),
    ]
    
    numero_hospedada = models.CharField(max_length=20, unique=True, verbose_name="Número de Hospedada")
    tipo_hospedada = models.CharField(max_length=20, choices=TIPOS_HOSPEDADA, default='continua', verbose_name="Tipo de Hospedada")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Empresa")
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE, verbose_name="Habitación")
    fecha_entrada = models.DateField(verbose_name="Fecha de Entrada")
    fecha_salida = models.DateField(null=True, blank=True, verbose_name="Fecha de Salida")
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
    
    # Campos para gestión de deudas
    tiene_deuda = models.BooleanField(default=False, verbose_name="Tiene Deuda")
    monto_deuda = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Monto de Deuda"
    )
    deudor = models.CharField(
        max_length=20, 
        choices=[('cliente', 'Cliente'), ('empresa', 'Empresa')],
        blank=True,
        verbose_name="Deudor"
    )
    fecha_checkout = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Checkout")
    observaciones_deuda = models.TextField(blank=True, verbose_name="Observaciones de Deuda")
    
    class Meta:
        verbose_name = "Hospedada"
        verbose_name_plural = "Hospedadas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Hospedada {self.numero_hospedada} - {self.cliente.nombre_completo}"
    
    def save(self, *args, **kwargs):
        if not self.numero_hospedada:
            prefix = "HOS" if self.tipo_hospedada == 'continua' else "HOR"
            self.numero_hospedada = f"{prefix}{uuid.uuid4().hex[:8].upper()}"
        
        # Calcular precio total basado en días de estancia
        if self.fecha_entrada and self.fecha_salida:
            dias = (self.fecha_salida - self.fecha_entrada).days
            if dias > 0:
                self.precio_total = self.habitacion.tipo.precio_por_noche * dias
        else:
            # Para reservas indefinidas, cobrar al menos una noche desde el inicio
            from datetime import date
            if self.fecha_entrada:
                # Calcular días desde la entrada hasta hoy (mínimo 1 día)
                dias_transcurridos = max(1, (date.today() - self.fecha_entrada).days + 1)
                self.precio_total = self.habitacion.tipo.precio_por_noche * dias_transcurridos
            else:
                self.precio_total = None
        
        super().save(*args, **kwargs)
    
    @property
    def dias_estancia(self):
        if self.fecha_entrada and self.fecha_salida:
            return (self.fecha_salida - self.fecha_entrada).days
        return 0
    
    @property
    def es_indefinida(self):
        """Indica si la hospedada tiene fecha de salida indefinida"""
        return self.fecha_salida is None
    
    def calcular_precio_hasta_fecha(self, fecha_hasta=None):
        """Calcula el precio desde la entrada hasta una fecha específica"""
        from datetime import date
        if not fecha_hasta:
            fecha_hasta = date.today()
        
        if self.fecha_entrada:
            dias = (fecha_hasta - self.fecha_entrada).days
            if dias > 0:
                return self.habitacion.tipo.precio_por_noche * dias
        return 0
    
    @property
    def subtotal_consumos(self):
        """Calcula el subtotal de consumos"""
        return sum(c.subtotal for c in self.consumohabitacion_set.all())
    
    @property
    def subtotal_servicios(self):
        """Calcula el subtotal de servicios adicionales"""
        return sum(s.subtotal for s in self.servicios.all())
    
    @property
    def subtotal_ajustes(self):
        """Calcula el subtotal de ajustes (extras - descuentos)"""
        from decimal import Decimal
        subtotal_base = (self.precio_total or 0) + self.subtotal_consumos + self.subtotal_servicios
        total_ajustes = Decimal('0')
        
        for ajuste in self.ajustes_precio.filter(activo=True):
            monto_ajuste = ajuste.calcular_monto_final(subtotal_base)
            if ajuste.tipo == 'extra':
                total_ajustes += monto_ajuste
            else:  # descuento
                total_ajustes -= monto_ajuste
        
        return total_ajustes
    
    @property
    def total_con_ajustes(self):
        """Calcula el total incluyendo habitación, consumos y ajustes"""
        # Para hospedadas indefinidas, actualizar precio antes de calcular total
        if self.es_indefinida:
            self.actualizar_precio_indefinida()
        
        return (self.precio_total or 0) + self.subtotal_consumos + self.subtotal_servicios + self.subtotal_ajustes
    
    def actualizar_precio_indefinida(self):
        """Actualiza el precio para hospedadas indefinidas basado en días transcurridos"""
        if self.es_indefinida and self.fecha_entrada:
            from datetime import date
            dias_transcurridos = max(1, (date.today() - self.fecha_entrada).days + 1)
            nuevo_precio = self.habitacion.tipo.precio_por_noche * dias_transcurridos
            if self.precio_total != nuevo_precio:
                self.precio_total = nuevo_precio
                self.save()
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente considerando ajustes"""
        # Para hospedadas indefinidas, actualizar precio antes de calcular saldo
        if self.es_indefinida:
            self.actualizar_precio_indefinida()
        
        total_pagos = sum(p.monto for p in self.pago_set.all())
        return self.total_con_ajustes - total_pagos
    
    def realizar_checkout(self, pagar_todo=False, deudor=None, observaciones_deuda=''):
        """Realiza el checkout de la hospedada"""
        from django.utils import timezone
        
        # Actualizar fecha de checkout
        self.fecha_checkout = timezone.now()
        
        # Calcular saldo pendiente
        saldo = self.saldo_pendiente
        
        if saldo > 0 and not pagar_todo:
            # Registrar deuda
            self.tiene_deuda = True
            self.monto_deuda = saldo
            self.deudor = deudor or ('empresa' if self.empresa else 'cliente')
            self.observaciones_deuda = observaciones_deuda
        else:
            # Sin deuda o se pagó todo
            self.tiene_deuda = False
            self.monto_deuda = 0
            self.deudor = ''
            self.observaciones_deuda = ''
        
        # Cambiar estado
        self.estado = 'finalizada'
        
        # Liberar habitación
        self.habitacion.estado = 'limpieza'
        self.habitacion.save()
        
        self.save()
        return self


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
    hospedada = models.ForeignKey('Hospedada', on_delete=models.CASCADE, verbose_name="Hospedada")
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
        return f"{self.producto.nombre} - {self.hospedada.numero_hospedada}"
    
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
    """Pagos realizados por las hospedadas"""
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
    
    PAGADO_POR = [
        ('cliente', 'Cliente'),
        ('empresa', 'Empresa'),
    ]
    
    numero_pago = models.CharField(max_length=20, unique=True, verbose_name="Número de Pago")
    hospedada = models.ForeignKey('Hospedada', on_delete=models.CASCADE, verbose_name="Hospedada")
    pagado_por = models.CharField(max_length=20, choices=PAGADO_POR, default='cliente', verbose_name="Pagado Por")
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


class AjustePrecio(models.Model):
    """Ajustes de precio para hospedadas (extras y descuentos)"""
    TIPOS_AJUSTE = [
        ('extra', 'Cargo Extra'),
        ('descuento', 'Descuento'),
    ]
    
    hospedada = models.ForeignKey('Hospedada', on_delete=models.CASCADE, verbose_name="Hospedada", related_name='ajustes_precio')
    tipo = models.CharField(max_length=20, choices=TIPOS_AJUSTE, verbose_name="Tipo de Ajuste")
    concepto = models.CharField(max_length=200, verbose_name="Concepto")
    monto = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Monto"
    )
    porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Porcentaje"
    )
    es_porcentaje = models.BooleanField(default=False, verbose_name="¿Es porcentaje?")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario que Creó")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Ajuste de Precio"
        verbose_name_plural = "Ajustes de Precio"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        signo = '+' if self.tipo == 'extra' else '-'
        if self.es_porcentaje:
            return f"{signo}{self.porcentaje}% - {self.concepto}"
        else:
            return f"{signo}${self.monto} - {self.concepto}"
    
    def calcular_monto_final(self, subtotal_base):
        """Calcula el monto final del ajuste basado en el subtotal"""
        if self.es_porcentaje:
            return subtotal_base * (self.porcentaje / 100)
        else:
            return self.monto
    
    @property
    def monto_calculado(self):
        """Retorna el monto calculado para mostrar en la interfaz"""
        if self.es_porcentaje and self.hospedada:
            subtotal = (self.hospedada.precio_total or 0) + sum(
                c.subtotal for c in ConsumoHabitacion.objects.filter(hospedada=self.hospedada)
            )
            return self.calcular_monto_final(subtotal)
        return self.monto


class Factura(models.Model):
    """Facturas generadas"""
    numero_factura = models.CharField(max_length=20, unique=True, verbose_name="Número de Factura")
    hospedada = models.OneToOneField('Hospedada', on_delete=models.CASCADE, verbose_name="Hospedada")
    fecha_emision = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Emisión")
    subtotal_habitacion = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal Habitación")
    subtotal_consumos = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Subtotal Consumos")
    subtotal_ajustes = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Subtotal Ajustes")
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
        self.subtotal_habitacion = self.hospedada.precio_total or 0
        
        # Sumar consumos
        consumos = ConsumoHabitacion.objects.filter(hospedada=self.hospedada)
        self.subtotal_consumos = sum(consumo.subtotal for consumo in consumos)
        
        # Calcular ajustes de precio
        subtotal_base = self.subtotal_habitacion + self.subtotal_consumos
        ajustes = AjustePrecio.objects.filter(hospedada=self.hospedada, activo=True)
        
        total_ajustes = Decimal('0')
        for ajuste in ajustes:
            monto_ajuste = ajuste.calcular_monto_final(subtotal_base)
            if ajuste.tipo == 'extra':
                total_ajustes += monto_ajuste
            else:  # descuento
                total_ajustes -= monto_ajuste
        
        self.subtotal_ajustes = total_ajustes
        
        # Calcular impuestos (ejemplo: 16% IVA)
        subtotal_antes_impuestos = subtotal_base + total_ajustes
        self.impuestos = subtotal_antes_impuestos * Decimal('0.16')
        
        self.total = subtotal_antes_impuestos + self.impuestos
        
        super().save(*args, **kwargs)


class Reserva(models.Model):
    """Reservas de habitaciones (previas a hospedadas)"""
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('convertida', 'Convertida a Hospedada'),
    ]
    
    numero_reserva = models.CharField(max_length=20, unique=True, verbose_name="Número de Reserva")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Empresa")
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE, verbose_name="Habitación")
    fecha_entrada_prevista = models.DateField(verbose_name="Fecha de Entrada Prevista")
    fecha_salida_prevista = models.DateField(verbose_name="Fecha de Salida Prevista")
    numero_huespedes = models.PositiveIntegerField(default=1, verbose_name="Número de Huéspedes")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente', verbose_name="Estado")
    precio_acordado = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Precio Acordado"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario que Creó")
    hospedada_convertida = models.OneToOneField(
        'Hospedada', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reserva_origen',
        verbose_name="Hospedada Resultante"
    )
    
    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Reserva {self.numero_reserva} - {self.cliente.nombre_completo}"
    
    def save(self, *args, **kwargs):
        if not self.numero_reserva:
            self.numero_reserva = f"RES{uuid.uuid4().hex[:8].upper()}"
        
        # Calcular precio acordado basado en días de estancia
        if self.fecha_entrada_prevista and self.fecha_salida_prevista and not self.precio_acordado:
            dias = (self.fecha_salida_prevista - self.fecha_entrada_prevista).days
            if dias > 0:
                self.precio_acordado = self.habitacion.tipo.precio_por_noche * dias
        
        super().save(*args, **kwargs)
    
    @property
    def dias_estancia_previstos(self):
        if self.fecha_entrada_prevista and self.fecha_salida_prevista:
            return (self.fecha_salida_prevista - self.fecha_entrada_prevista).days
        return 0
    
    def verificar_disponibilidad(self):
        """Verifica si la habitación está disponible para las fechas solicitadas"""
        from django.db.models import Q
        
        # Verificar contra otras reservas activas
        reservas_conflicto = Reserva.objects.filter(
            habitacion=self.habitacion,
            estado__in=['pendiente', 'confirmada']
        ).exclude(pk=self.pk)
        
        # Verificar solapamiento de fechas con reservas
        for reserva in reservas_conflicto:
            if (self.fecha_entrada_prevista <= reserva.fecha_salida_prevista and 
                self.fecha_salida_prevista >= reserva.fecha_entrada_prevista):
                return False, f"Conflicto con reserva {reserva.numero_reserva}"
        
        # Verificar contra hospedadas actuales
        hospedadas_conflicto = Hospedada.objects.filter(
            habitacion=self.habitacion,
            estado__in=['confirmada', 'en_curso']
        )
        
        for hospedada in hospedadas_conflicto:
            # Si la hospedada tiene fecha de salida
            if hospedada.fecha_salida:
                if (self.fecha_entrada_prevista <= hospedada.fecha_salida and 
                    self.fecha_salida_prevista >= hospedada.fecha_entrada):
                    return False, f"Conflicto con hospedada {hospedada.numero_hospedada}"
            else:
                # Si la hospedada es indefinida, verificar solo contra fecha de entrada
                if self.fecha_entrada_prevista <= hospedada.fecha_entrada:
                    return False, f"Conflicto con hospedada indefinida {hospedada.numero_hospedada}"
        
        return True, "Habitación disponible"
    
    def convertir_a_hospedada(self, tipo_hospedada='continua', usuario=None):
        """Convierte esta reserva en una hospedada"""
        if self.estado == 'convertida':
            raise ValueError("Esta reserva ya ha sido convertida a hospedada")
        
        # Crear la hospedada
        hospedada = Hospedada.objects.create(
            tipo_hospedada=tipo_hospedada,
            cliente=self.cliente,
            empresa=self.empresa,
            habitacion=self.habitacion,
            fecha_entrada=self.fecha_entrada_prevista,
            fecha_salida=self.fecha_salida_prevista,
            numero_huespedes=self.numero_huespedes,
            estado='confirmada',
            precio_total=self.precio_acordado,
            observaciones=f"Convertida desde reserva {self.numero_reserva}. {self.observaciones}",
            usuario_creacion=usuario
        )
        
        # Actualizar la reserva
        self.estado = 'convertida'
        self.hospedada_convertida = hospedada
        self.save()
        
        # Actualizar estado de la habitación
        self.habitacion.estado = 'ocupada'
        self.habitacion.save()
        
        return hospedada


class ElementoInventario(models.Model):
    """Catálogo de elementos que pueden estar en las habitaciones"""
    CATEGORIAS = [
        ('basico', 'Básico'),
        ('sexshop', 'Sex Shop'),
        ('premium', 'Premium'),
        ('limpieza', 'Limpieza'),
        ('tecnologia', 'Tecnología'),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Elemento")
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='basico', verbose_name="Categoría")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    costo_reposicion = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Costo de Reposición"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Elemento de Inventario"
        verbose_name_plural = "Elementos de Inventario"
        ordering = ['categoria', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"


class InventarioHabitacion(models.Model):
    """Inventario específico de cada habitación"""
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE, related_name='inventario', verbose_name="Habitación")
    elemento = models.ForeignKey(ElementoInventario, on_delete=models.CASCADE, verbose_name="Elemento")
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    estado = models.CharField(
        max_length=20,
        choices=[
            ('bueno', 'Bueno'),
            ('regular', 'Regular'),
            ('malo', 'Malo'),
            ('faltante', 'Faltante'),
        ],
        default='bueno',
        verbose_name="Estado"
    )
    ultima_revision = models.DateTimeField(auto_now=True, verbose_name="Última Revisión")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    class Meta:
        verbose_name = "Inventario de Habitación"
        verbose_name_plural = "Inventarios de Habitaciones"
        unique_together = ['habitacion', 'elemento']
        ordering = ['habitacion', 'elemento__categoria', 'elemento__nombre']
    
    def __str__(self):
        return f"{self.habitacion.numero} - {self.elemento.nombre} ({self.cantidad})"


class FaltanteCheckout(models.Model):
    """Registro de elementos faltantes al hacer checkout"""
    hospedada = models.ForeignKey('Hospedada', on_delete=models.CASCADE, related_name='faltantes', verbose_name="Hospedada")
    elemento = models.ForeignKey(ElementoInventario, on_delete=models.CASCADE, verbose_name="Elemento")
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad Faltante")
    costo_cobrado = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Costo Cobrado"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Registrado Por")
    
    class Meta:
        verbose_name = "Faltante en Checkout"
        verbose_name_plural = "Faltantes en Checkout"
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.hospedada.numero_hospedada} - {self.elemento.nombre} ({self.cantidad})"


class TipoServicio(models.Model):
    """Tipos de servicios adicionales disponibles"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Servicio")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    precio_sugerido = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Precio Sugerido"
    )
    requiere_precio = models.BooleanField(default=True, verbose_name="Requiere Precio Manual")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    icono = models.CharField(max_length=50, default='fas fa-concierge-bell', verbose_name="Icono (Font Awesome)")
    
    class Meta:
        verbose_name = "Tipo de Servicio"
        verbose_name_plural = "Tipos de Servicios"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class ServicioHospedada(models.Model):
    """Servicios adicionales consumidos en una hospedada"""
    hospedada = models.ForeignKey('Hospedada', on_delete=models.CASCADE, related_name='servicios', verbose_name="Hospedada")
    tipo_servicio = models.ForeignKey(TipoServicio, on_delete=models.CASCADE, verbose_name="Tipo de Servicio")
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Precio"
    )
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    fecha_servicio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Servicio")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Registrado Por")
    
    class Meta:
        verbose_name = "Servicio de Hospedada"
        verbose_name_plural = "Servicios de Hospedadas"
        ordering = ['-fecha_servicio']
    
    def __str__(self):
        return f"{self.hospedada.numero_hospedada} - {self.tipo_servicio.nombre}"
    
    @property
    def subtotal(self):
        return self.precio * self.cantidad