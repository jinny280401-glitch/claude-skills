# Reimbursement Skill

Claude Code skill 用于自动化餐饮报销流程：从消费截图和发票 PDF 提取数据 → 核对商户和金额 → 自动填写接待审批单上半部分 → 保存历史记录。

## 功能

- **数据提取**：利用 Claude 视觉能力从消费截图和发票 PDF 提取商户名、金额
- **数据校验**：商户名模糊匹配（去除常见后缀后比对相似度）、金额一致性、人均费用合规性
- **自动填表**：使用 python-docx 填写 Word 审批单上半部分（事前审批），下半部分留作手写
- **历史记录**：每条报销保存到本地 JSON，便于后续转账追踪和查询

## 安装

将 `reimbursement/` 整个目录复制到 `~/.claude/skills/`：

```bash
cp -r reimbursement ~/.claude/skills/
chmod +x ~/.claude/skills/reimbursement/scripts/*.py
```

依赖：`python-docx`

```bash
pip install python-docx
```

可选：安装 `/baoxiao` slash command，用一条命令快速启动报销流程：

```bash
mkdir -p ~/.claude/commands
cp reimbursement/commands/baoxiao.md ~/.claude/commands/
```

安装后在 Claude Code 里输入 `/baoxiao` 即可。

## 配置

编辑 `references/approval_form_mapping.json`，把 `template_path` 改成你自己的接待审批单模板路径。

字段映射也可以按需修改（不同公司模板的表格行列索引可能不同）。

## 使用

向 Claude Code 说：

> 帮我报销，截图是 /path/to/receipt.jpg，发票是 /path/to/invoice.pdf

Claude 会按以下流程处理：

1. 读取消费截图和发票 PDF，提取商户名和金额
2. 展示提取结果，校验商户名和金额是否一致
3. 询问接待对象、人数、事由
4. 计算人均费用并校验合规性（默认上限 600 元/人）
5. 生成已填写的 Word 文档
6. 保存历史记录到 `~/.claude/reimbursement_history.json`

## 历史记录查询

```bash
# 查看最近 10 条
python3 ~/.claude/skills/reimbursement/scripts/history.py list 10

# 按接待对象/商户搜索
python3 ~/.claude/skills/reimbursement/scripts/history.py search "张三"

# 按 ID 查询
python3 ~/.claude/skills/reimbursement/scripts/history.py get 5
```

## 文件结构

```
reimbursement/
├── SKILL.md                              # Skill 定义和工作流说明
├── scripts/
│   ├── fill_approval_form.py             # 填写 Word 审批单
│   ├── validate.py                       # 商户/金额/人均费用校验
│   └── history.py                        # 本地 JSON 历史记录管理
└── references/
    └── approval_form_mapping.json        # 模板路径和字段映射配置
```

## 注意事项

- 只填写审批单**上半部分（事前审批）**，下半部分（事后清单、签字）需手写
- 模板的表格行列索引写在配置文件里，不同公司的模板需要重新映射
- Claude 视觉识别准确率不是 100%，关键金额请人工核对一遍
- 历史记录是明文 JSON，包含商户、金额等信息，注意访问权限
