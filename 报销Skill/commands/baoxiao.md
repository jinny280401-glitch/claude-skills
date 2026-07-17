---
description: 启动报销助手 - 从消费截图和发票 PDF 自动填写接待审批单
argument-hint: [截图路径] [发票路径]
allowed-tools: [Read, Bash, Skill]
---

# 报销助手

启动 reimbursement skill，处理一笔餐饮报销。

## 用户输入

$ARGUMENTS

## 工作流程

1. **检查输入**：用户可能在 $ARGUMENTS 中提供了截图和发票路径，也可能没提供
   - 如果路径已提供：直接进入 Step 2
   - 如果未提供：询问用户消费截图和发票 PDF 的路径

2. **调用 reimbursement skill** 执行完整流程：
   - 用 Read 工具读取消费截图，提取商户名和金额
   - 用 Read 工具读取发票 PDF，提取开票商户名、金额、税额、价税合计
   - 展示提取结果给用户确认
   - 调用 `~/.claude/skills/reimbursement/scripts/validate.py` 验证商户名和金额
   - 询问接待对象、人数、事由、接待时间
   - 计算人均费用并校验合规性
   - 调用 `~/.claude/skills/reimbursement/scripts/fill_approval_form.py` 生成 Word 审批单（只填上半部分）
   - 调用 `~/.claude/skills/reimbursement/scripts/history.py add` 保存历史记录

3. **交付结果**：告知用户生成的 Word 文件路径和历史记录 ID

## 参考

详细工作流见 `~/.claude/skills/reimbursement/SKILL.md`。
