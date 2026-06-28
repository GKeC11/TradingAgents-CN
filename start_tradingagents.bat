@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"
set "PYTHON_EXE=%PROJECT_ROOT%\.venv-run\Scripts\python.exe"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python venv not found: %PYTHON_EXE%
  echo Please install backend dependencies first.
  pause
  exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
  echo [ERROR] Frontend dependencies not found: %FRONTEND_DIR%\node_modules
  echo Please run "npm install" in the frontend directory first.
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm was not found in PATH.
  echo Please install Node.js 18+ or add npm to PATH.
  pause
  exit /b 1
)

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "DEBUG=false"
set "DOCKER_CONTAINER=false"
set "TRADINGAGENTS_LOG_DIR=logs"
set "MONGODB_HOST=localhost"
set "MONGODB_PORT=27017"
set "MONGODB_USERNAME=admin"
set "MONGODB_PASSWORD=tradingagents123"
set "MONGODB_AUTH_SOURCE=admin"
set "MONGODB_DATABASE=tradingagentscn"
set "REDIS_HOST=localhost"
set "REDIS_PORT=6379"
set "REDIS_PASSWORD=tradingagents123"
set "VITE_API_BASE_URL=http://localhost:8000"

echo Starting TradingAgents-CN backend and frontend...
echo Backend:  http://localhost:8000/api/health
echo Frontend: http://localhost:3000/
echo.
echo Make sure MongoDB and Redis are already running on localhost.
echo.

start "TradingAgents Backend" /D "%PROJECT_ROOT%" cmd /k ""%PYTHON_EXE%" -m app"

timeout /t 3 /nobreak >nul

start "TradingAgents Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev -- --host 0.0.0.0 --port 3000"

timeout /t 6 /nobreak >nul
start "" "http://localhost:3000/"

echo Started. Keep the backend and frontend windows open while using the app.
pause
