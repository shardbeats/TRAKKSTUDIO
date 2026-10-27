@echo off
REM TRAKKSTUDIO one-click setup + launch (Windows)
setlocal
if not exist .venv (
  echo [trakkstudio] creating venv...
  python -m venv .venv
)
call .venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py %*
