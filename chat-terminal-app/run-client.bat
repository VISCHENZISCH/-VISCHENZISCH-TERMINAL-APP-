@echo off
setlocal ENABLEEXTENSIONS

rem Change to this script's directory (project root)
cd /d "%~dp0"

rem Activate local venv if present
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

rem Choose Python interpreter
set "PYTHON="
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if not defined PYTHON where python >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON where py >nul 2>&1 && set "PYTHON=py -3"
if not defined PYTHON (
  echo [error] Python introuvable. Installez Python 3.10+ ou activez votre environnement.
  echo.
  if "%NO_PAUSE%"=="" (
    echo Appuyez sur une touche pour fermer cette fenetre...
    pause >nul
  )
  exit /b 1
)

rem Defaults (override by setting env vars HTTP_URL / WS_URL or via CLI args)
set "HTTP_DEFAULT=http://127.0.0.1:8000"
set "WS_DEFAULT=ws://127.0.0.1:8000/ws"

if "%HTTP_URL%"=="" set "HTTP_URL=%HTTP_DEFAULT%"
if "%WS_URL%"=="" set "WS_URL=%WS_DEFAULT%"

%PYTHON% -m client.main --http "%HTTP_URL%" --ws "%WS_URL%" %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo [client] Termine avec le code %RC%
echo.
if "%NO_PAUSE%"=="" (
  echo Appuyez sur une touche pour fermer cette fenetre...
  pause >nul
)
exit /b %RC%


