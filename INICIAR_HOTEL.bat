@echo off
echo ================================================
echo    🏨 SISTEMA DE GESTION HOTELERA 🏨
echo ================================================
echo.
echo Activando entorno virtual...
call hotel_env\Scripts\activate.bat
echo.
echo Verificando migraciones...
python manage.py migrate
echo.
echo ✅ Sistema listo para usar!
echo.
echo 🌐 Acceso al sistema:
echo    - Aplicacion principal: http://127.0.0.1:8000/
echo    - Panel de administracion: http://127.0.0.1:8000/admin/
echo.
echo 🔐 Credenciales de administrador:
echo    - Usuario: admin
echo    - Contraseña: admin123
echo.
echo ================================================
echo          Iniciando servidor Django...
echo ================================================
echo.
python manage.py runserver
pause