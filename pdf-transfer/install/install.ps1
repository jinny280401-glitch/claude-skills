# ============================================================
# install.ps1 — PDF-Transfer Windows 安装脚本 (PowerShell)
# ============================================================
# 用法 (PowerShell,推荐):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\install.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$SkillName = "pdf-transfer"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

function Write-Step($msg) { Write-Host "▶ $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "⚠ $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "✗ $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " PDF-Transfer Windows 安装 (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ----- 检测 Python -----
$py = $null
foreach ($cmd in @("python", "py", "python3")) {
    $p = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($p) { $py = $cmd; break }
}
if (-not $py) {
    Write-Fail "未找到 Python 3"
    Write-Host "  下载: https://www.python.org/downloads/"
    exit 1
}
Write-OK "Python: $py"
& $py --version

# ----- 检测包管理器 -----
$pkg = $null
foreach ($p in @("choco", "scoop", "winget")) {
    if (Get-Command $p -ErrorAction SilentlyContinue) {
        $pkg = $p
        break
    }
}
if ($pkg) {
    Write-OK "包管理器: $pkg"
} else {
    Write-Warn "未检测到包管理器 (choco/scoop/winget),GTK3 runtime 需手动装"
}

# ----- 检查 weasyprint -----
$hasWeasy = $false
try {
    & $py -c "import weasyprint" 2>$null
    if ($LASTEXITCODE -eq 0) { $hasWeasy = $true }
} catch {}

if (-not $hasWeasy) {
    # 装 GTK3
    Write-Step "安装 GTK3 runtime..."
    switch ($pkg) {
        "choco"  { choco install -y gtk-runtime }
        "scoop"  { scoop install gtk }
        "winget" {
            Write-Warn "winget 暂无 gtk-runtime"
            Write-Host "  手动下载: https://github.com/nickvdyck/weasyprint-win/releases"
        }
        default  { Write-Warn "请手动装 GTK3 runtime" }
    }

    # 装 weasyprint
    Write-Step "安装 weasyprint (Python 包)..."
    & $py -m pip install --upgrade pip
    & $py -m pip install weasyprint
    Write-OK "weasyprint 安装完成"
} else {
    Write-OK "weasyprint 已安装"
}

# ----- 中文字体检查 -----
Write-Step "中文字体检查..."
$zhFonts = @("C:\Windows\Fonts\msyh.ttc", "C:\Windows\Fonts\msyh.ttf", "C:\Windows\Fonts\simfang.ttf")
$hasFont = $false
foreach ($f in $zhFonts) {
    if (Test-Path $f) { $hasFont = $true; break }
}
if ($hasFont) {
    Write-OK "中文字体已就绪"
} else {
    Write-Warn "未检测到 Microsoft YaHei / SimSun"
}

# ----- 可选: 链接到 Claude Code skills -----
$claudeSkills = Join-Path $env:USERPROFILE ".claude\skills"
if (Test-Path $claudeSkills) {
    Write-Host ""
    $reply = Read-Host "是否链接到 Claude Code skills 目录? [y/N]"
    if ($reply -match "^[Yy]$") {
        $target = Join-Path $claudeSkills $SkillName
        if (Test-Path $target) { Remove-Item $target -Recurse -Force }
        # 软链接
        $wscript = New-Object -ComObject WScript.Shell
        $shortcut = $wscript.CreateShortcut($target)
        $shortcut.TargetPath = $ScriptDir
        $shortcut.Save()
        Write-OK "已创建快捷方式: $target → $ScriptDir"
    }
}

# ----- 烟雾测试 -----
Write-Host ""
Write-Step "烟雾测试..."
$tmpPdf = Join-Path $env:TEMP "$SkillName-smoke-test.pdf"
try {
    & $py "$ScriptDir\scripts\html2pdf.py" `
        "$ScriptDir\examples\集合竞价-2026-06-09.html" `
        $tmpPdf --no-open
} finally {
    if (Test-Path $tmpPdf) { Remove-Item $tmpPdf -Force }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 安装完成!" -ForegroundColor Green
Write-Host " 用法: $py $ScriptDir\scripts\html2pdf.py input.html output.pdf" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
