@echo off
title Enterprise HR Analytics & Warehouse App
echo ==============================================================================
echo Starting Enterprise HR Analytics & Data Warehouse Platform (Phases 4 & 5)...
echo Theme: Executive Cyber Dark Mode
echo ==============================================================================
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run app.py
) else if exist "C:\Users\PrakharMishra\AppData\Local\Python\bin\python.exe" (
    "C:\Users\PrakharMishra\AppData\Local\Python\bin\python.exe" -m streamlit run app.py
) else (
    python -m streamlit run app.py
)
pause
