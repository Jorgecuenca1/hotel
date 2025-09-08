# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0003_factura_subtotal_ajustes_ajusteprecio'),
    ]

    operations = [
        # Crear modelo Empresa
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre de la Empresa')),
                ('rfc', models.CharField(max_length=20, unique=True, verbose_name='RFC')),
                ('direccion', models.TextField(verbose_name='Dirección')),
                ('telefono', models.CharField(max_length=20, verbose_name='Teléfono')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('contacto', models.CharField(blank=True, max_length=100, verbose_name='Persona de Contacto')),
                ('activa', models.BooleanField(default=True, verbose_name='Activa')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')),
            ],
            options={
                'verbose_name': 'Empresa',
                'verbose_name_plural': 'Empresas',
                'ordering': ['nombre'],
            },
        ),
        
        # Agregar campo empresa a Cliente
        migrations.AddField(
            model_name='cliente',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hotel.empresa', verbose_name='Empresa Asociada'),
        ),
        
        # Renombrar modelo Reserva a Hospedada
        migrations.RenameModel(
            old_name='Reserva',
            new_name='Hospedada',
        ),
        
        # Renombrar campo numero_reserva a numero_hospedada
        migrations.RenameField(
            model_name='hospedada',
            old_name='numero_reserva',
            new_name='numero_hospedada',
        ),
        
        # Agregar campo tipo_hospedada
        migrations.AddField(
            model_name='hospedada',
            name='tipo_hospedada',
            field=models.CharField(choices=[('continua', 'Hospedada Continua'), ('por_rato', 'Hospedada Por Rato')], default='continua', max_length=20, verbose_name='Tipo de Hospedada'),
        ),
        
        # Agregar campo empresa a Hospedada
        migrations.AddField(
            model_name='hospedada',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hotel.empresa', verbose_name='Empresa'),
        ),
        
        # Renombrar campo reserva a hospedada en ConsumoHabitacion
        migrations.RenameField(
            model_name='consumohabitacion',
            old_name='reserva',
            new_name='hospedada',
        ),
        
        # Renombrar campo reserva a hospedada en Pago
        migrations.RenameField(
            model_name='pago',
            old_name='reserva',
            new_name='hospedada',
        ),
        
        # Agregar campo pagado_por a Pago
        migrations.AddField(
            model_name='pago',
            name='pagado_por',
            field=models.CharField(choices=[('cliente', 'Cliente'), ('empresa', 'Empresa')], default='cliente', max_length=20, verbose_name='Pagado Por'),
        ),
        
        # Renombrar campo reserva a hospedada en AjustePrecio
        migrations.RenameField(
            model_name='ajusteprecio',
            old_name='reserva',
            new_name='hospedada',
        ),
        
        # Renombrar campo reserva a hospedada en Factura
        migrations.RenameField(
            model_name='factura',
            old_name='reserva',
            new_name='hospedada',
        ),
        
        # Actualizar opciones del modelo
        migrations.AlterModelOptions(
            name='hospedada',
            options={'ordering': ['-fecha_creacion'], 'verbose_name': 'Hospedada', 'verbose_name_plural': 'Hospedadas'},
        ),
    ]