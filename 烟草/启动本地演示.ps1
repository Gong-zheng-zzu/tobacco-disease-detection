$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Get-ChildItem -Path $root -Recurse -Filter manage.py -File |
  Where-Object { $_.FullName -match 'drf_test002' } |
  Select-Object -First 1 -ExpandProperty DirectoryName
$frontend = Get-ChildItem -Path $root -Recurse -Filter vite.config.js -File |
  Where-Object { $_.FullName -match 'app.*true.*tobacco' } |
  Select-Object -First 1 -ExpandProperty DirectoryName
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.InterfaceAlias -eq 'WLAN' -and $_.IPAddress -notmatch '^(127|169\.254)' } |
  Select-Object -First 1 -ExpandProperty IPAddress)
if (-not $lanIp) { $lanIp = '127.0.0.1' }

Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$backend'; & '.\.venv\Scripts\python.exe' manage.py runserver 0.0.0.0:8000 --noreload"
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$frontend'; `$env:VITE_API_HOST='http://$lanIp:8000'; npm run dev -- --host 0.0.0.0"
Write-Host "前端地址: http://$lanIp`:5173/#/login"
Write-Host '账号: admin'
Write-Host '密码: 123456'
