$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Test-Port($Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try { $client.Connect('127.0.0.1', $Port); return $true }
    catch { return $false }
    finally { $client.Dispose() }
}

$python = Join-Path $PSScriptRoot 'backend/venv/Scripts/python.exe'
$node = (Get-Command node -ErrorAction Stop).Source
$next = Join-Path $PSScriptRoot 'frontend/node_modules/next/dist/bin/next'
if (!(Test-Path $python) -or !(Test-Path $next)) {
    throw 'Install the backend and frontend dependencies first. See README.md.'
}
if (!(Test-Path 'backend/.env')) { throw 'Configure backend/.env first. See README.md.' }

# Reuse the workspace-local PostgreSQL installation when configured.
$config = Get-Content 'backend/.env' -Raw
if ($config -match '(?m)^DATABASE_URL=.*127\.0\.0\.1:55432/' -and !(Test-Port 55432)) {
    $pgctl = Join-Path $PSScriptRoot '.audit/node_modules/@embedded-postgres/windows-x64/native/bin/pg_ctl.exe'
    if (!(Test-Path $pgctl)) { throw 'Local PostgreSQL is missing. Configure an existing PostgreSQL database in backend/.env.' }
    & $pgctl -D (Join-Path $PSScriptRoot '.audit/postgres') -l (Join-Path $PSScriptRoot '.audit/postgres/server.log') -o '-h 127.0.0.1 -p 55432' -w start
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL failed to start.' }
}

New-Item -ItemType Directory -Force '.local' | Out-Null
if (!(Test-Port 8001)) {
    Start-Process -FilePath $python -ArgumentList '-m uvicorn app.main:app --host 127.0.0.1 --port 8001' -WorkingDirectory (Join-Path $PSScriptRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot '.local/backend.log') -RedirectStandardError (Join-Path $PSScriptRoot '.local/backend-error.log') | Out-Null
}
if (!(Test-Port 3000)) {
    Start-Process -FilePath $node -ArgumentList ('"{0}" dev --hostname 127.0.0.1 --port 3000' -f $next) -WorkingDirectory (Join-Path $PSScriptRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot '.local/frontend.log') -RedirectStandardError (Join-Path $PSScriptRoot '.local/frontend-error.log') | Out-Null
}
Write-Host 'TripPilot is starting at http://localhost:3000. Logs: .local/'
Write-Host 'Enter SECRET_KEY from backend/.env in the app Settings. Ollama is optional for generation, required for modifications.'
