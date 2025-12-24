@echo off
REM Script de demarrage du backend avec PostgreSQL (Windows)

echo.
echo ========================================
echo   Demarrage Backend avec PostgreSQL
echo ========================================
echo.

cd backend

echo [1/4] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERREUR: Impossible d'activer l'environnement virtuel
    pause
    exit /b 1
)

echo.
echo [2/4] Verification de la configuration PostgreSQL...

REM Verifier que le .env contient PostgreSQL
findstr /C:"DB_ENGINE=django.db.backends.postgresql" .env >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERREUR: PostgreSQL n'est pas configure dans .env
    echo.
    echo Executez d'abord: setup_postgresql.bat
    echo.
    pause
    exit /b 1
)

echo Configuration PostgreSQL detectee dans .env

echo.
echo [3/4] Test de la connexion PostgreSQL...
python test_postgresql_connection.py
if %errorlevel% neq 0 (
    echo.
    echo ERREUR: La connexion PostgreSQL a echoue!
    echo.
    echo Verifications:
    echo   1. PostgreSQL est-il demarre?
    echo   2. La base 'captive_portal_db' existe-t-elle?
    echo   3. Le mot de passe dans .env est-il correct?
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Demarrage du serveur Django...
echo.
echo ========================================
echo   Backend PostgreSQL pret!
echo   http://localhost:8000
echo   Admin: http://localhost:8000/admin
echo ========================================
echo.
echo Pour arreter le serveur: Ctrl+C
echo.
echo Dans un autre terminal, demarrez le frontend:
echo   cd frontend\portail-captif
echo   npm run dev
echo.

python manage.py runserver 0.0.0.0:8000
