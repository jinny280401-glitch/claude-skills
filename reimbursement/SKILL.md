---
name: reimbursement
description: 报销助手。从餐饮消费截图和发票 PDF 提取数据，核对商户名称和金额，自动填写接待审批单（Word 文档）上半部分，并保存历史记录。触发词：报销、接待审批单、填报销单、发票识别、餐饮报销、商务接待、费用报销。当用户提到"帮我报销"、"填接待审批单"、"处理发票"时使用此 skill。
---

# 报销助手

自动化处理餐饮报销流程：提取数据 → 核对验证 → 填充审批单上半部分 → 保存历史记录。

## 使用场景

用户说：
- "帮我报销，截图是 xxx.jpg，发票是 xxx.pdf"
- "填一份接待审批单，接待对象是张三等4人"
- "处理这张发票，事由是维护客户"

## 工作流程

### Step 1：收集文件

询问用户（如果未提供）：
1. **消费截图路径**：餐饮小票或支付截图
2. **发票 PDF 路径**：电子发票文件

### Step 2：提取数据

使用 Read 工具读取文件：

```
1. Read 消费截图 → 提取：商户名、消费金额
2. Read 发票 PDF → 提取：开票商户名、金额、税额、价税合计
```

提取后展示给用户确认：
```
消费截图识别结果：
- 商户：XX餐厅
- 金额：532.32 元

发票识别结果：
- 开票商户：XX市XX区XX餐饮管理有限公司
- 金额：502.19 元
- 税额：30.13 元
- 价税合计：532.32 元
```

### Step 3：数据验证

调用 `scripts/validate.py`：

```python
# 商户名称核对
merchant_check = validate_merchant_match(
    receipt_merchant="XX餐厅",
    invoice_merchant="XX市XX区XX餐饮管理有限公司"
)

# 金额一致性
amount_check = validate_amount(
    receipt_amount=532.32,
    invoice_total=532.32
)
```

展示验证结果：
```
✓ 商户名称匹配（相似度 75%）
✓ 金额一致
```

如果有问题：
```
⚠️ 商户名称不匹配（相似度 45%）
  - 消费截图：海底捞
  - 发票开票：XX市XX区XX餐饮管理有限公司
  
是否继续？[y/N]
```

### Step 4：收集接待信息

询问用户补充信息：
1. **接待对象**（如 "张三等"）
2. **接待人数**
3. **陪餐人数**
4. **接待时间**（默认今天）
5. **事由**（拓展客户/维护客户/商业合作/其他）

计算并展示：
- 人均费用 = 总金额 / (接待人数 + 陪餐人数)
- 预算总额（建议向上取整到百位）

验证人均费用合规性：
```
✓ 人均费用合规：88.72 元/人（限额 600 元）
```

或警告：
```
⚠️ 人均费用超标：650 元/人（限额 600 元，超出 50 元）
```

### Step 5：填充审批单

调用 `scripts/fill_approval_form.py`：

```bash
python3 ~/.claude/skills/reimbursement/scripts/fill_approval_form.py \
  "~/Documents/报销/接待审批单（空）.docx" \
  "~/Documents/报销/20260506接待审批单（532.32元）.docx" \
  '{
    "send_date": "2026.5.6",
    "reception_object": "张三等",
    "reception_date": "2026.5.6",
    "reason": "维护客户",
    "reception_count": 4,
    "accompany_count": 2,
    "per_capita": 100,
    "budget_total": 600
  }'
```

**注意**：只填写上半部分（事前审批），下半部分（事后清单）需要手写。

### Step 6：保存历史记录

调用 `scripts/history.py`：

```bash
python3 ~/.claude/skills/reimbursement/scripts/history.py add '{
  "date": "2026.5.6",
  "reception_object": "张三等",
  "merchant": "XX市XX区XX餐饮管理有限公司",
  "amount": 532.32,
  "reception_count": 4,
  "accompany_count": 2,
  "reason": "维护客户",
  "receipt_image": "/path/to/receipt.jpg",
  "invoice_pdf": "/path/to/invoice.pdf",
  "approval_form": "~/Documents/报销/20260506接待审批单（532.32元）.docx"
}'
```

### Step 7：交付

告知用户：
```
✓ 审批单已生成：
  ~/Documents/报销/20260506接待审批单（532.32元）.docx

✓ 历史记录已保存（ID: 5）

已填充字段（上半部分 - 事前审批）：
- 送审时间：2026.5.6
- 接待对象：张三等
- 接待时间：2026.5.6
- 事由：☑维护客户
- 预算：接待4人，陪餐2人，人均100元，总额600元

下半部分（事后清单）需要手写：
- 商务宴请费用明细
- 承办部门经办人签名
- 承办部门意见
- 审批人意见
```

## 历史记录管理

### 查询最近的报销记录

```bash
python3 ~/.claude/skills/reimbursement/scripts/history.py list 10
```

### 搜索报销记录

```bash
python3 ~/.claude/skills/reimbursement/scripts/history.py search "张三"
```

### 获取指定记录

```bash
python3 ~/.claude/skills/reimbursement/scripts/history.py get 5
```

历史记录保存在：`~/.claude/reimbursement_history.json`

## 常见问题

| 问题 | 处理方式 |
|------|----------|
| Claude 无法识别截图 | 提示用户提供更清晰的图片，或手动输入商户名和金额 |
| 商户名称不匹配 | 展示相似度，让用户决定是否继续 |
| 金额不一致 | 高亮差异，提示用户核对 |
| 人均费用超标 | 红色警告，提示违反规定 |

## 配置

编辑 `~/.claude/skills/reimbursement/references/approval_form_mapping.json`：

```json
{
  "template_path": "~/Documents/报销/接待审批单（空）.docx",
  "output_dir": "~/Documents/报销/",
  "validation_rules": {
    "per_capita_limit": 600,
    "merchant_similarity_threshold": 0.6,
    "amount_tolerance": 0.5
  }
}
```
