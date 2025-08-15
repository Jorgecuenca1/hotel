# 🏨 INSTRUCCIONES DE INSTALACIÓN Y USO - SISTEMA HOTELERO

## ✅ Estado del Proyecto
¡El sistema está **COMPLETAMENTE FUNCIONAL** con entorno virtual configurado y listo para usar!

## 🚀 Cómo Ejecutar el Sistema

### **🎯 MÉTODO FÁCIL - Archivo de Inicio Automático**
1. **Hacer doble clic en `INICIAR_HOTEL.bat`**
   - Se activará automáticamente el entorno virtual
   - Se verificarán las migraciones
   - Se iniciará el servidor
   - ¡Listo para usar!

### **🔧 MÉTODO MANUAL**

#### 1. **Abrir Terminal/PowerShell en la carpeta del proyecto**
```bash
cd C:\Users\ROOM04\Documents\hotel
```

#### 2. **Activar el entorno virtual**
```bash
hotel_env\Scripts\activate
```

#### 3. **Ejecutar el servidor**
```bash
python manage.py runserver
```

### **🌐 Acceder al sistema**
- **Aplicación principal**: http://127.0.0.1:8000/
- **Panel de administración**: http://127.0.0.1:8000/admin/

### **🔐 Credenciales de Administrador**
- **Usuario**: `admin`
- **Contraseña**: `admin123`

## 🎯 Sistema Completamente Configurado

### ✅ Lo que YA está listo:
- ✅ Base de datos SQLite configurada y migrada
- ✅ 15 habitaciones creadas (pisos 1-3, números 101-305)
- ✅ 4 tipos de habitación (Individual, Doble, Suite, Familiar)
- ✅ 13 productos en inventario con stock
- ✅ 4 categorías de productos
- ✅ 3 clientes de ejemplo
- ✅ Frontend moderno y responsivo
- ✅ Todas las funcionalidades implementadas

### 📱 Funcionalidades Principales:

#### 🏠 **Dashboard**
- Estadísticas en tiempo real
- Gráficos de ocupación
- Acciones rápidas
- Alertas de stock bajo

#### 🛏️ **Gestión de Habitaciones**
- Ver estado en tiempo real
- Cambiar estados (Disponible/Ocupada/Mantenimiento/Limpieza)
- Filtros por tipo, piso y estado
- Vista de tarjetas intuitiva

#### 👥 **Gestión de Clientes**
- Registro completo con documentos
- Búsqueda avanzada
- Historial de reservas
- Formularios validados

#### 📅 **Sistema de Reservas**
- Verificación de disponibilidad automática
- Check-in y check-out
- Estados de reserva
- Cálculo automático de precios

#### 📦 **Control de Inventario**
- Gestión de productos por categorías
- Control de stock con alertas
- Registro de consumos
- Descuento automático

#### 💰 **Facturación y Pagos**
- Generación automática de facturas
- Múltiples métodos de pago
- Cálculo de impuestos (16% IVA)
- Historial de pagos

#### 📊 **Reportes**
- Gráficos interactivos
- Exportación a CSV
- Estadísticas de ocupación
- Análisis de ingresos

## 🔧 Crear Superusuario (Opcional)

Para acceder al panel de administración:

```bash
python manage.py createsuperuser
```

Seguir las instrucciones para crear usuario y contraseña.

## 📋 Datos de Ejemplo Incluidos

### 🏨 Habitaciones:
- **Piso 1**: 101, 102, 103, 104, 105
- **Piso 2**: 201, 202, 203, 204, 205  
- **Piso 3**: 301, 302, 303, 304, 305

### 🛏️ Tipos de Habitación:
- **Individual**: $80/noche (1 persona)
- **Doble**: $120/noche (2 personas)
- **Suite**: $200/noche (4 personas)
- **Familiar**: $150/noche (6 personas)

### 📦 Productos en Inventario:
- **Bebidas**: Agua, refrescos, cerveza, jugos
- **Snacks**: Papas, cacahuates, chocolate
- **Comidas**: Sandwich, ensalada, pizza
- **Amenidades**: Kit de aseo, toallas, almohadas

### 👤 Clientes de Ejemplo:
- **Juan Carlos Pérez García** (Cédula: 12345678)
- **María Elena González López** (Cédula: 87654321)
- **Carlos Roberto Martínez Silva** (Pasaporte: P123456789)

## 🎮 Cómo Usar el Sistema

### **1. Crear una Nueva Reserva:**
1. Ir al Dashboard
2. Hacer clic en "Nueva Reserva"
3. Buscar cliente (o crear uno nuevo)
4. Seleccionar fechas
5. Elegir habitación disponible
6. Guardar

### **2. Registrar Check-in:**
1. Ir a Reservas
2. Filtrar por estado "Confirmada"
3. Hacer clic en el botón de check-in
4. La habitación cambia automáticamente a "Ocupada"

### **3. Registrar Consumos:**
1. Ir a Inventario
2. Seleccionar producto
3. Elegir la reserva
4. Especificar cantidad
5. Se descuenta automáticamente del stock

### **4. Procesar Pagos:**
1. Ir al detalle de una reserva
2. Hacer clic en "Registrar Pago"
3. Especificar método y monto
4. Guardar

### **5. Generar Facturas:**
1. Ir al detalle de una reserva
2. Hacer clic en "Generar Factura"
3. Se incluyen hospedaje + consumos + impuestos
4. Imprimir o descargar

## 🎨 Características del Diseño

- **Diseño moderno** con gradientes y animaciones
- **Completamente responsivo** (móvil, tablet, desktop)
- **Sidebar colapsable** para más espacio
- **Gráficos interactivos** con Chart.js
- **Notificaciones elegantes** con SweetAlert2
- **Colores consistentes** y tipografía moderna
- **Iconos Font Awesome** en toda la interfaz

## 🔒 Seguridad Implementada

- Validación de datos en cliente y servidor
- Protección CSRF en formularios
- Sanitización de entradas
- Control de sesiones

## 📱 Compatibilidad

- ✅ Google Chrome
- ✅ Mozilla Firefox  
- ✅ Microsoft Edge
- ✅ Safari
- ✅ Dispositivos móviles
- ✅ Tablets

## 🆘 Solución de Problemas

### **Error: No module named 'django'**
```bash
pip install -r requirements.txt
```

### **Error: Port already in use**
```bash
python manage.py runserver 8001
```

### **Error de migraciones**
```bash
python manage.py migrate
```

### **Limpiar caché del navegador**
- Ctrl + F5 (Windows/Linux)
- Cmd + Shift + R (Mac)

## 🎉 ¡Listo para Usar!

El sistema está **100% funcional** con:
- ✅ Frontend moderno y profesional
- ✅ Backend robusto con Django
- ✅ Base de datos configurada
- ✅ Datos de ejemplo incluidos
- ✅ Todas las funcionalidades implementadas
- ✅ Responsive design
- ✅ Documentación completa

**¡Simplemente ejecuta `python manage.py runserver` y comienza a administrar tu hotel!** 🏨✨

---

**Desarrollado con ❤️ para la gestión hotelera moderna**