@echo off
REM Script pour corriger les permissions admin d'un utilisateur

echo.
echo ========================================
echo   Correction Permissions Admin
echo ========================================
echo.

cd backend
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERREUR: Impossible d'activer l'environnement virtuel
    pause
    exit /b 1
)

python fix_admin_user.py valerdy

pause
