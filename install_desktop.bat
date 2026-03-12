@echo off
TITLE MDTransformer - Install ^& Desktop Shortcut
echo ==============================================
echo  MDTransformer - Desktop Setup
echo ==============================================
echo.
echo 1/3 Checking Python environment...
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment ^(venv^) to keep the app isolated...
    python -m venv venv
)

echo.
echo 2/3 Installing Production Dependencies...
echo This might take a few minutes as it downloads UI and Document reading engines...
echo.
call venv\Scripts\pip install -r requirements.txt

echo.
echo 3/3 Creating Desktop Shortcut...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\MDTransformer.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut^(sLinkFile^) >> CreateShortcut.vbs
echo oLink.TargetPath = "%~dp0venv\Scripts\pythonw.exe" >> CreateShortcut.vbs
echo oLink.Arguments = """%~dp0main.py""" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%~dp0" >> CreateShortcut.vbs
echo oLink.IconLocation = "%~dp0assets\icon.ico" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo.
echo ==============================================
echo   DONE! MDTransformer is ready.
echo   You can run it from the Desktop icon or use run.bat.
echo ==============================================
echo Launching application...
start "" "venv\Scripts\pythonw.exe" "main.py"
pause
