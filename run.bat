@echo off
setlocal
cd /d "%~dp0"

rem Virtual environment location. Set VENV_DIR before running to use a different one.
if not defined VENV_DIR set "VENV_DIR=%~dp0.venv"
set "VPY=%VENV_DIR%\Scripts\python.exe"
set "MARKER=%VENV_DIR%\requirements.installed"

if exist "%VPY%" goto :check_venv

call :find_python
if not defined PY (
    call :install_python || goto :fail
    call :find_python
)
if not defined PY (
    echo Python was installed but could not be located. Open a new window and run this script again.
    goto :fail
)
echo Creating virtual environment in "%VENV_DIR%" ...
%PY% -m venv "%VENV_DIR%" || goto :fail

:check_venv
"%VPY%" -c "import sys" >nul 2>&1 || (
    echo The virtual environment in "%VENV_DIR%" is broken. Delete that folder and run this script again.
    goto :fail
)

rem Reinstall only when requirements.txt changed since the last successful install.
fc /b requirements.txt "%MARKER%" >nul 2>&1 && goto :run
echo Installing requirements ...
"%VPY%" -m pip install -r requirements.txt || goto :fail
call :has_browser
if errorlevel 1 (
    echo Neither Chrome nor Edge found, downloading Playwright's Chromium ...
    "%VPY%" -m playwright install chromium || goto :fail
)
copy /y requirements.txt "%MARKER%" >nul

:run
echo.
echo Starting the web UI at http://127.0.0.1:5000 - close this window or press Ctrl+C to stop.
start "" /b powershell -NoProfile -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5000'"
"%VPY%" app.py
if errorlevel 1 pause
exit /b

:find_python
set "PY="
where py >nul 2>&1 && call :try_python py -3
for /f "delims=" %%P in ('where python 2^>nul') do call :try_python "%%P"
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*" "%ProgramFiles%\Python3*" "%ProgramFiles(x86)%\Python3*" "%SystemDrive%\Python3*") do call :try_python "%%D\python.exe"
exit /b 0

:try_python
rem Accept the first interpreter that actually runs and is 3.9+ (skips the Microsoft Store stub).
if defined PY exit /b 0
%* -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1 && set PY=%*
exit /b 0

:has_browser
for %%B in (
    "%ProgramFiles%\Google\Chrome\Application\chrome.exe"
    "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
    "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
    "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
    "%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"
) do if exist %%B exit /b 0
exit /b 1

:install_python
echo Python 3.9 or newer was not found.
where winget >nul 2>&1 || (
    echo Install it from https://www.python.org/downloads/ and run this script again.
    exit /b 1
)
choice /c YN /m "Install Python 3.12 for your user account with winget"
if errorlevel 2 exit /b 1
winget install --exact --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
exit /b %errorlevel%

:fail
echo.
echo Setup failed. See the messages above.
pause
exit /b 1
