@echo off
echo === Internship Scraper Launcher ===

:: Initialize default python command
set "PYTHON_EXE=python"

:: Check if python is available in PATH
python --version >nul 2>&1
if %errorlevel% equ 0 goto :has_python

:: Check if python is installed in local user app data folder
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
    goto :has_python
)

:: If Python is not found, offer automatic installation
echo Python is not detected on your system.
set /p "choice=Would you like to automatically download and install Python 3.11? [Y/N] (Default: Y): "
if /i "%choice%"=="n" (
    echo.
    echo Please install Python manually from: https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo.
echo Downloading Python 3.11 installer (please wait)...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe' -OutFile '%temp%\python-installer.exe'"

if not exist "%temp%\python-installer.exe" (
    echo Error: Failed to download Python installer. Please check your internet connection.
    pause
    exit /b 1
)

echo.
echo Installing Python... 
echo A setup progress window will appear. Please wait for it to complete.
"%temp%\python-installer.exe" /passive InstallAllUsers=0 PrependPath=1 Include_test=0

:: Clean up installer
del "%temp%\python-installer.exe"

:: Verify installation path again
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
    echo.
    echo Python installed successfully.
    goto :has_python
)

:: Try standard command check in case PATH updated
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    echo.
    echo Python installed successfully.
    goto :has_python
)

echo.
echo Error: Failed to install or verify Python installation. 
echo Please download and install Python manually from: https://www.python.org/
pause
exit /b 1

:has_python
echo Using Python: %PYTHON_EXE%

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo.
    echo Creating Python virtual environment (.venv)...
    "%PYTHON_EXE%" -m venv .venv
)

:: Activate virtual environment
echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

:: Upgrade pip and install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Run app as Desktop App (with Web browser fallback)
echo.
echo Launching Scraper Console...
python desktop.py
if %errorlevel% neq 0 (
    echo.
    echo Desktop window engine not supported on this PC.
    echo Launching in web browser fallback mode...
    start http://127.0.0.1:5000/
    python app.py
)
pause
