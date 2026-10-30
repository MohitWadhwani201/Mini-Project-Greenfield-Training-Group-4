Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "Starting Enterprise HR Analytics & Data Warehouse Platform (Phases 4 & 5)..." -ForegroundColor Green
Write-Host "Theme: Executive Cyber Dark Mode (Sky Blue / Slate / Emerald Palette)" -ForegroundColor DarkCyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Set-Location $PSScriptRoot

if (Test-Path ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" -m streamlit run app.py
} elseif (Test-Path "C:\Users\PrakharMishra\AppData\Local\Python\bin\python.exe") {
    & "C:\Users\PrakharMishra\AppData\Local\Python\bin\python.exe" -m streamlit run app.py
} else {
    python -m streamlit run app.py
}
