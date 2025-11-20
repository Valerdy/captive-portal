@echo off
REM Script pour créer un superuser admin rapidement

echo.
echo ========================================
echo   Creation d'un superuser admin
echo ========================================
echo.

cd backend
call venv\Scripts\activate.bat

echo Creation d'un superuser avec les credentials par defaut:
echo   Username: admin
echo   Email: admin@example.com
echo   Password: admin123
echo.

python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123') and print('Superuser cree avec succes!') or print('Superuser admin existe deja')"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Superuser cree avec succes!
    echo.
    echo Credentials:
    echo   Username: admin
    echo   Password: admin123
    echo.
    echo Connectez-vous sur: http://localhost:8000/admin
    echo ========================================
) else (
    echo.
    echo ERREUR lors de la creation du superuser
    echo Essayez manuellement:
    echo   python manage.py createsuperuser
)

echo.
pause
