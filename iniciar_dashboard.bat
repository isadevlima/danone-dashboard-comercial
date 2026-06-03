@echo off
chcp 65001 >nul
title Dashboard Danone NTR
cd /d "%~dp0"

echo.
echo  ========================================
echo   Dashboard Comercial - Danone NTR
echo  ========================================
echo.

if not exist "dados\ESTUDO_DANONE_MAT_MAIO1.xlsx" (
    if not exist "dados\ESTUDO_DANONE_MAT_MAIO.xlsx" (
        echo  [ERRO] Planilha nao encontrada em dados\
        echo  Coloque ESTUDO_DANONE_MAT_MAIO1.xlsx na pasta dados\
        pause
        exit /b 1
    )
)

where python >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado.
    echo  Instale em https://www.python.org/downloads/
    echo  Marque "Add Python to PATH" na instalacao.
    pause
    exit /b 1
)

echo  Verificando dependencias...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo  [ERRO] Falha ao instalar bibliotecas.
    pause
    exit /b 1
)

echo.
echo  Abrindo dashboard no navegador...
echo  URL: http://localhost:8501
echo  Para encerrar: feche esta janela ou pressione Ctrl+C
echo.

start "" http://localhost:8501
python -m streamlit run streamlit_app.py --server.headless true

pause
