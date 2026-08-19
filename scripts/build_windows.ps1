$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

npm --prefix frontend ci
npm --prefix frontend run build
py -m pip install -r desktop-requirements.txt
py -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name Webmark `
  --paths . `
  --add-data "frontend/dist;frontend_dist" `
  --collect-all trafilatura `
  --collect-all courlan `
  --collect-all htmldate `
  --collect-all justext `
  --collect-all webview `
  desktop_launcher.py

Write-Host "Built: $ProjectDir\dist\Webmark.exe"
