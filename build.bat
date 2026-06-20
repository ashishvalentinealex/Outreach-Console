@echo off
setlocal enabledelayedexpansion

echo =^> Creating a clean virtual environment...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create virtual environment. Is Python installed?
    pause & exit /b 1
)

echo =^> Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment.
    pause & exit /b 1
)

echo =^> Removing obsolete pathlib package if present...
pip uninstall pathlib -y 2>nul

echo =^> Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: pip install failed.
    pause & exit /b 1
)

echo =^> Closing any running OutreachConsole instance...
taskkill /f /im OutreachConsole.exe 2>nul
timeout /t 2 /nobreak >nul

echo =^> Building Windows executable...
pyinstaller OutreachConsole.spec --clean
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: PyInstaller failed. Check the output above for details.
    pause & exit /b 1
)

echo.
echo   Build complete: dist\OutreachConsole.exe
echo   You can now distribute that single file.
pause
