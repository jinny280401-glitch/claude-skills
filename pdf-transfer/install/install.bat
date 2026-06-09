@echo off
REM ============================================================
REM install.bat — PDF-Transfer Windows 安装脚本 (cmd.exe)
REM ============================================================
REM 用法:
REM   右键 → "以管理员身份运行" install.bat
REM   或: install.bat
REM
REM 自动检测:
REM   - Python 3 (py launcher 优先)
REM   - 包管理器: choco / scoop / winget
REM   - 现有 weasyprint
REM ============================================================

setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ============================================================
echo  PDF-Transfer Windows 安装
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "SKILL_NAME=pdf-transfer"

REM ----- 检测 Python -----
set "PY="
where python 2>nul >nul && set "PY=python"
where py 2>nul >nul && set "PY=py"
where python3 2>nul >nul && set "PY=python3"

if "%PY%"=="" (
    echo [X] 未找到 Python 3
    echo     下载: https://www.python.org/downloads/
    exit /b 1
)
echo [OK] Python: %PY%
%PY% --version
echo.

REM ----- 检测包管理器 -----
set "PKG="
where choco 2>nul >nul && set "PKG=choco"
where scoop 2>nul >nul && set "PKG=scoop"
where winget 2>nul >nul && set "PKG=winget"

if "%PKG%"=="" (
    echo [!] 未检测到包管理器 ^(choco/scoop/winget^)
    echo     建议安装 Chocolatey: https://chocolatey.org/install
    echo     或手动装 GTK3: https://github.com/nickvdyck/weasyprint-win
    echo.
    echo 跳过系统库安装,直接装 weasyprint ^(可能失败^)
) else (
    echo [OK] 包管理器: %PKG%
)
echo.

REM ----- 装 GTK3 runtime (weasyprint 依赖) -----
%PY% -c "import weasyprint" 2>nul
if %errorlevel% neq 0 (
    echo [i] 安装 GTK3 runtime (weasyprint 系统依赖)...
    if "%PKG%"=="choco" (
        choco install -y gtk-runtime
    ) else if "%PKG%"=="scoop" (
        scoop install gtk
    ) else if "%PKG%"=="winget" (
        echo [!] winget 暂无 gtk-runtime, 请手动下载:
        echo     https://github.com/nickvdyck/weasyprint-win/releases
    ) else (
        echo [!] 需手动装 GTK3:
        echo     下载 MSYS2 + pacman -S mingw-w64-x86_64-pango
        echo     或: https://github.com/nickvdyck/weasyprint-win
    )
    echo.
)

REM ----- 装 weasyprint -----
%PY% -c "import weasyprint" 2>nul
if %errorlevel% neq 0 (
    echo [i] 安装 weasyprint ^(Python 包^)...
    %PY% -m pip install --upgrade pip
    %PY% -m pip install weasyprint
) else (
    echo [OK] weasyprint 已安装
)
echo.

REM ----- 中文字体检查 -----
echo [i] 中文字体检查...
if exist "C:\Windows\Fonts\msyh.ttc" (
    echo [OK] Microsoft YaHei 已安装
) else if exist "C:\Windows\Fonts\simfang.ttf" (
    echo [OK] SimSun 已安装
) else (
    echo [!] 未检测到中文字体
    echo     Windows 7+: 控制面板 → 字体 → 应有 Microsoft YaHei
    echo     如缺失,运行: dism /online /add-package /packagepath:...
)

REM ----- 可选: 链接到 Claude Code skills 目录 -----
if exist "%USERPROFILE%\.claude\skills\" (
    echo.
    set /p REPLY="是否链接到 Claude Code skills 目录以便自动发现? [y/N]: "
    if /i "!REPLY!"=="y" (
        set "TARGET=%USERPROFILE%\.claude\skills\%SKILL_NAME%"
        if exist "!TARGET!" (
            rmdir "!TARGET!" 2>nul
        )
        mklink /D "!TARGET!" "%SCRIPT_DIR%" 2>nul || (
            xcopy /E /I /Y "%SCRIPT_DIR%" "!TARGET!"
        )
        echo [OK] 已链接: !TARGET!
    )
)

echo.
echo [i] 烟雾测试...
%PY% "%SCRIPT_DIR%scripts\html2pdf.py" "%SCRIPT_DIR%examples\集合竞价-2026-06-09.html" "%TEMP%\%SKILL_NAME%-smoke-test.pdf" --no-open
del "%TEMP%\%SKILL_NAME%-smoke-test.pdf" 2>nul

echo.
echo ============================================================
echo  安装完成!
echo  用法: %PY% "%SCRIPT_DIR%scripts\html2pdf.py" input.html output.pdf
echo ============================================================
endlocal
