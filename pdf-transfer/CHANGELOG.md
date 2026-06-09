# Changelog

All notable changes to PDF-Transfer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-06-09

### Added
- 首个公开版本（诞生于 2026/06/09 早盘集合竞价分析报告场景）
- 跨平台支持：macOS / Linux (Ubuntu/Debian) / 统信 UOS / Windows
- 双渲染引擎：weasyprint（主力）+ headless Chrome（备选）
- 紧凑排版 HTML 模板（`templates/compact-report.html`）
- 跨平台 Python 转换脚本（`scripts/html2pdf.py`）
- 跨平台安装脚本：
  - `install/install.sh` — macOS / Linux / UOS（自动检测 brew/apt/dnf/yum/pacman）
  - `install/install.bat` — Windows cmd
  - `install/install.ps1` — Windows PowerShell
- 排版规则参考（`references/density-rules.md`）
- 跨平台字体配置（`references/platform-fonts.md`）
- 密度自检（每页 < 200 字符自动告警）
- 样例文件（`examples/集合竞价-2026-06-09.{html,pdf}`）

### Design Decisions
- **核心约束：技术不要留白** — 每页都要塞满有意义的内容，最后一页不能 < 半页
- **自然分页** — 不强制分页（除非封面/章首），让内容自然填满
- **密度黄金参数**：16mm 边距、9.2pt 正文、1.55 行高、表格 1.5mm padding
- **抗孤行 / 抗断页**：标题后不孤行、表格不跨页断

### Lessons Learned
- 第一版用 premium-a4-printable-pdfs 的强制分页 → 大量留白 → 被用户当场打回
- "premium 编辑感"和"不留白"在排版上是反方向 — 本 skill 选后者
