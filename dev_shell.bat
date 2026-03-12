@echo off
TITLE MDTransformer - Dev Shell
echo ==============================================
echo  MDTransformer - Developer Shell Environment
echo ==============================================
echo.
echo Bypassing PowerShell Execution Policy for this session...
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (!(Test-Path 'venv\Scripts\Activate.ps1')) { echo 'Creating venv...'; python -m venv venv; .\venv\Scripts\pip install -r requirements-dev.txt }; & '.\venv\Scripts\Activate.ps1'; if($?) { Write-Host 'Environment Activated!' -ForegroundColor Green } else { Write-Host 'Failed to activate environment.' -ForegroundColor Red }; $host.UI.RawUI.WindowTitle = 'MDTransformer Dev Shell'; Start-Sleep -s 1; cmd /c cd ."
cmd /k "venv\Scripts\activate.bat"
