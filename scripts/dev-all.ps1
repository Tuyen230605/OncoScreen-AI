# Mở 2 cửa sổ chạy backend + frontend (Windows PowerShell)
$root = (Resolve-Path "$PSScriptRoot\..").Path
$uvicorn = if (Test-Path "$root\.venv\Scripts\uvicorn.exe") { "$root\.venv\Scripts\uvicorn.exe" } else { "uvicorn" }
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\backend'; & '$uvicorn' app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\frontend'; npm run dev"
Write-Host "Backend: http://localhost:8000/docs | Frontend: http://localhost:3000"

