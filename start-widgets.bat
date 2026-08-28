@echo off
cd /d "%~dp0"
title Hello, Dolly
echo.
echo  Starting Dolly widgets...
echo.

where py >nul 2>&1
if %errorlevel%==0 (
  py -3 -c "from PIL import Image" 2>nul
  if errorlevel 1 (
    echo  Installing Pillow...
    py -3 -m pip install pillow
  )
  py -3 desktop_widgets.py
  if errorlevel 1 goto :fail
  goto :eof
)

where python >nul 2>&1
if %errorlevel%==0 (
  python -c "from PIL import Image" 2>nul
  if errorlevel 1 (
    echo  Installing Pillow...
    python -m pip install pillow
  )
  python desktop_widgets.py
  if errorlevel 1 goto :fail
  goto :eof
)

echo  Python was not found. Install Python 3 from python.org and check "Add python.exe to PATH".
pause
exit /b 1

:fail
echo.
echo  Dolly did not start. Leave this window open and send a screenshot of the text above.
pause
