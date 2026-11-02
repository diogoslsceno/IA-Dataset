@echo off
chcp 65001 >nul
echo ==================================================================
echo     INICIALIZANDO PLATAFORMA WORDGEN · IA - DATASET              
echo ==================================================================

rem 1. Localiza diretorio base
set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%..\dashboard\server_com_chat.py" (
    set "BASE_DIR=%SCRIPT_DIR%..\"
) else if exist "%SCRIPT_DIR%dashboard\server_com_chat.py" (
    set "BASE_DIR=%SCRIPT_DIR%"
) else if exist "%SCRIPT_DIR%IA - Dataset\dashboard\server_com_chat.py" (
    set "BASE_DIR=%SCRIPT_DIR%IA - Dataset\"
) else (
    set "BASE_DIR=%SCRIPT_DIR%"
)

rem 2. Verifica Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado no sistema. Por favor instale o Python 3.9+ e adicione ao PATH.
    pause
    exit /b 1
)

echo [1/2] Python detectado com sucesso.
echo [2/2] Iniciando Servidor HTTP e Chatbot na porta 8765...
echo ------------------------------------------------------------------
echo Acesse no navegador: http://localhost:8765/dist/
echo Pressione CTRL+C para encerrar o servidor.
echo ------------------------------------------------------------------

start http://localhost:8765/dist/
python "%BASE_DIR%dashboard\server_com_chat.py"
pause
