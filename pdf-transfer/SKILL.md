---
name: pdf-transfer
description: 把结构化文本/数据/Word-like 内容转成 A4 PDF 的工作流。核心约束：技术不要留白 — 每页都要塞满有意义的内容。集成 weasyprint（主力）+ headless Chrome（备选）双引擎。触发条件：用户提到"做成 PDF"、"导出 PDF"、"排版一下"、"Word 转 PDF"、"留白太多"、"压紧一点"、"premium A4 风格"、"PDF 排版"等。跨平台支持 macOS / Linux / 统信 UOS / Windows。
---

# PDF-Transfer — A4 排版工作流（跨平台）

> **核心约束：技术不要留白。** 每页都要塞满有意义的内容，最后一页不能是半页。

把结构化文本（报告、表格、清单、合同、数据汇总）转成 A4 PDF 的三步工作流。
**默认渲染后端：weasyprint**（macOS / Linux / 统信 UOS / Windows 全部支持）。
**备选引擎：headless Chrome**（用系统已装的 Chrome / Edge / Chromium）。

## 使用场景

- 报告型 PDF（早盘集合竞价日报、研究报告、内参）
- 表格密集型 PDF（数据清单、对比表、矩阵）
- Word-like 文档（合同、纪要、SOP、模板）
- 需要"留白少、专业感"的任何 A4 输出

用户说：
- "把这份报告做成 PDF"
- "按 premium A4 风格做一份"
- "这个 PDF 留白太多，压紧一点"
- "Word 转 PDF 工作流"

## 三步工作流

### 1. 选模板

```bash
ls templates/
# compact-report.html   ← 报告型（封面+多章）
```

复制模板到工作目录：

```bash
cp templates/compact-report.html my-report.html
```

### 2. 改内容

模板已内置"不留白"的 CSS（详见 `references/density-rules.md`）：
- 16mm 边距（比 premium 18mm 更紧）
- 9.2pt 正文 / 1.55 行高
- 表格紧凑 padding
- 自然分页（不强制）

替换占位符：`{{TITLE}}`、`{{CH1_TITLE}}` 等。

### 3. 导出 + 自检

**Unix / macOS / UOS：**
```bash
./scripts/html2pdf.py my-report.html "我的报告.pdf"
```

**Windows (PowerShell)：**
```powershell
python scripts\html2pdf.py my-report.html "我的报告.pdf"
```

脚本自动完成：
1. weasyprint 渲染
2. 统计页数 + 每页字符数
3. **如果某页字符数 < 200，警告"留白过多"** ← 核心自检
4. 自动 `open` 打开 PDF

## 跨平台安装

### macOS
```bash
brew install pango
pip install weasyprint
```

### Linux (Ubuntu/Debian) / 统信 UOS
```bash
sudo apt-get update
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \
                            libfontconfig1 fonts-noto-cjk
pip install weasyprint
```

### Windows
```powershell
# 1. 装 GTK3 runtime (任选一种)
choco install gtk-runtime     # Chocolatey
scoop install gtk             # Scoop

# 2. 装 weasyprint
pip install weasyprint
```

或直接跑 `install/install.bat` / `install/install.ps1` 一键安装。

### 字体自动检测
脚本会扫描系统字体，跨平台适配：
- macOS: `PingFang SC / Heiti SC / Songti SC`
- Linux/UOS: `Noto Sans CJK SC / WenQuanYi Zen Hei`
- Windows: `Microsoft YaHei / SimSun`

详见 `references/platform-fonts.md`。

## 命令速查

| 需求 | 命令 |
|------|------|
| 基础导出 | `python scripts/html2pdf.py input.html output.pdf` |
| 不自动打开 | `python scripts/html2pdf.py input.html output.pdf --no-open` |
| 仅检查密度 | `python scripts/html2pdf.py input.html output.pdf --check-only` |
| 用 Chrome 渲染 | `ENGINE=chrome python scripts/html2pdf.py input.html output.pdf` |

## 密度自检表（导出后必看）

打开 PDF 后，**逐页过这 5 项**：

| 检查项 | 期望 | 修法 |
|---|---|---|
| 最后一页 | 不能 < 半页 | 内容不够就合并到倒数第二页；或扩成完整章节 |
| 中间页 | 字符密度均匀 | 表格行高不均 → 用 padding 统一 |
| 标题孤行 | 标题不和正文分离 | 调 margin-bottom |
| 表格断裂 | 表格不跨页断行 | 加 `page-break-inside: avoid` |
| 空白页 | **绝不允许** | 99% 是空 `<section>` 或多余 page-break |

## 常见问题

**Q: 字体变成方块 / 乱码？**
A: 模板 font-family 顺序是 `PingFang SC → Heiti SC → Songti SC → Microsoft YaHei → Noto Sans CJK SC`。
各平台会自动取第一个可用的。如果全失败：
- macOS: 系统自带，应无问题
- Linux/UOS: `apt install fonts-noto-cjk`
- Windows: 系统自带雅黑，应无问题

**Q: weasyprint 报 `libpango-1.0-0 not found`？**
A:
- macOS: `brew install pango harfbuzz libdatrie libthai`
- Linux/UOS: `apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1`
- Windows: 装 GTK3 runtime（见上面"Windows"小节）

**Q: 想要更专业的编辑风（premium/Harvard 感）？**
A: 参考 `~/.claude/skills/premium-a4-printable-pdfs/SKILL.md` 体系，把封面/章节/页脚风格再叠上去。
本 skill 优先"密度"而非"编辑感"。

**Q: 表格列太挤？**
A: 模板里 `.col-code` 14% / `.col-name` 18% / `.col-num` 12% / `.col-text` auto，根据实际列数调整百分比。

**Q: 内容超出 A4 留白边距？**
A: 模板 `@page { margin: 16mm }` 已经安全。如果超出，说明内容太密 — 该拆页了。

**Q: Windows 上 open 命令报错？**
A: Windows 用 `os.startfile` 自动调用默认 PDF 阅读器。脚本已处理。如果还报错，加 `--no-open` 然后手动打开。

## 文件结构

```
pdf-transfer/
├── SKILL.md                      ← 本文件
├── README.md                     ← 快速上手
├── CHANGELOG.md                  ← 版本日志
├── LICENSE                       ← MIT
├── templates/
│   └── compact-report.html       ← 报告型
├── scripts/
│   ├── html2pdf.py               ← 跨平台转换（主力）
│   └── html2pdf.sh               ← Unix 兼容（旧版）
├── install/
│   ├── install.sh                ← macOS / Linux / UOS
│   ├── install.bat               ← Windows (cmd)
│   └── install.ps1               ← Windows (PowerShell)
├── examples/
│   ├── 集合竞价-2026-06-09.html
│   └── 集合竞价-2026-06-09.pdf
└── references/
    ├── density-rules.md          ← 排版规则
    └── platform-fonts.md         ← 跨平台字体配置
```

## 写在最后

本 skill 的诞生场景：2026/06/09 早盘集合竞价分析报告，目标是快速出 A4 PDF 给用户。
**第一版用了 premium-a4-printable-pdfs 的强制分页 — 大量留白，被用户当场打回。**

教训：**"premium 编辑感"和"不留白"在排版上是反方向。**
- premium → 章节独立成页，呼吸感强
- 不留白 → 章节自然流，密度优先

本 skill 选后者。如果以后做正式发布物（年报、白皮书），再用 premium 体系。
