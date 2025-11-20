@echo off
REM Script de configuration PostgreSQL pour le backend Django (Windows)

echo.
echo ========================================
echo   Configuration PostgreSQL
echo ========================================
echo.

cd backend

echo [1/6] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERREUR: Impossible d'activer l'environnement virtuel
    echo Assurez-vous que le venv existe: python -m venv venv
    pause
    exit /b 1
)

echo.
echo [2/6] Verification de psycopg2...
python -c "import psycopg2" 2>nul
if %errorlevel% neq 0 (
    echo psycopg2 n'est pas installe, installation en cours...
    pip install psycopg2-binary
    if %errorlevel% neq 0 (
        echo ERREUR: Impossible d'installer psycopg2-binary
        pause
        exit /b 1
    )
) else (
    echo psycopg2 est deja installe
)

echo.
echo [3/6] Configuration de PostgreSQL dans .env...

REM Sauvegarder l'ancien .env si existe
if exist .env (
    echo Sauvegarde de l'ancien .env...
    copy .env .env.backup.%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2% >nul 2>&1
)

REM Demander le mot de passe PostgreSQL
set /p PGPASSWORD="Entrez le mot de passe PostgreSQL (utilisateur postgres): "
if "%PGPASSWORD%"=="" (
    echo ERREUR: Le mot de passe ne peut pas etre vide
    pause
    exit /b 1
)

REM Créer le fichier .env avec PostgreSQL
(
echo # Django Configuration
echo SECRET_KEY=django-insecure-dev-key-change-in-production-!uwv@971di86^)lw6c!=85n+uclltw$g2*y0_17$%%y#1ln0@mzc
echo DEBUG=True
echo ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
echo.
echo # Database Configuration - PostgreSQL
echo DB_ENGINE=django.db.backends.postgresql
echo DB_NAME=captive_portal_db
echo DB_USER=postgres
echo DB_PASSWORD=%PGPASSWORD%
echo DB_HOST=localhost
echo DB_PORT=5432
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

echo Configuration PostgreSQL appliquee!

echo.
echo [4/6] Test de la connexion PostgreSQL...
python test_postgresql_connection.py
if %errorlevel% neq 0 (
    echo.
    echo ERREUR: La connexion PostgreSQL a echoue!
    echo.
    echo Verifications a effectuer:
    echo   1. PostgreSQL est-il demarre? ^(services.msc -^> postgresql^)
    echo   2. La base de donnees 'captive_portal_db' existe-t-elle?
    echo   3. Le mot de passe est-il correct?
    echo.
    echo Pour creer la base de donnees:
    echo   - Ouvrez pgAdmin
    echo   - Clic droit sur Databases -^> Create -^> Database
    echo   - Name: captive_portal_db
    echo   - Owner: postgres
    echo   - Save
    echo.
    pause
    exit /b 1
)

echo.
echo [5/6] Application des migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo.
    echo ERREUR: Les migrations ont echoue!
    echo Verifiez les erreurs ci-dessus.
    pause
    exit /b 1
)

echo.
echo [6/6] Verification du superuser...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser existe' if User.objects.filter(is_superuser=True).exists() else 'Aucun superuser')" 2>nul

echo.
echo ========================================
echo   Configuration PostgreSQL terminee!
echo ========================================
echo.
echo Base de donnees: captive_portal_db
echo Utilisateur: postgres
echo Host: localhost:5432
echo.
echo Prochaines etapes:
echo   1. Creer un superuser: python manage.py createsuperuser
echo      Ou utilisez: create_admin.bat
echo.
echo   2. Demarrer le backend: python manage.py runserver
echo      Ou utilisez: start_with_postgresql.bat
echo.
echo   3. Demarrer le frontend dans un autre terminal:
echo      cd frontend\portail-captif
echo      npm run dev
echo.
pause
