@echo off
cd /d "%~dp0frontend"
echo.
echo ========================================
echo       STOCKFLOW FRONTEND
 echo ========================================
echo.
call npm install
call npm run dev
pause
