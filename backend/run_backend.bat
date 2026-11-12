@echo off
title Voltix TechStore Backend
cd /d "%~dp0"
echo ===================================================
echo Starting Voltix TechStore FastAPI Backend...
echo ===================================================
call .venv\Scripts\activate.bat
python main.py
pause
