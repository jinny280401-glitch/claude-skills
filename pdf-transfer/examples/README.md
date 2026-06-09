# 样例

两个真实样例展示本 skill 最常用的两个模板：

## 1. Morning Brief（极简，1 页）

- 文件：`集合竞价-Morning-Brief-2026-06-09.html`
- 用途：盘前/开盘定调,30 秒扫一眼就能决策
- 内容：4 个核心数字 + 3 条主线 vs 3 条风险 + 5 只重点观察

## 2. 集合竞价报告（详细，3-4 页）

- 文件：`集合竞价-报告-2026-06-09.html`
- 用途：详细盘面分析,业务研究
- 内容：5 个核心数字 + 3 条核心主线 + 连板梯队 + 赚钱效应 + 人气 + 异动 + 综合判断 + 重点观察

## 生成 PDF

```bash
python3 pdf-transfer/scripts/html2pdf.py \
    pdf-transfer/examples/集合竞价-Morning-Brief-2026-06-09.html \
    pdf-transfer/examples/集合竞价-Morning-Brief-2026-06-09.pdf

python3 pdf-transfer/scripts/html2pdf.py \
    pdf-transfer/examples/集合竞价-报告-2026-06-09.html \
    pdf-transfer/examples/集合竞价-报告-2026-06-09.pdf
```

## 设计原则

两个模板都遵循 **"技术不要留白"** 核心约束,且**不写工程化内容**（字体、工具、数据源、错误信息、缺失模块等）—— 这些对盘前决策是噪音,只保留业务结论和投资观点。
