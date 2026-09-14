# Mở 2 cửa sổ chạy backend + frontend (Windows PowerShell)
$root = Split-Path -Parent $PSScriptRoot
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\backend'; uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\frontend'; npm run dev"
Write-Host "Backend: http://localhost:8000/docs | Frontend: http://localhost:3000"
