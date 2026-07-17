---
name: business-tracker
description: 制作业务推动表、客户跟进表、竞赛推动表。当用户需要：为一批经理（投资经理/财富经理/业务员）制作客户跟进系统、从数据源提取客户并按经理分配、生成母表（管理层汇总）和子表（客户明细）、设置完成率公式、制作业务竞赛追踪表、对已有子表做"优先级分批/二次分类"时，使用此 skill。触发词：业务推动表、业务跟进表、客户追踪表、母表子表、竞赛推动、经理客户分配、现有客户数、已联络客户数、完成率、优先级分类、P0/P1/P2/P3、开发潜力、熟悉度、二次分类、分批覆盖、先见哪批。
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

---

## Step 7：子表二次分类（优先级分批，P1/P2/P3）

**触发场景：** 子表已经发下去后，总监要求"先打哪一批"——业务员需要按熟悉度+开发潜力把名单切成 P1/P2/P3，每批先攻 25–30 人，总监陪访跟进。本步骤直接在**已存在的子表**上加列改造，不动原数据。

### 7.1 加列规则（紧跟在"客户号"之后插入 4 列）

| 列名 | 类型 | 取值 | 说明 |
|---|---|---|---|
| 熟悉度 | 人工录入（下拉） | 熟悉=1 / 不熟悉=0 | 业务员对该客户的熟悉程度 |
| 潜力度 | 人工录入（下拉） | 高=1 / 低=0 | 开发潜力的人工判断 |
| 开发潜力 | 公式 | 高 / 中 / 低 | 熟悉度+潜力度，2→高，1→中，0→低 |
| 优先级 | 公式 | P1 / P2 / P3 | 与开发潜力一一对应 |

### 7.2 评分口径（等权重相加）

- 1 + 1 = 2 → **高 / P1**（熟悉且高潜力，第一批先攻）
- 1 + 0 或 0 + 1 = 1 → **中 / P2**（第二批）
- 0 + 0 = 0 → **低 / P3**（兜底批次）
- 任一为空 → 留空，公式不强行判定

> **P0 不进公式**：留给总监手动覆写"本周必见 VIP"白名单。优先级列允许人工改写，配合深红色条件格式即可。

### 7.3 实施脚本（openpyxl 通用模板）

> 关键点：用 `insert_cols` 在客户号后插入，公式引用同行的熟悉度/潜力度单元格，下拉用 `DataValidation`，配色用 `CellIsRule`。另存为 `_v2.xlsx`，**绝不覆盖原件**。

```python
import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

SRC = '客户联络推进表（子表）.xlsx'
DST = '客户联络推进表（子表）_v2.xlsx'
TARGET_SHEETS = ['存量']  # 多张同结构表可一起处理

P0_FILL = PatternFill('solid', fgColor='C00000')   # 手动 VIP
P1_FILL = PatternFill('solid', fgColor='FFC7CE')   # 红
P2_FILL = PatternFill('solid', fgColor='FFEB9C')   # 黄
P3_FILL = PatternFill('solid', fgColor='D9D9D9')   # 灰
HIGH_FILL = PatternFill('solid', fgColor='63BE7B')
MID_FILL  = PatternFill('solid', fgColor='B7E1A1')
LOW_FILL  = PatternFill('solid', fgColor='D9D9D9')
HEADER_FILL = PatternFill('solid', fgColor='4F81BD')
HEADER_FONT = Font(bold=True, color='FFFFFF')

def find_col(ws, name):
    for c in range(1, ws.max_column + 1):
        if ws.cell(row=1, column=c).value == name:
            return c
    raise ValueError(f'Column {name} not found in {ws.title}')

def enhance(ws):
    last_row = ws.max_row
    insert_at = find_col(ws, '客户号') + 1
    ws.insert_cols(insert_at, amount=4)

    for i, h in enumerate(['熟悉度', '潜力度', '开发潜力', '优先级']):
        cell = ws.cell(row=1, column=insert_at + i, value=h)
        cell.fill = HEADER_FILL; cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal='center')

    fam_col, pot_col, dev_col, pri_col = insert_at, insert_at+1, insert_at+2, insert_at+3
    fam_L, pot_L = get_column_letter(fam_col), get_column_letter(pot_col)
    dev_L, pri_L = get_column_letter(dev_col), get_column_letter(pri_col)

    for r in range(2, last_row + 1):
        f, p = f'{fam_L}{r}', f'{pot_L}{r}'
        ws.cell(row=r, column=dev_col).value = (
            f'=IF(OR({f}="",{p}=""),"",IF({f}+{p}=2,"高",IF({f}+{p}=1,"中","低")))'
        )
        ws.cell(row=r, column=pri_col).value = (
            f'=IF(OR({f}="",{p}=""),"",IF({f}+{p}=2,"P1",IF({f}+{p}=1,"P2","P3")))'
        )
        for c in (fam_col, pot_col, dev_col, pri_col):
            ws.cell(row=r, column=c).alignment = Alignment(horizontal='center')

    dv = DataValidation(type='list', formula1='"0,1"', allow_blank=True)
    dv.error = '只能填 0 或 1'; dv.errorTitle = '取值范围'
    ws.add_data_validation(dv)
    dv.add(f'{fam_L}2:{fam_L}{last_row}')
    dv.add(f'{pot_L}2:{pot_L}{last_row}')

    pri_range = f'{pri_L}2:{pri_L}{last_row}'
    for val, fill in [('P0',P0_FILL),('P1',P1_FILL),('P2',P2_FILL),('P3',P3_FILL)]:
        ws.conditional_formatting.add(pri_range,
            CellIsRule(operator='equal', formula=[f'"{val}"'], fill=fill))

    dev_range = f'{dev_L}2:{dev_L}{last_row}'
    for val, fill in [('高',HIGH_FILL),('中',MID_FILL),('低',LOW_FILL)]:
        ws.conditional_formatting.add(dev_range,
            CellIsRule(operator='equal', formula=[f'"{val}"'], fill=fill))

    for c in (fam_col, pot_col, dev_col, pri_col):
        ws.column_dimensions[get_column_letter(c)].width = 10
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f'A1:{get_column_letter(ws.max_column)}{last_row}'

wb = openpyxl.load_workbook(SRC)
for s in TARGET_SHEETS:
    enhance(wb[s])
wb.save(DST)
```

### 7.4 实施前必问

1. **改哪几张工作表**？子表往往有"存量""存量（历史）""新增"等多个 sheet，确认哪些需要改造、哪些原样保留（如"新增"通常是统计表，不动）。
2. **是否启用 P0**？默认不进公式，留人工覆写；若用户要规则化（比如"AUM > 500万自动 P0"），追加 IF 分支。
3. **另存还是覆盖**？默认 `_v2.xlsx` 另存，除非用户明确说覆盖。

### 7.5 验证清单（必做）

1. 列顺序：经理姓名 … 客户号 / **熟悉度 / 潜力度 / 开发潜力 / 优先级** / 是否已联络 …
2. 任挑一行人工填值反查：
   - 1/1 → 高 / P1
   - 1/0 → 中 / P2
   - 0/1 → 中 / P2
   - 0/0 → 低 / P3
   - 任一空 → 两列均留空
3. 优先级列勾选筛选 P1 → 应能筛出对应行
4. 条件格式着色生效（P1 红 / P2 黄 / P3 灰；高深绿 / 中浅绿 / 低灰）
5. 原数据行数、客户号未被改动（用 `wb_old.max_row == wb_new.max_row` 比对）

### 7.6 交付话术（给业务员/总监）

> 子表已加 4 列：**熟悉度、潜力度、开发潜力、优先级**。业务员只需在熟悉度/潜力度填 0 或 1，后两列自动出结果。点表头筛选按钮勾选"P1"，导出本周要见的 25–30 人小名单，总监按 P1 → P2 → P3 逐批陪访。VIP 客户总监可直接把优先级改成 P0（深红色）。
