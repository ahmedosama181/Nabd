@echo off
setlocal
cd /d "%~dp0"
title Nabd - EGP market pulse

rem 1) our private portable Python, 2) an installed Python 3.8+, 3) download a portable one (no admin needed)
set "PY="
if exist "runtime\python-win\python.exe" set "PY=runtime\python-win\python.exe"
if not defined PY ( py -3 -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>nul && set "PY=py -3" )
if not defined PY ( python -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>nul && set "PY=python" )
if not defined PY (
  echo Python was not found. Setting up a private copy for Nabd - this happens only once.
  powershell -NoProfile -ExecutionPolicy Bypass -File "tools\bootstrap-windows.ps1"
  if exist "runtime\python-win\python.exe" set "PY=runtime\python-win\python.exe"
)
if not defined PY (
  echo.
  echo Could not set up Python automatically. Check your internet connection and run this file again,
  echo or install Python from https://www.python.org/downloads/ and run this file again.
  pause
  exit /b 1
)
%PY% app.py
pause
