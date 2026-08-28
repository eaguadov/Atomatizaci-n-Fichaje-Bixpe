@echo off
chcp 65001 >nul
echo ======================================================
echo   SINCRONIZADOR DE VACACIONES (EXCEL -^> GITHUB)
echo ======================================================
echo.
cd /d "%~dp0"
python scripts\actualizar_vacaciones.py
echo.
echo ======================================================
pause
