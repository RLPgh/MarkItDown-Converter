@echo off
TITLE MDTransformer - EXE Builder
echo ==============================================
echo  MDTransformer - Build Standalone EXE
echo ==============================================
echo.
echo Make sure Python is installed on your system.
echo Warning: Building the standalone EXE may take a few minutes.
echo.

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Installing dependencies (Prod + Dev/PyInstaller)...
call venv\Scripts\pip install -r requirements-dev.txt

echo.
echo Building single-file executable via PyInstaller...
echo Removing old build artifacts...
if exist "build" rm -r build
if exist "dist\MDTransformer.exe" rm dist\MDTransformer.exe
if exist "MDTransformer.spec" rm MDTransformer.spec

call venv\Scripts\pyinstaller --name "MDTransformer" --onefile --windowed --icon "assets\icon.ico" --add-data "assets;assets" main.py

echo.
echo ==============================================
echo   BUILD COMPLETE!
echo   Your portable EXE is located in the `dist` folder.
echo ==============================================
pause
