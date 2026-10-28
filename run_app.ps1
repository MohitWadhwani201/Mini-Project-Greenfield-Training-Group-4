Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "Starting Enterprise HR Analytics & Data Warehouse Platform (Phases 4 & 5)..." -ForegroundColor Green
Write-Host "Theme: Executive Cyber Dark Mode (Sky Blue / Slate / Emerald Palette)" -ForegroundColor DarkCyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Set-Location $PSScriptRoot
& "C:\Users\PrakharMishra\AppData\Local\Python\bin\python.exe" -m streamlit run app.py

