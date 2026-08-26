@echo off
cd /d "%~dp0"
title Hello, Dolly
echo.
echo  Starting Dolly widgets...
echo.

py -3 -c "from PIL import Image" 2>nul
if errorlevel 1 (
  echo  Pillow is not installed on this Python. Installing now...
  py -3 -m pip install pillow
  if errorlevel 1 (
    echo.
    echo  Could not install Pillow. Try:
    echo    py -3 -m pip install pillow
    echo.
    pause
    exit /b 1
  )
)

py -3 desktop_widgets.py
if errorlevel 1 (
  echo.
  echo  Dolly did not start. Leave this window open and send a screenshot of the text above.
  pause
)
