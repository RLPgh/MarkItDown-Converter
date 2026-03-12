@echo off
TITLE MDTransformer - Runner
echo ==============================================
echo  MDTransformer
echo ==============================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [!] No environment found. Running initial setup first...
    call install_desktop.bat
    exit /b
)

echo Starting application...
start "" "venv\Scripts\pythonw.exe" "main.py"

