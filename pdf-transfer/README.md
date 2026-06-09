# PDF-Transfer

> **核心约束：技术不要留白。** 把结构化文本转成紧凑、专业的 A4 PDF。

跨平台（macOS / Linux / 统信 UOS / Windows）一站式工作流，集成 weasyprint + headless Chrome 双引擎。

## 30 秒上手

```bash
# 1. 装依赖
./install/install.sh    # macOS / Linux / UOS
# 或 install\install.bat / install\install.ps1  ← Windows

# 2. 复制模板
cp templates/compact-report.html my-report.html

# 3. 改内容(替换 {{TITLE}} 等占位符)

# 4. 导出
python3 scripts/html2pdf.py my-report.html "我的报告.pdf"
```

脚本会自动：渲染 → 密度自检 → 打开 PDF。

## 核心特性

- **不留白**：每页 ≥ 200 字符（脚本自检），最后一页 ≥ 半页
- **跨平台**：macOS / Linux / UOS / Windows 全覆盖
- **抗孤行 / 抗断页**：标题不孤行、表格不跨页断
- **双引擎**：weasyprint（主力）+ Chrome（备选）
- **OpenClaw 兼容**：SKILL.md frontmatter 符合 OpenClaw 规范

## 何时使用 vs 不使用

✅ 报告型 PDF、表格密集 PDF、Word-like 文档、需要密度优先的 A4 输出
❌ 演示幻灯片（用 pptx skill）、交互式网页、学术论文（用 LaTeX）

## 文件结构

```
pdf-transfer/
├── SKILL.md                      # OpenClaw 格式主入口
├── README.md                     # 本文件
├── CHANGELOG.md
├── LICENSE                       # MIT
├── templates/
│   └── compact-report.html       # 报告型模板
├── scripts/
│   ├── html2pdf.py               # 跨平台转换（Python）
│   └── html2pdf.sh               # Unix 兼容
├── install/
│   ├── install.sh                # macOS / Linux / UOS
│   ├── install.bat               # Windows cmd
│   └── install.ps1               # Windows PowerShell
├── examples/
│   ├── 集合竞价-2026-06-09.html
│   └── 集合竞价-2026-06-09.pdf
└── references/
    ├── density-rules.md          # 排版规则
    └── platform-fonts.md         # 跨平台字体
```

## 跨平台安装命令

### macOS
```bash
brew install pango
pip3 install weasyprint
```

### Linux (Ubuntu/Debian) / UOS
```bash
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1 fonts-noto-cjk
pip3 install weasyprint
```

### Windows
```powershell
choco install -y gtk-runtime   # 或 scoop install gtk
pip install weasyprint
```

详见 [SKILL.md](SKILL.md)。

## 命令速查

| 需求 | 命令 |
|------|------|
| 基础导出 | `python3 scripts/html2pdf.py input.html output.pdf` |
| 不自动打开 | `... --no-open` |
| 仅检查密度 | `... --check-only` |
| 用 Chrome 渲染 | `ENGINE=chrome python3 scripts/html2pdf.py ...` |

## License

MIT
