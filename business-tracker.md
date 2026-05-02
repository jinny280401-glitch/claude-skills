---
name: business-tracker
description: 制作业务推动表、客户跟进表、竞赛推动表。当用户需要：为一批经理（投资经理/财富经理/业务员）制作客户跟进系统、从数据源提取客户并按经理分配、生成母表（管理层汇总）和子表（客户明细）、设置完成率公式、制作业务竞赛追踪表时，使用此 skill。触发词：业务推动表、业务跟进表、客户追踪表、母表子表、竞赛推动、经理客户分配、现有客户数、已联络客户数、完成率。
---

# 业务推动表制作

为一批经理从数据源提取客户，生成母表（管理层汇总）+ 子表A（现有客户跟进）+ 子表B（新客户成果），并写入完成率公式。

## Step 1：收集需求

开始前确认以下信息（未提供的逐一询问）：

1. **经理名单**：姓名 + 工号，按指定顺序排列
2. **数据源文件**：路径，以及哪个字段对应"经理姓名"（常见：营销关系、服务关系）
3. **模板文件**：子表和母表是否有现成模板（有则读取表头结构）
4. **完成率公式**：用户提供，或使用默认公式
5. **折抵项**：已邀约到现场数、新增开户数、高净值面访数等是否需要拆分到子表B（新客户成果）

## Step 2：提取客户数据

```python
import pandas as pd
import openpyxl

# 读取数据源
df = pd.read_excel('数据源路径.xlsx')

# 目标经理名单（从用户输入构建）
managers = [
    ('经理姓名1', '工号1'),
    ('经理姓名2', '工号2'),
    # ...
]
manager_names = [m[0] for m in managers]

# 按营销关系字段筛选
# 注意：字段名可能是"营销关系"或"服务关系"，根据实际情况调整
target_col = '营销关系'
filtered = df[df[target_col].isin(manager_names)][['客户姓名', '客户号', target_col]]
filtered = filtered.rename(columns={target_col: '经理姓名'})

# 统计并报告
for name, emp_id in managers:
    count = len(filtered[filtered['经理姓名'] == name])
    status = f"{count}个客户" if count > 0 else "⚠️ 0个客户（数据源中未找到）"
    print(f"  {name}({emp_id}): {status}")
```

**数据清洗检查：**
- 经理姓名是否有多余空格（用 `str.strip()` 处理）
- 客户号是否为科学计数法（转为字符串：`str(int(客户号))`）
- 是否有重复客户号

## Step 3：生成子表A（现有客户跟进）

**列结构：** 经理姓名 | 工号 | 客户姓名 | 客户号 | 是否已联络 | 联络方式 | 沟通时间 | 沟通情况/成果

```python
wb = openpyxl.load_workbook('子表模板.xlsx')  # 或新建 Workbook()
ws = wb.active

# 表头（如模板已有则跳过）
headers = ['经理姓名', '工号', '客户姓名', '客户号', '是否已联络', '联络方式', '沟通时间', '沟通情况/成果']

# 按经理顺序写入数据
current_row = 3  # 根据模板调整起始行
for manager_name, emp_id in managers:
    customers = filtered[filtered['经理姓名'] == manager_name]
    for _, row in customers.iterrows():
        ws.cell(row=current_row, column=1, value=manager_name)
        ws.cell(row=current_row, column=2, value=emp_id)
        ws.cell(row=current_row, column=3, value=row['客户姓名'])
        ws.cell(row=current_row, column=4, value=str(int(row['客户号'])))
        current_row += 1

wb.save('子表A_现有客户跟进.xlsx')
```

## Step 4：生成子表B（新客户成果，可选）

当折抵项（邀约到现场、新增开户、高净值面访）可能来自**不在现有客户名单内的新客户**时，需要拆分到子表B。

**列结构：** 经理姓名 | 工号 | 客户姓名 | 成果类型 | 日期 | 备注

成果类型选项：`邀约到现场` / `新增开户` / `高净值面访`

```python
wb_b = openpyxl.Workbook()
ws_b = wb_b.active
ws_b.cell(row=1, column=1, value='子表B_新客户成果')
headers_b = ['经理姓名', '工号', '客户姓名', '成果类型', '日期', '备注']
for col, h in enumerate(headers_b, start=1):
    ws_b.cell(row=2, column=col, value=h)
wb_b.save('子表B_新客户成果.xlsx')
```

## Step 5：生成母表

**列结构：** 投资经理 | 完成率 | 已联络客户数 | 现有客户数 | 已邀约到现场数 | 新增开户数 | 高净值面访数

```python
wb_m = openpyxl.load_workbook('母表模板.xlsx')
ws_m = wb_m.active

# 统计每位经理的客户数
customer_counts = filtered.groupby('经理姓名').size().to_dict()

for idx, (name, emp_id) in enumerate(managers, start=2):
    count = customer_counts.get(name, 0)
    ws_m.cell(row=idx, column=1, value=f'{name}({emp_id})')  # 投资经理
    ws_m.cell(row=idx, column=4, value=count)                 # 现有客户数（D列）
    # 完成率公式（B列）
    ws_m.cell(row=idx, column=2, value=f'=(D{idx}-C{idx}-(E{idx}*3)-(F{idx}*3)-(G{idx}*3))/D{idx}')

wb_m.save('母表.xlsx')
```

**默认完成率公式：**
```
=(现有客户数 - 已联络客户数 - (已邀约到现场数*3) - (新增开户数*3) - (高净值面访数*3)) / 现有客户数
```
> 折抵逻辑：每个高质量成果（邀约/开户/面访）可抵扣3个未联络客户。用户可提供自定义公式。

## Step 6：交付与导入说明

生成文件后告知用户：
1. **子表A** → 导入企业微信/腾讯表格，业务员填写联络情况
2. **子表B** → 导入企业微信/腾讯表格，业务员手动添加新客户成果
3. **功能表**（用户在表格系统内配置）→ 汇总子表A的已联络数 + 子表B的折抵项计数
4. **母表** → 从功能表获取数据，完成率自动计算

## 常见问题

| 问题 | 处理方式 |
|------|----------|
| 某经理在数据源中0个客户 | 报告给用户，确认是否手动补充或跳过 |
| 经理姓名有空格/全角字符 | 用 `str.strip()` 清洗后再匹配 |
| 客户号显示为科学计数法 | 转为字符串：`str(int(float(x)))` |
| 数据源字段名不是"营销关系" | 询问用户确认字段名，或列出所有列名让用户选择 |
| 一个客户对应多个经理 | 询问用户：以营销关系为主，还是服务关系为主 |
