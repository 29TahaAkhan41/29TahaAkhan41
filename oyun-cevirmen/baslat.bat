@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv (
    echo Ilk kurulum yapiliyor, lutfen bekleyin...
    py -3 -m venv .venv || python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)
start "" pythonw -m oyun_cevirmen
