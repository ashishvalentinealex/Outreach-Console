@echo off
echo =^> Installing dependencies...
pip install -r requirements.txt

echo =^> Building Windows executable...
pyinstaller OutreachConsole.spec --clean

echo.
echo   Build complete: dist\OutreachConsole.exe
echo   Run it with:   dist\OutreachConsole.exe
pause
