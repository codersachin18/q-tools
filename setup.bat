@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Q-Tools Setup

echo.
echo  ==================================================
echo    Q-Tools  -  first time setup
echo  ==================================================
echo.

rem --------------------------------------------------
rem 1/4  Find Python
rem --------------------------------------------------
set "PY="
where python >nul 2>nul
if not errorlevel 1 set "PY=python"
if not defined PY (
    where py >nul 2>nul
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY goto :no_python

echo [1/4] Python found:
%PY% --version
echo.

rem --------------------------------------------------
rem 2/4  Create the virtual environment
rem --------------------------------------------------
set "VENV=%~dp0.venv"
if exist "%VENV%\Scripts\pythonw.exe" goto :venv_ok
echo [2/4] Creating virtual environment (one time, please wait)...
%PY% -m venv "%VENV%"
if errorlevel 1 goto :venv_failed
:venv_ok
echo        OK
echo.

set "VPY=%VENV%\Scripts\python.exe"

rem --------------------------------------------------
rem 3/4  Install requirements
rem --------------------------------------------------
echo [3/4] Installing required packages...
"%VPY%" -m pip install --upgrade pip --disable-pip-version-check -q
if errorlevel 1 echo        (pip upgrade skipped)
"%VPY%" -m pip install -r "%~dp0requirements.txt" --disable-pip-version-check -q
if errorlevel 1 goto :pip_failed
echo        OK
echo.

rem --------------------------------------------------
rem 4/4  Icon + desktop shortcut
rem --------------------------------------------------
if exist "%~dp0assets\make_icon.py" (
    echo [4/4] Generating icon and creating shortcuts...
    "%VPY%" "%~dp0assets\make_icon.py" >nul 2>nul
) else (
    echo [4/4] Creating shortcuts...
)

set "PYW=%VENV%\Scripts\pythonw.exe"
if not exist "%PYW%" set "PYW=pythonw.exe"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$proj='%~dp0'.TrimEnd('\'); $pyw='%PYW%'; $ico=Join-Path $proj 'assets\qtools.ico'; if(Test-Path $ico){$icon=$ico+',0'}else{$icon=$pyw+',0'}; $w=New-Object -ComObject WScript.Shell; $targets=@([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('Programs')); foreach($d in $targets){ if($d -and (Test-Path $d)){ $s=$w.CreateShortcut((Join-Path $d 'Q-Tools.lnk')); $s.TargetPath=$pyw; $s.Arguments='\"'+(Join-Path $proj 'app.py')+'\"'; $s.WorkingDirectory=$proj; $s.IconLocation=$icon; $s.Description='Q-Tools - everyday utilities'; $s.WindowStyle=1; $s.Save() } }; Write-Host '        shortcut created'"
if errorlevel 1 goto :shortcut_failed

echo.
echo  ==================================================
echo    Setup complete!
echo.
echo    * Double click the "Q-Tools" icon on your Desktop
echo    * Or run start.bat from this folder
echo  ==================================================
echo.
pause
exit /b 0

rem --------------------------------------------------
rem Errors
rem --------------------------------------------------
:no_python
echo [ERROR] Python was not found on this computer.
echo.
echo         1. Open https://www.python.org/downloads/
echo         2. Download and run the installer
echo         3. IMPORTANT: tick "Add python.exe to PATH"
echo         4. Run setup.bat again
echo.
pause
exit /b 1

:venv_failed
echo [ERROR] Could not create the virtual environment.
echo         Re-run setup.bat, or install Python with the
echo         "py launcher" component enabled.
echo.
pause
exit /b 1

:pip_failed
echo [ERROR] Installing packages failed.
echo         Check your internet connection and run setup.bat again.
echo.
pause
exit /b 1

:shortcut_failed
echo [ERROR] The shortcut could not be created.
echo         You can still start the app with start.bat.
echo.
pause
exit /b 1
