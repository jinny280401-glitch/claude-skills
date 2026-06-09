# Claude Skills 集合

可复用的 Claude Code 工作流自动化 Skills。

## Skills 列表

### business-tracker

**功能：** 制作业务推动表、客户跟进表、竞赛推动表

**使用场景：**
- 为一批经理（投资经理/财富经理/业务员）制作客户跟进系统
- 从数据源提取客户并按经理分配
- 生成母表（管理层汇总）和子表（客户明细）
- 设置完成率公式

**触发词：** 业务推动表、业务跟进表、客户追踪表、母表子表、竞赛推动

**输出：**
- 子表A：现有客户跟进（经理姓名、工号、客户姓名、客户号、联络状态等）
- 子表B：新客户成果（经理姓名、工号、客户姓名、成果类型、日期、备注）
- 母表：管理层汇总（投资经理、完成率、已联络客户数、现有客户数、折抵项）

**示例：**
```
用户：帮我做一个业务推动表
Claude：[触发 business-tracker skill，按流程收集需求并生成表格]
```

### pdf-transfer

**功能：** 把结构化文本/数据/Word-like 内容转成 A4 PDF，核心约束是"技术不要留白"

**使用场景：**
- 报告型 PDF（早盘集合竞价日报、研究报告、内参）
- 表格密集型 PDF（数据清单、对比表、矩阵）
- Word-like 文档（合同、纪要、SOP、模板）
- 任何需要"留白少、专业感"的 A4 输出

**触发词：** 做成 PDF、导出 PDF、排版一下、Word 转 PDF、留白太多、压紧一点、premium A4 风格、PDF 排版

**输出：**
- A4 PDF 文件（默认 weasyprint 渲染，备选 headless Chrome）
- 自动密度自检（每页 < 200 字符告警）
- 自动打开 PDF（macOS / Linux / Windows 全平台）

**支持平台：** macOS / Linux / 统信 UOS / Windows

**包含 3 个模板**（`pdf-transfer/templates/`）：
- `compact-report.html` — 通用报告型（封面 + 多章）
- `auction-morning-brief.html` — 集合竞价 Morning Brief（1 页极简定调）
- `auction-report.html` — 集合竞价详细报告（3-4 页业务研究）

**示例：**
```
用户：把这份集合竞价分析报告做成 PDF，要紧凑不留白
Claude：[触发 pdf-transfer skill，套用 auction-morning-brief.html 或 auction-report.html，导出 PDF 并自检密度]
```

## 安装

将对应文件/目录复制到 `~/.claude/skills/` 目录：

```bash
# 单文件 skill
cp business-tracker.md ~/.claude/skills/

# 多文件 skill (整个子目录)
cp -R pdf-transfer ~/.claude/skills/

# 或从 GitHub clone
git clone https://github.com/jinny280401-glitch/claude-skills.git
cp -R claude-skills/pdf-transfer ~/.claude/skills/
```

## 使用

在 Claude Code 中直接说出触发词，skill 会自动激活。

## 贡献

欢迎提交新的 skills 或改进现有 skills。

## License

MIT
