# Cai dat video-factory tren Windows (chay 1 lan).
# Cach chay, tai thu muc repo:
#   powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
# Tuy chon: -DriveRoot "G:\My Drive\EDIT"   (bo trong thi script tu tim)
# File chi dung ky tu ASCII de Windows PowerShell 5.1 doc dung.

param([string]$DriveRoot = "")

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

Step "1/5 Cong cu: ffmpeg, Python 3.11, Node, Git"
$pkgs = @(
    @{ cmd = "ffmpeg"; id = "Gyan.FFmpeg" },
    @{ cmd = "node";   id = "OpenJS.NodeJS.LTS" },
    @{ cmd = "git";    id = "Git.Git" }
)
foreach ($p in $pkgs) {
    if (Have $p.cmd) { Write-Host "   co san: $($p.cmd)" }
    else {
        Write-Host "   cai: $($p.id)"
        winget install --id $p.id -e --accept-source-agreements --accept-package-agreements
    }
}
$hasPy311 = $false
if (Have "py") { & py -3.11 --version *> $null; $hasPy311 = ($LASTEXITCODE -eq 0) }
if (-not $hasPy311) {
    Write-Host "   cai: Python.Python.3.11"
    winget install --id Python.Python.3.11 -e --accept-source-agreements --accept-package-agreements
}
Refresh-Path

Step "2/5 Moi truong Python (.venv) va thu vien"
if (-not (Test-Path ".venv\Scripts\python.exe")) { & py -3.11 -m venv .venv }
& .venv\Scripts\python.exe -m pip install --upgrade pip -q
& .venv\Scripts\python.exe -m pip install -e ".[dev]" -q
if ($LASTEXITCODE -ne 0) { throw "pip install loi" }

Step "3/5 Remotion (chu dong)"
Push-Location remotion
npm install --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "npm install loi" }
Pop-Location

Step "4/5 Tim thu muc EDIT trong Google Drive"
if (-not $DriveRoot) {
    $found = @()
    foreach ($d in Get-PSDrive -PSProvider FileSystem) {
        $root = $d.Root
        # "My Drive" (tieng Anh) hoac "Drive cua toi" (tieng Viet) ...
        $candidates = @(Join-Path $root "My Drive\EDIT")
        Get-ChildItem $root -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "*Drive*" } |
            ForEach-Object { $candidates += (Join-Path $_.FullName "EDIT") }
        foreach ($c in $candidates) {
            if (Test-Path (Join-Path $c "source g*")) { $found += $c }
        }
    }
    $found = $found | Select-Object -Unique
    if ($found.Count -ge 1) { $DriveRoot = $found[0]; Write-Host "   tim thay: $DriveRoot" }
    else {
        Write-Host "   Khong tu tim thay. Mo Google Drive for Desktop, bat 'Available offline' cho thu muc EDIT."
        $DriveRoot = Read-Host "   Dan duong dan thu muc EDIT (vd G:\My Drive\EDIT)"
    }
}
$posix = $DriveRoot.TrimEnd('\').Replace('\', '/')
# UTF-8 khong BOM de Python tomllib doc duoc
[IO.File]::WriteAllText((Join-Path (Get-Location) "vf.toml"), "drive_root = `"$posix`"`n",
                        (New-Object System.Text.UTF8Encoding($false)))
Write-Host "   da ghi vf.toml: drive_root = $posix"

Step "5/5 Kiem tra"
& .venv\Scripts\vf.exe doctor
if ($LASTEXITCODE -eq 0) {
    Write-Host "`nXONG. Mo Claude Code (phien Local) o thu muc nay va go: /smilee-video" -ForegroundColor Green
} else {
    Write-Host "`nCon loi o tren, sua theo goi y roi chay lai script." -ForegroundColor Yellow
}
