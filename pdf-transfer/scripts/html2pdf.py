#!/usr/bin/env python3
"""
html2pdf.py — PDF-Transfer 跨平台转换脚本
============================================

用法:
    python html2pdf.py input.html "output.pdf"              # 默认 weasyprint + 自动打开
    python html2pdf.py input.html "output.pdf" --no-open   # 不打开
    python html2pdf.py input.html "output.pdf" --check-only # 只检查密度
    ENGINE=chrome python html2pdf.py input.html out.pdf     # 切到 headless Chrome

跨平台支持:
    - macOS  : open <file>
    - Linux  : xdg-open <file>
    - Windows: os.startfile(<file>)

依赖:
    pip install weasyprint
    系统库: pango + harfbuzz + libfontconfig (见 SKILL.md 安装章节)
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import zlib
from pathlib import Path


# ============================================================
# 工具函数
# ============================================================

def detect_platform() -> str:
    """返回标准化平台名: macos | linux | windows | unknown"""
    s = platform.system().lower()
    if s == "darwin":
        return "macos"
    if s == "linux":
        # 统信 UOS / Deepin 都被识别为 linux
        return "linux"
    if s in ("windows", "win32"):
        return "windows"
    return "unknown"


def abspath(p: str) -> str:
    """把相对路径转成绝对路径(基于调用 shell 的 cwd)"""
    return str(Path(p).expanduser().resolve())


def check_zh_fonts() -> tuple[bool, list[str]]:
    """检测系统中文字体,返回 (是否充足, 找到的字体列表)"""
    target_patterns = [
        r"pingfang", r"heiti", r"songti",       # macOS
        r"noto\s*sans\s*cjk", r"wenquanyi",     # Linux
        r"microsoft\s*yahei", r"simsun",        # Windows
    ]
    pat = re.compile("|".join(target_patterns), re.IGNORECASE)
    found: list[str] = []
    try:
        if detect_platform() == "windows":
            # Windows: 直接查注册表/C:/Windows/Fonts
            fonts_dir = Path("C:/Windows/Fonts")
            if fonts_dir.exists():
                for f in fonts_dir.iterdir():
                    if pat.search(f.name):
                        found.append(f.name)
        else:
            # macOS / Linux: 用 fc-list
            out = subprocess.run(
                ["fc-list", ":lang=zh", "file"],
                capture_output=True, text=True, timeout=5
            )
            for line in out.stdout.splitlines():
                m = re.match(r"^(.+?):", line)
                if m and pat.search(m.group(1)):
                    found.append(m.group(1).split("/")[-1])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # 去重
    seen = set()
    unique = []
    for f in found:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return (len(unique) > 0, unique)


def check_weasyprint() -> tuple[bool, str | None]:
    """检查 weasyprint 是否可用"""
    try:
        import weasyprint  # noqa: F401
        return (True, None)
    except ImportError as e:
        return (False, str(e))


def find_chrome() -> str | None:
    """查找系统 Chrome / Edge / Chromium,返回可执行路径"""
    candidates = {
        "macos": [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ],
        "linux": [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/microsoft-edge",
            "/snap/bin/chromium",
        ],
        "windows": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ],
    }
    pf = detect_platform()
    for c in candidates.get(pf, []):
        if Path(c).exists():
            return c
    # 兜底: which 命令
    for name in ("google-chrome", "chromium", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    return None


def open_file(path: str) -> None:
    """跨平台打开文件(用系统默认程序)"""
    pf = detect_platform()
    try:
        if pf == "macos":
            subprocess.Popen(["open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif pf == "linux":
            subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif pf == "windows":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            print(f"  ⚠ 未知平台,无法自动打开: {path}")
    except Exception as e:
        print(f"  ⚠ 自动打开失败: {e}")


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ============================================================
# 渲染
# ============================================================

def render_with_weasyprint(input_abs: str, output_abs: str) -> tuple[bool, str]:
    """用 weasyprint 渲染,返回 (成功, 错误信息)"""
    try:
        from weasyprint import HTML
        # 静默 weasyprint 自身的 WARNING
        import logging
        logging.getLogger("weasyprint").setLevel(logging.ERROR)
        HTML(filename=input_abs).write_pdf(output_abs)
        return (True, "")
    except Exception as e:
        return (False, str(e))


def render_with_chrome(chrome: str, input_abs: str, output_abs: str) -> tuple[bool, str]:
    """用 headless Chrome 渲染"""
    try:
        cmd = [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={output_abs}",
            f"file://{input_abs}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return (False, result.stderr[:500] or "chrome 退出非 0")
        return (True, "")
    except Exception as e:
        return (False, str(e))


# ============================================================
# 密度自检
# ============================================================

def density_check(pdf_path: str) -> int:
    """检查 PDF 密度,返回 0(OK)/1(警告)/2(严重)"""
    try:
        raw = Path(pdf_path).read_bytes()
    except Exception as e:
        print(f"  ⚠ 读取 PDF 失败: {e}")
        return 0

    # 解压所有流
    all_text_chunks: list[str] = []
    for m in re.finditer(rb"stream\r?\n", raw):
        end = raw.find(b"endstream", m.start())
        if end < 0:
            continue
        try:
            dec = zlib.decompress(raw[m.end():end].rstrip(b"\r\n"))
            all_text_chunks.append(dec.decode("utf-8", errors="ignore"))
        except Exception:
            pass

    all_text = " ".join(all_text_chunks)
    chinese = len(re.findall(r"[一-鿿]", all_text))
    ascii_ = len(re.findall(r"[a-zA-Z0-9]", all_text))
    total = chinese + ascii_

    print(f"  总字符: {total} (中 {chinese} + 英 {ascii_})")

    # 找页数(/Count in /Pages)
    page_count = 0
    for chunk in all_text_chunks:
        m = re.search(r"/Type\s*/Pages.*?/Count\s+(\d+)", chunk, re.DOTALL)
        if m:
            page_count = int(m.group(1))
            break

    # 兜底: 数 /Type /Page
    if page_count == 0:
        n = 0
        for chunk in all_text_chunks:
            n += len(re.findall(r"/Type\s*/Page\b(?!s)", chunk))
        page_count = n

    print(f"  页数:   {page_count}")

    if page_count == 0:
        print("  ⚠ 无法解析页数,跳过密度检查")
        return 0

    avg = total / page_count
    if avg < 100:
        print(f"  🚨 极可能存在空白页(平均 {int(avg)} 字符/页)")
        return 2
    if avg < 200:
        print(f"  ⚠ 平均 {int(avg)} 字符/页 — 留白过多!")
        print(f"     修法: 合并章节/缩小边距/加大字号,详见 references/density-rules.md")
        return 1
    print(f"  ✓ 密度: {int(avg)} 字符/页 — OK")
    return 0


# ============================================================
# 主流程
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="PDF-Transfer 一键转换 (weasyprint 跨平台)"
    )
    parser.add_argument("input", help="输入 HTML 文件")
    parser.add_argument("output", help="输出 PDF 路径")
    parser.add_argument(
        "--no-open", action="store_true", help="不自动打开"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="只检查密度,不重新渲染"
    )
    parser.add_argument(
        "--engine", choices=["weasyprint", "chrome", "auto"], default=None,
        help="渲染引擎(默认读 $ENGINE 环境变量,否则 weasyprint)"
    )
    args = parser.parse_args()

    engine = args.engine or os.environ.get("ENGINE", "weasyprint").lower()
    if engine == "auto":
        ok, _ = check_weasyprint()
        chrome = find_chrome()
        engine = "weasyprint" if ok else ("chrome" if chrome else "weasyprint")

    input_abs = abspath(args.input)
    output_abs = abspath(args.output)

    if not Path(input_abs).exists():
        print(f"❌ 输入文件不存在: {input_abs}")
        return 1

    print(f"▶ 输入:  {input_abs}")
    print(f"▶ 输出:  {output_abs}")
    print(f"▶ 引擎:  {engine}")
    print(f"▶ 平台:  {detect_platform()}")
    print()

    # --check-only 跳过渲染
    if args.check_only:
        if not Path(output_abs).exists():
            print(f"❌ PDF 不存在,无法检查: {output_abs}")
            return 1
        return density_check(output_abs)

    # 字体自检
    has_zh, fonts = check_zh_fonts()
    if has_zh:
        print(f"✓ 中文字体: 找到 {len(fonts)} 个 (例: {', '.join(fonts[:3])})")
    else:
        print("⚠ 未检测到中文字体,中文可能渲染失败")
        pf = detect_platform()
        if pf == "linux":
            print("  建议: sudo apt install fonts-noto-cjk")
        elif pf == "windows":
            print("  建议: 控制面板 → 字体 → 安装 Microsoft YaHei / SimSun")
        elif pf == "macos":
            print("  异常: macOS 应自带 PingFang SC")

    print()

    # 渲染
    t0 = time.time()
    if engine == "weasyprint":
        ok, err = check_weasyprint()
        if not ok:
            print(f"❌ weasyprint 不可用: {err[:200]}")
            print("  安装: pip install weasyprint")
            chrome = find_chrome()
            if chrome:
                print(f"  找到 Chrome 备选: {chrome}")
                print(f"  重试: ENGINE=chrome python {sys.argv[0]} {args.input} {args.output}")
            return 1
        ok, err = render_with_weasyprint(input_abs, output_abs)
    elif engine == "chrome":
        chrome = find_chrome()
        if not chrome:
            print("❌ 未找到 Chrome / Edge / Chromium")
            print("  macOS: brew install --cask google-chrome")
            print("  Linux: sudo apt install chromium-browser")
            print("  Windows: 下载安装 Chrome 或 Edge")
            return 1
        print(f"  Chrome 路径: {chrome}")
        ok, err = render_with_chrome(chrome, input_abs, output_abs)
    else:
        print(f"❌ 未知引擎: {engine}")
        return 1

    if not ok:
        print(f"❌ 渲染失败: {err}")
        return 1

    elapsed = time.time() - t0
    size = Path(output_abs).stat().st_size
    print(f"✓ 渲染完成: {human_size(size)} ({elapsed:.1f}s)")
    print()

    # 密度自检
    print("━━━ 密度自检 ━━━")
    density_result = density_check(output_abs)
    print()

    # 自动打开
    if not args.no_open:
        open_file(output_abs)
        print(f"✓ 已尝试打开: {output_abs}")

    return density_result


if __name__ == "__main__":
    sys.exit(main())
