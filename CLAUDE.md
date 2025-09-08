# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based hotel management system that handles room reservations, inventory, billing, and reporting. It runs on Python 3.8+ with SQLite for development and PostgreSQL for production.

## Commands

### Development Server
```bash
# Activate virtual environment (Windows)
hotel_env\Scripts\activate

# Run development server
python manage.py runserver
```

### Database Management
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Load example data (optional)
python crear_datos_ejemplo.py
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# The application runs on https://hotel2.corpofuturo.org in production
```

## Architecture

### Django Application Structure
- **Main Project**: `hotel_management/` - Django project settings and configuration
- **Main App**: `hotel/` - Core hotel management application
  - `models.py`: Data models for rooms, clients, reservations, products, payments, and invoices
  - `views.py`: Business logic and request handlers
  - `urls.py`: URL routing configuration
  - `admin.py`: Django admin interface customization

### Key Models and Relationships
- **TipoHabitacion** → **Habitacion**: Room types define pricing, rooms have specific numbers and floors
- **Cliente** → **Reserva**: Clients make reservations
- **Reserva** → **ConsumoHabitacion**: Tracks product consumption during stays
- **Reserva** → **Pago**: Multiple payments can be made for a reservation
- **Reserva** → **Factura**: Invoices generated with automatic tax calculation (16% IVA)

### Frontend Structure
- **Templates**: `templates/hotel/` - Django templates with Bootstrap 5
- **Base Template**: `templates/base.html` - Main layout with sidebar navigation
- **JavaScript**: Inline in templates, uses jQuery, Chart.js, and SweetAlert2
- **No separate frontend build process** - Static files served directly by Django

### Database
- **Development**: SQLite (`db.sqlite3`)
- **Production**: PostgreSQL (configured in docker-compose.yml)
- **Settings**: Database configuration in `hotel_management/settings.py`

## Important Configuration

### Tax Calculation
IVA tax rate (16%) is hardcoded in `hotel/models.py:Factura.save()` method. Modify here to change tax percentage.

### Allowed Hosts
Production domains are configured in `settings.py:ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.

### Time Zone
Set to `America/Mexico_City` in settings.py. Date format is configured as DD/MM/YYYY.

## Development Guidelines

### When Modifying Models
1. Always create migrations: `python manage.py makemigrations`
2. Apply migrations: `python manage.py migrate`
3. Update related views and templates if needed

### When Adding Features
1. Check existing patterns in `hotel/views.py` for similar functionality
2. Follow URL naming convention in `hotel/urls.py` (e.g., `hotel:feature_name`)
3. Use existing templates as reference for UI consistency

### Testing Changes
1. Use the existing test scripts in the root directory (e.g., `probar_botones_reserva.py`)
2. Load example data with `crear_datos_ejemplo.py` for testing
3. Access admin panel at `/admin/` to verify data changes

## Common Tasks

### Check Room Availability
Rooms have states: disponible, ocupada, mantenimiento, limpieza. State changes are handled via AJAX in the habitaciones template.

### Process Reservations
1. Create reservation → State: pendiente
2. Confirm → State: confirmada
3. Check-in → State: en_curso, Room: ocupada
4. Check-out → State: finalizada, Room: disponible

### Handle Payments
Payments support multiple methods (cash, card, transfer) and partial payments (abonos). Full payment history is tracked per reservation.

### Generate Reports
Reports available at `/reportes/` with PDF export functionality using ReportLab 3.6.13 (compatible with Python 3.8).