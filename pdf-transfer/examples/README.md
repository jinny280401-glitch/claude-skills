# 样例

本 skill 的两个真实样例：

## ⚠ 简讯样例已 deprecated

`集合竞价-Morning-Brief-2026-06-09.html` 仅作历史参考,本 skill **不再推荐**走完整流程出简讯 PDF。
简讯场景请直接 chat 输出 markdown 表格(无 PDF 渲染,成本低 7-13 倍)。

详细报告 (`集合竞价-报告-2026-06-09.html`) 仍是本 skill 主推用法。

## 1. 集合竞价详细报告 (3-4 页)

- 文件: `集合竞价-报告-2026-06-09.html`
- 用途: 详细盘面分析 / 业务研究
- 内容: 5 个核心数字 + 3 条核心主线 + 连板梯队 + 赚钱效应 + 人气 + 异动 + 综合判断 + 重点观察

## 2. Morning Brief (1 页, deprecated)

- 文件: `集合竞价-Morning-Brief-2026-06-09.html`
- 状态: **deprecated — 不推荐再走 skill 流程**
- 历史用途: 盘前/开盘定调
- 推荐替代: chat 内联 markdown 表格

## 生成 PDF

```bash
# 推荐:详细报告
python3 pdf-transfer/scripts/html2pdf.py \
    pdf-transfer/examples/集合竞价-报告-2026-06-09.html \
    pdf-transfer/examples/集合竞价-报告-2026-06-09.pdf

# deprecated:简讯(不推荐)
python3 pdf-transfer/scripts/html2pdf.py \
    pdf-transfer/examples/集合竞价-Morning-Brief-2026-06-09.html \
    pdf-transfer/examples/集合竞价-Morning-Brief-2026-06-09.pdf
```

## 设计原则

- 严格遵守 **"技术不要留白"** 核心约束
- **不写工程化内容**(字体、工具、数据源、错误、缺失模块) — 对盘前决策是噪音
- 只保留业务结论和投资观点
