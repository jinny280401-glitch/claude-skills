#!/bin/bash
# ============================================================
# html2pdf.sh — PDF-Transfer 一键转换脚本
#
# 用法:
#   ./html2pdf.sh input.html "output.pdf"           # 默认 weasyprint + 自动打开
#   ./html2pdf.sh input.html "output.pdf" --no-open # 不打开
#   ./html2pdf.sh input.html "output.pdf" --check-only # 只检查密度
#   ENGINE=chrome ./html2pdf.sh input.html out.pdf  # 切到 headless Chrome
#
# 自检:
#   - 字体可用性
#   - 渲染成功
#   - 页数 + 每页字符数
#   - 留白警告（每页 < 200 字符）
# ============================================================

set -e

# ----- 参数解析 -----
if [ $# -lt 2 ]; then
  echo "用法: $0 input.html 'output.pdf' [--no-open|--check-only]"
  echo "      ENGINE=chrome $0 input.html out.pdf"
  exit 1
fi

INPUT="$1"
OUTPUT="$2"
FLAG="${3:-}"

# ----- 前置检查 -----
if [ ! -f "$INPUT" ]; then
  echo "❌ 输入文件不存在: $INPUT"
  exit 1
fi

# 绝对路径
INPUT_ABS="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"
OUTPUT_ABS="$(cd "$(dirname "$OUTPUT" 2>/dev/null)" 2>/dev/null && pwd)/$(basename "$OUTPUT")"
[ -z "$OUTPUT_ABS" ] && OUTPUT_ABS="$OUTPUT"

# 引擎选择
ENGINE="${ENGINE:-weasyprint}"

echo "▶ 输入: $INPUT_ABS"
echo "▶ 输出: $OUTPUT_ABS"
echo "▶ 引擎: $ENGINE"

# ----- 中文字体检查 -----
HAS_ZH=$(fc-list :lang=zh 2>/dev/null | grep -ciE "pingfang|heiti|songti|noto sans cjk" || true)
if [ "$HAS_ZH" -lt 1 ]; then
  echo "⚠ 未检测到系统中文字体,中文可能渲染失败"
  echo "  macOS 通常自带 PingFang/Heiti,如仍异常运行: brew install pango"
fi

# ----- 渲染 -----
case "$ENGINE" in
  weasyprint)
    weasyprint "$INPUT_ABS" "$OUTPUT_ABS" 2>&1 | grep -v "print-color-adjust" || true
    ;;
  chrome)
    CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if [ ! -x "$CHROME" ]; then
      echo "❌ Chrome 不在标准位置,改回 weasyprint"
      ENGINE=weasyprint
      weasyprint "$INPUT_ABS" "$OUTPUT_ABS" 2>&1 | grep -v "print-color-adjust" || true
    else
      "$CHROME" --headless --disable-gpu --no-pdf-header-footer \
        --print-to-pdf="$OUTPUT_ABS" "file://$INPUT_ABS" 2>&1 | tail -5
    fi
    ;;
  *)
    echo "❌ 未知引擎: $ENGINE (支持: weasyprint | chrome)"
    exit 1
    ;;
esac

# ----- 后置检查 -----
if [ ! -f "$OUTPUT_ABS" ]; then
  echo "❌ 渲染失败,无输出文件"
  exit 1
fi

SIZE=$(stat -f%z "$OUTPUT_ABS" 2>/dev/null || stat -c%s "$OUTPUT_ABS" 2>/dev/null)
echo "✓ 渲染完成: $(numfmt --to=iec --suffix=B $SIZE 2>/dev/null || echo "${SIZE}B")"

# ----- 密度自检 -----
echo ""
echo "━━━ 密度自检 ━━━"

# 用 Python 检查每页字符数(解压 PDF 流)
python3 - <<PY
import re, zlib, sys
with open("$OUTPUT_ABS", "rb") as f:
    raw = f.read()

# 解压所有流,找 /Type /Page 和文字
pages_raw = []
for m in re.finditer(rb'stream\r?\n', raw):
    end = raw.find(b'endstream', m.start())
    if end < 0: continue
    try:
        dec = zlib.decompress(raw[m.end():end].rstrip(b'\r\n'))
        pages_raw.append(dec)
    except: pass

# 提取所有文字
all_text = b' '.join(pages_raw).decode('utf-8', errors='ignore')
# 中文 + ASCII
chinese = re.findall(r'[一-鿿]', all_text)
chinese_count = len(chinese)
ascii_count = len(re.findall(r'[a-zA-Z0-9]', all_text))
total = chinese_count + ascii_count

print(f"  总字符: {total} (中 {chinese_count} + 英 {ascii_count})")

# 找 /Count
counts = []
for dec in pages_raw:
    for m in re.finditer(rb'/Type\s*/Pages.*?/Count\s+(\d+)', dec, re.DOTALL):
        counts.append(int(m.group(1)))
        break

# 兜底:数 /Type /Page
if not counts:
    n = 0
    for dec in pages_raw:
        n += len(re.findall(rb'/Type\s*/Page\b(?!s)', dec))
    counts = [n] if n else [0]

page_count = max(counts) if counts else 0
print(f"  页数:   {page_count}")

# 警告阈值(每页 < 200 字符)
if page_count == 0:
    print("  ⚠ 无法解析页数,跳过密度检查")
elif total / page_count < 200:
    print(f"  ⚠ 平均 {int(total/page_count)} 字符/页 — 留白过多!")
    print(f"     修法: 合并章节/缩小边距/加大字号,详见 references/density-rules.md")
else:
    print(f"  ✓ 密度: {int(total/page_count)} 字符/页 — OK")

# 空白页警告
if page_count > 0 and total / page_count < 100:
    print(f"  🚨 极可能存在空白页(平均 {int(total/page_count)} 字符/页)")
    sys.exit(2)
PY

EXIT=$?
echo ""

# ----- 打开 -----
if [ "$FLAG" != "--no-open" ] && [ "$FLAG" != "--check-only" ]; then
  open "$OUTPUT_ABS"
  echo "✓ 已打开: $OUTPUT_ABS"
fi

exit $EXIT
