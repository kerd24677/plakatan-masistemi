@echo off
if not exist .venv (
    echo Sanal ortam bulunamadi. Once kurulum yapin:
    echo   py -3.11 -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    exit /b 1
)
call .venv\Scripts\activate.bat
python main.py
