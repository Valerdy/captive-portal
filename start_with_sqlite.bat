@echo off
REM Script de démarrage rapide avec SQLite (Windows)
REM Ce script configure automatiquement SQLite et démarre le backend

echo.
echo ========================================
echo   Configuration SQLite pour le backend
echo ========================================
echo.

cd backend

echo [1/5] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo.
echo [2/5] Configuration de SQLite dans .env...

REM Créer une sauvegarde du .env
copy .env .env.backup >nul 2>&1

REM Créer un nouveau .env avec SQLite
(
echo # Django Configuration
echo SECRET_KEY=django-insecure-dev-key-change-in-production-!uwv@971di86^)lw6c!=85n+uclltw$g2*y0_17$%%y#1ln0@mzc
echo DEBUG=True
echo ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
echo.
echo # Database Configuration - SQLite pour developpement local
echo DB_ENGINE=django.db.backends.sqlite3
echo DB_NAME=db.sqlite3
echo.
echo # CORS Configuration
echo CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000
echo.
echo # JWT Token Lifetimes ^(in minutes^)
echo JWT_ACCESS_TOKEN_LIFETIME=60
echo JWT_REFRESH_TOKEN_LIFETIME=1440
echo.
echo # Mikrotik Router Configuration
echo MIKROTIK_HOST=192.168.88.1
echo MIKROTIK_PORT=8728
echo MIKROTIK_USERNAME=admin
echo MIKROTIK_PASSWORD=
echo MIKROTIK_USE_SSL=False
echo.
echo # Mikrotik Agent Configuration
echo MIKROTIK_AGENT_URL=http://localhost:3001
echo MIKROTIK_AGENT_TIMEOUT=10
echo.
echo # RADIUS Configuration
echo RADIUS_SERVER=127.0.0.1
echo RADIUS_SECRET=testing123
echo RADIUS_AUTH_PORT=1812
echo RADIUS_ACCT_PORT=1813
echo.
echo # Captive Portal Configuration
echo PORTAL_REDIRECT_URL=http://example.com
echo SESSION_TIMEOUT=3600
) > .env

echo Configuration SQLite appliquee!
echo Sauvegarde de l'ancien .env: .env.backup
echo.

echo [3/5] Application des migrations...
python manage.py migrate

if %errorlevel% neq 0 (
    echo.
    echo ERREUR: Les migrations ont echoue!
    echo Verifiez les erreurs ci-dessus.
    pause
    exit /b 1
)

echo.
echo [4/5] Verification du superuser...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser existe' if User.objects.filter(is_superuser=True).exists() else 'Aucun superuser')"

echo.
echo [5/5] Demarrage du serveur Django...
echo.
echo ========================================
echo   Backend demarre sur http://localhost:8000
echo   Admin: http://localhost:8000/admin
echo ========================================
echo.
echo Pour creer un superuser, arretez ce script (Ctrl+C)
echo et executez: python manage.py createsuperuser
echo.
echo Demarrez le frontend dans un autre terminal:
echo   cd frontend\portail-captif
echo   npm run dev
echo.

python manage.py runserver 0.0.0.0:8000
