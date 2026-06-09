#!/bin/bash
# ============================================================
# install.sh — PDF-Transfer 跨平台安装 (macOS / Linux / 统信 UOS)
# ============================================================
# 用法:
#   chmod +x install.sh
#   ./install.sh
#
# 自动检测:
#   - 包管理器 (brew / apt / dnf / yum / pacman)
#   - Python (系统 / homebrew)
#   - 现有 weasyprint / pango
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="pdf-transfer"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}▶${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
fail()  { echo -e "${RED}✗${NC} $1"; }

# ----- 检测 OS -----
detect_os() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macos"
  elif [ -f /etc/os-release ]; then
    . /etc/os-release
    case "$ID" in
      ubuntu|debian|deepin|uos|kylin)
        echo "debian" ;;
      fedora|rhel|centos|rocky|almalinux)
        echo "redhat" ;;
      arch|manjaro)
        echo "arch" ;;
      *)
        echo "linux-unknown" ;;
    esac
  else
    echo "unknown"
  fi
}

# ----- 检测包管理器 -----
detect_pkg_mgr() {
  if command -v brew &>/dev/null; then
    echo "brew"
  elif command -v apt-get &>/dev/null; then
    echo "apt"
  elif command -v dnf &>/dev/null; then
    echo "dnf"
  elif command -v yum &>/dev/null; then
    echo "yum"
  elif command -v pacman &>/dev/null; then
    echo "pacman"
  else
    echo "none"
  fi
}

# ----- 检测 Python -----
detect_python() {
  # 优先: python3.11 / python3.12 (weasyprint 兼容性好)
  for v in 3.12 3.11 3.10 3.9; do
    if command -v "python$v" &>/dev/null; then
      echo "python$v"
      return
    fi
  done
  if command -v python3 &>/dev/null; then
    echo "python3"
    return
  fi
  echo ""
}

OS=$(detect_os)
PKG=$(detect_pkg_mgr)
PY=$(detect_python)

info "OS:     $OS"
info "包管理器: $PKG"
info "Python:  ${PY:-未找到}"

# ----- 检查 weasyprint -----
WEASY_OK=0
if [ -n "$PY" ] && $PY -c "import weasyprint" 2>/dev/null; then
  WEASY_OK=1
  ok "weasyprint 已安装"
fi

# ----- 装系统库 (pango) -----
if [ "$WEASY_OK" -eq 0 ]; then
  echo ""
  info "安装 weasyprint 系统依赖 (pango + harfbuzz + libfontconfig)..."

  case "$PKG" in
    brew)
      if ! brew list pango &>/dev/null; then
        brew install pango harfbuzz libdatrie libthai
      else
        ok "pango 已安装 (brew)"
      fi
      # 中文字体
      if ! fc-list :lang=zh 2>/dev/null | grep -qi "noto.*cjk\|pingfang\|heiti"; then
        warn "未检测到中文字体,尝试安装 noto-cjk"
        brew install --cask font-noto-sans-cjk-sc 2>/dev/null || true
      else
        ok "中文字体已就绪"
      fi
      ;;
    apt)
      sudo apt-get update -qq
      sudo apt-get install -y \
        libpango-1.0-0 libpangoft2-1.0-0 \
        libharfbuzz0b libfontconfig1 \
        libpangocairo-1.0-0 libcairo2 \
        libgdk-pixbuf2.0-0 libffi-dev \
        shared-mime-info
      # 中文字体
      if ! fc-list :lang=zh 2>/dev/null | grep -qi "noto.*cjk\|wqy"; then
        warn "未检测到中文字体,安装 noto-cjk"
        sudo apt-get install -y fonts-noto-cjk
      else
        ok "中文字体已就绪"
      fi
      ;;
    dnf|yum)
      sudo $PKG install -y \
        pango harfbuzz fontconfig \
        cairo gdk-pixbuf2 pango-devel
      sudo $PKG install -y google-noto-sans-cjk-sc-fonts 2>/dev/null || \
        sudo $PKG install -y wqy-zenhei-fonts 2>/dev/null || \
        warn "中文字体未自动安装,请手动装 noto-cjk"
      ;;
    pacman)
      sudo pacman -S --noconfirm \
        pango harfbuzz fontconfig cairo gdk-pixbuf2
      sudo pacman -S --noconfirm noto-fonts-cjk 2>/dev/null || \
        warn "中文字体未自动安装,请手动装 noto-fonts-cjk"
      ;;
    none)
      fail "未检测到包管理器,请手动安装 pango + harfbuzz + libfontconfig"
      exit 1
      ;;
  esac
fi

# ----- 装 Python 包 -----
if [ "$WEASY_OK" -eq 0 ]; then
  if [ -z "$PY" ]; then
    fail "未找到 Python,请先安装 Python 3.9+"
    exit 1
  fi

  info "安装 weasyprint (Python 包)..."
  $PY -m pip install --user --upgrade pip 2>/dev/null || true
  $PY -m pip install --user weasyprint

  ok "weasyprint 安装完成"
fi

# ----- 设置可执行 -----
chmod +x "$SCRIPT_DIR/scripts/html2pdf.py"
chmod +x "$SCRIPT_DIR/scripts/html2pdf.sh" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/install/install.sh"

# ----- 可选: 装到 ~/.claude/skills/ 让 agent 自动发现 -----
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
if [ -d "$HOME/.claude" ] && [ -d "$CLAUDE_SKILLS_DIR" ]; then
  echo ""
  read -p "是否将 $SKILL_NAME 链接到 $CLAUDE_SKILLS_DIR 让 Claude Code 自动发现? [y/N] " REPLY
  if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    TARGET="$CLAUDE_SKILLS_DIR/$SKILL_NAME"
    if [ -L "$TARGET" ]; then
      rm "$TARGET"
    fi
    ln -s "$SCRIPT_DIR" "$TARGET"
    ok "已链接: $TARGET → $SCRIPT_DIR"
    info "重启 Claude Code 后,此 skill 可被自动调用"
  fi
fi

# ----- 烟雾测试 -----
echo ""
info "烟雾测试..."
$PY "$SCRIPT_DIR/scripts/html2pdf.py" \
  "$SCRIPT_DIR/examples/集合竞价-2026-06-09.html" \
  "/tmp/${SKILL_NAME}-smoke-test.pdf" \
  --no-open 2>&1 | tail -10
rm -f "/tmp/${SKILL_NAME}-smoke-test.pdf"

echo ""
ok "安装完成! 使用方法:"
echo "    $PY $SCRIPT_DIR/scripts/html2pdf.py input.html output.pdf"
