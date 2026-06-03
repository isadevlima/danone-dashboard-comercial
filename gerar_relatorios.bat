@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m scripts.gerar_relatorios_laboratorios %*
pause
