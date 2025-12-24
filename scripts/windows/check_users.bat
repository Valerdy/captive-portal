@echo off
REM Script pour vérifier les utilisateurs et leurs permissions

echo.
echo ========================================
echo   Diagnostic des Utilisateurs
echo ========================================
echo.

cd backend
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERREUR: Impossible d'activer l'environnement virtuel
    pause
    exit /b 1
)

python check_users.py

pause
