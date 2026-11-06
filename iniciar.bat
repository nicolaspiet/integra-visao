@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Ambiente nao encontrado. Primeiro execute a instalacao do README.
  pause
  exit /b 1
)
.venv\Scripts\python.exe main.py %*
