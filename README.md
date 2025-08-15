# Sistema de Gestión Hotelera

Un sistema completo de administración hotelera desarrollado con Django que permite gestionar todas las operaciones de un hotel de manera eficiente.

## 🏨 Características Principales

### 📊 Dashboard Interactivo
- Panel de control con estadísticas en tiempo real
- Gráficos de ocupación y ingresos
- Alertas de stock bajo y notificaciones importantes
- Acciones rápidas para operaciones comunes

### 🛏️ Gestión de Habitaciones
- Control de estado de habitaciones (Disponible, Ocupada, Mantenimiento, Limpieza)
- Diferentes tipos de habitaciones con precios personalizables
- Vista en tarjetas con cambio de estado dinámico
- Filtros por estado, tipo y piso

### 👥 Administración de Clientes
- Registro completo de clientes con documentos de identidad
- Búsqueda avanzada por nombre, documento o email
- Historial de reservas por cliente
- Autocompletado en formularios de reserva

### 📅 Sistema de Reservas
- Creación de reservas con verificación de disponibilidad
- Estados de reserva (Pendiente, Confirmada, En Curso, Finalizada, Cancelada)
- Check-in y check-out automatizado
- Cálculo automático de precios por días de estancia

### 📦 Control de Inventario
- Gestión de productos con categorías
- Control de stock con alertas de reposición
- Registro de consumos por habitación
- Descuento automático de inventario

### 💰 Sistema de Facturación y Pagos
- Generación automática de facturas con desglose detallado
- Múltiples métodos de pago (Efectivo, Tarjetas, Transferencias)
- Registro de abonos y pagos parciales
- Cálculo automático de impuestos (IVA 16%)

### 📈 Reportes y Exportación
- Reportes de ocupación, ingresos y ventas
- Gráficos interactivos con Chart.js
- Exportación a CSV para contabilidad
- Filtros personalizables por fechas

### 🔧 Panel de Administración Django
- Interfaz administrativa completa
- Gestión de usuarios y permisos
- Configuración de tipos de habitación y productos
- Respaldos y mantenimiento de datos

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   # Si tienes git instalado
   git clone <url-del-repositorio>
   cd hotel-management
   
   # O simplemente descomprime el archivo ZIP en una carpeta
   ```

2. **Crear un entorno virtual (recomendado)**
   ```bash
   python -m venv hotel_env
   
   # En Windows
   hotel_env\Scripts\activate
   
   # En Linux/Mac
   source hotel_env/bin/activate
   ```

3. **Instalar las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar la base de datos**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Crear un superusuario (opcional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Cargar datos de ejemplo (opcional)**
   ```bash
   python manage.py loaddata initial_data.json
   ```

7. **Ejecutar el servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

8. **Acceder al sistema**
   - Aplicación principal: http://127.0.0.1:8000/
   - Panel de administración: http://127.0.0.1:8000/admin/

## 📖 Guía de Uso

### Configuración Inicial

1. **Accede al panel de administración** (/admin/) con tu cuenta de superusuario
2. **Configura los tipos de habitación** con sus precios
3. **Crea las habitaciones** asignándoles tipos y pisos
4. **Configura las categorías de productos** para el inventario
5. **Agrega productos** al inventario con precios y stock inicial

### Operaciones Diarias

#### Crear una Nueva Reserva
1. Ve al Dashboard o sección de Reservas
2. Haz clic en "Nueva Reserva"
3. Busca o crea un cliente
4. Selecciona las fechas de entrada y salida
5. Elige una habitación disponible
6. Guarda la reserva

#### Registrar Check-in
1. Ve a la sección de Reservas
2. Filtra por estado "Confirmada"
3. Haz clic en el botón de check-in de la reserva correspondiente
4. La habitación cambiará automáticamente a "Ocupada"

#### Registrar Consumos
1. Ve a la sección de Inventario
2. Selecciona el producto consumido
3. Elige la reserva correspondiente
4. Especifica la cantidad
5. El sistema descontará automáticamente del stock

#### Procesar Pagos
1. Ve al detalle de una reserva
2. Haz clic en "Registrar Pago"
3. Selecciona el método de pago
4. Especifica si es un abono o pago total
5. Agrega referencias si es necesario

#### Generar Facturas
1. Ve al detalle de una reserva
2. Haz clic en "Generar Factura"
3. La factura incluirá hospedaje + consumos + impuestos
4. Puedes imprimir o descargar en PDF

### Gestión de Habitaciones

- **Cambiar estado**: Haz clic en el dropdown de estado en la vista de habitaciones
- **Disponible**: Lista para nuevos huéspedes
- **Ocupada**: Con huéspedes actualmente
- **Mantenimiento**: Fuera de servicio
- **Limpieza**: En proceso de limpieza

### Reportes y Análisis

- **Dashboard**: Estadísticas generales y gráficos en tiempo real
- **Reportes**: Análisis detallado con gráficos interactivos
- **Exportación**: Descarga datos en CSV para contabilidad externa

## 🛠️ Funcionalidades Técnicas

### Arquitectura
- **Backend**: Django 4.2 (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Base de datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Gráficos**: Chart.js
- **Iconos**: Font Awesome 6
- **Alertas**: SweetAlert2

### Modelos de Datos
- **TipoHabitacion**: Configuración de tipos y precios
- **Habitacion**: Habitaciones individuales con estado
- **Cliente**: Información completa de huéspedes
- **Reserva**: Reservas con fechas y estado
- **Producto**: Inventario de productos consumibles
- **ConsumoHabitacion**: Registro de consumos por reserva
- **Pago**: Historial de pagos con métodos
- **Factura**: Facturas generadas con desglose completo

### Seguridad
- Validación de datos en cliente y servidor
- Protección CSRF en formularios
- Sanitización de entradas de usuario
- Control de acceso basado en sesiones

### Responsive Design
- Diseño adaptable a dispositivos móviles
- Sidebar colapsable para tablets
- Tablas responsivas con scroll horizontal
- Formularios optimizados para touch

## 🔧 Personalización

### Configuración de Impuestos
Edita el archivo `hotel/models.py` en la clase `Factura`, método `save()`:
```python
# Cambiar el porcentaje de IVA (ejemplo: 21%)
self.impuestos = subtotal_antes_impuestos * Decimal('0.21')
```

### Agregar Nuevos Campos
1. Modifica el modelo correspondiente en `models.py`
2. Crea y aplica migraciones: `python manage.py makemigrations && python manage.py migrate`
3. Actualiza los formularios y templates según sea necesario

### Personalizar Diseño
- Colores: Modifica las variables CSS en `templates/base.html`
- Logo: Reemplaza el texto en el sidebar con tu logo
- Estilos: Agrega CSS personalizado en `static/css/custom.css`

## 📋 Datos de Ejemplo

El sistema incluye datos de ejemplo para facilitar las pruebas:
- Tipos de habitación: Individual, Doble, Suite, Familiar
- Habitaciones numeradas del 101 al 305
- Categorías de productos: Bebidas, Snacks, Comidas, Amenidades
- Productos básicos con precios

## 🐛 Solución de Problemas

### Error de Migraciones
```bash
python manage.py makemigrations --empty hotel
python manage.py migrate
```

### Error de Permisos
Asegúrate de que el usuario tenga permisos de escritura en la carpeta del proyecto.

### Error de Dependencias
```bash
pip install --upgrade -r requirements.txt
```

### Base de Datos Corrupta
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## 📞 Soporte

Para soporte técnico o consultas:
- Revisa la documentación de Django: https://docs.djangoproject.com/
- Verifica los logs en la consola del servidor
- Consulta la sección de issues del proyecto

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Puedes usarlo, modificarlo y distribuirlo libremente.

## 🤝 Contribuciones

Las contribuciones son bienvenidas:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

---

**¡Disfruta administrando tu hotel con este sistema completo y moderno!** 🏨✨