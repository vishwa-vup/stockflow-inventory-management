@echo off
cd /d "%~dp0backend"
echo.
echo ========================================
echo       STOCKFLOW BACKEND
 echo ========================================
echo.
python -m uvicorn app.main:app --reload --port 8000
pause
