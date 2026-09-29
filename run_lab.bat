@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "VENV_DIR=.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "SETUP_MARKER=%VENV_DIR%\.issuer_lab_requirements.sha256"

echo.
echo Issuer Protocol Lab
echo ===================

if not exist "requirements.txt" (
    echo [ERRO] requirements.txt nao foi encontrado em:
    echo        %CD%
    goto :fail
)

if not exist "issuer_lab\frontend_app.py" (
    echo [ERRO] issuer_lab\frontend_app.py nao foi encontrado.
    goto :fail
)

if not exist "%VENV_PYTHON%" (
    echo [1/3] Criando o ambiente virtual...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv "%VENV_DIR%"
    ) else (
        where python >nul 2>nul
        if errorlevel 1 (
            echo [ERRO] Python nao foi encontrado no PATH.
            echo Instale Python 3.11 ou superior e marque a opcao Add Python to PATH.
            goto :fail
        )
        python -m venv "%VENV_DIR%"
    )
    if errorlevel 1 goto :fail
)

call "%VENV_ACTIVATE%"
if errorlevel 1 goto :fail

set "CURRENT_HASH="
for /f "usebackq delims=" %%H in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-FileHash -LiteralPath 'requirements.txt' -Algorithm SHA256).Hash"`) do set "CURRENT_HASH=%%H"

if not defined CURRENT_HASH (
    echo [ERRO] Nao foi possivel calcular o hash de requirements.txt.
    goto :fail
)

set "INSTALLED_HASH="
if exist "%SETUP_MARKER%" set /p INSTALLED_HASH=<"%SETUP_MARKER%"

if /I not "%CURRENT_HASH%"=="%INSTALLED_HASH%" (
    echo [2/3] Instalando ou atualizando dependencias...
    python -m pip install --upgrade pip
    if errorlevel 1 goto :fail
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :fail
    >"%SETUP_MARKER%" echo %CURRENT_HASH%
) else (
    echo [2/3] Ambiente pronto. Instalacao ignorada.
)

echo [3/3] Abrindo o Streamlit...
echo.
python -m streamlit run issuer_lab\frontend_app.py
if errorlevel 1 goto :fail

endlocal
exit /b 0

:fail
echo.
echo O Lab nao foi iniciado. Revise a mensagem acima.
pause
endlocal
exit /b 1
