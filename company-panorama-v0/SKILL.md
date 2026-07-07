---
name: company-panorama-v0
description: Generate a 3-minute company visit preparation card for sales/research/risk teams. Uses Choice Miaoxiang API with Trust Gate filtering. Not for due diligence or investment advice.
---

# Company Panorama v0: 3分钟生成客户拜访准备卡

## Overview

为销售、投研、风控团队在客户拜访前快速建立公司背景认知，生成一页拜访准备卡。

**不是：** 完整尽调、投资建议、估值/评级/买卖建议

**是：** 背景准备、风险信号识别、人工核查问题清单

## When to Use

触发关键词：
- 公司背景调查 / 客户拜访准备 / 公司扫描
- 生成拜访卡 / 公司速查 / 尽调前准备

触发场景：
- 销售团队拜访前准备
- 投研团队初步扫描
- 风控团队背景核查
- 商务合作前背景了解

## 前置要求

### 环境变量

```bash
export EM_API_KEY="<your_key_here>"
```

**安全规则：**
- API key 只进环境变量，不进日志、不进 Prompt、不回显
- 不写入任何文件
- 不在 Engram 或其他存储中记录
- 显示时只用脱敏格式：em_***6a7

### Choice API 能力映射

```yaml
基本面研究能力: 公司资料、公告、年报、财务字段、股东结构
资讯与事件能力: 新闻、舆情、热点事件、公告事件
研究工具能力: 搜索、筛选、结构化提取、对比
宏观与行业能力: 行业背景、产业链、周期语境
市场数据能力: 仅用于上市公司识别和背景，不生成交易观点
跨资产筛选能力: v0 可暂不启用；只在发行人/债券/主体识别时调用
```

## 输出结构

### 1. 一页摘要

- 公司定位
- 主营业务
- 关键人物（带证据等级）
- 核心产品/服务
- 最近动态（带来源等级）

### 2. 风险雷达

5 类风险信号（不作最终结论）：
- 工商异常
- 舆情风险
- 诉讼风险
- 股权/控制权风险
- 经营波动风险

信号状态：
- `signal_present` — 检测到信号，需人工核查
- `signal_absent` — 未检测到信号
- `unknown` — 数据不足
- `requires_manual_check` — 必须人工确认

### 3. 证据等级表

```
High:   官方公告、工商、年报、监管文件
Medium: 主流媒体、券商研报、招投标、招聘、公开业务资料
Low:    自媒体、二手转述、估算信息
```

### 4. 不可推导边界

必须明确声明：
- 未取得审计财报
- 媒体估算不等于事实
- 非上市公司收入/利润不可确认
- 本报告不构成投资建议
- 风险信号不等于风险事实

### 5. 人工核查问题清单

输出 3-5 个拜访问题：
- 请确认当前主营收入来源
- 是否存在大客户集中
- 最近融资或扩产进度如何
- 是否有未披露诉讼、担保或关联交易风险
- 当前主要合作方和销售区域是什么

## 执行流程

### Phase 1: Resolve Company

```python
# 避免同名公司误配
resolve_company(company_name, company_alias=[], entity_type="unknown")
→ {
    "resolved_name": "宁德时代新能源科技股份有限公司",
    "stock_code": "300750.SZ",
    "entity_type": "listed",
    "confidence": 0.95
  }
```

### Phase 2: Collect Evidence

从 Choice API 或 Fallback 源采集：
- 公司基本资料
- 公告与年报
- 新闻与舆情
- 行业背景
- 股东结构（上市公司）

### Phase 3: Trust Gate Filter

**HARD GATE：Trust Gate 必须在 Prompt 前**

```python
raw_evidence[] → trust_gate_filter() → curated_evidence[]
```

必备字段：
- `source_url`
- `source_title`
- `source_type`
- `publish_date`
- `extracted_claim`
- `company_match_confidence`

证据等级规则：

```yaml
source_rank:
  High:
    - 官方公告/年报/招股书/监管披露/工商登记/法院或仲裁官方文书
  Medium:
    - 主流财经媒体/券商研报/招投标/招聘/公司官网普通新闻/公开业务资料
  Low:
    - 自媒体/论坛/二手转述/未标注来源榜单/估算数据

allowed_use:
  High: 可作为事实，但必须带来源
  Medium: 可作为背景或"据公开资料显示"，不得作最终结论
  Low: 只能作为待核查线索，不得写成事实

blocked_fields:
  - valuation
  - rating
  - buy_sell_hold
  - position_sizing
  - private_company_revenue_profit_without_audit
  - definitive_legal_liability
  - definitive_credit_conclusion
  - due_diligence_replacement_claim

private_company_financial_rule:
  default: UNKNOWN
  exception: 官方或审计来源
```

### Phase 4: LLM Generate Visit Card

将过滤后的证据送入 LLM，生成拜访准备卡。

Prompt 必须包含：
- Trust Gate 过滤后的证据
- 证据等级标注
- 禁用表达清单
- 输出结构模板

### Phase 5: Post-QC Blocked Claim Scan

扫描输出，检测禁用表达：
- 估值/评级/买卖/仓位建议
- "该公司值得投资/不值得投资"
- "本报告可替代尽调"
- 非上市公司财务数据作为事实（无官方/审计来源）
- 媒体估算作为确认事实
- 风险结论（"该公司无风险"/"存在重大风险"）

## Blocked Claims List

```
- "该公司值得投资/不值得投资"
- "给予买入/卖出/持有评级"
- "目标价/估值区间/合理市值"
- "建议加仓/减仓/配置比例"
- "公司无诉讼风险/无舆情风险/无经营风险"
- "非上市公司收入、利润、估值已确认"（除非来自官方或审计来源）
- "媒体估算显示即为事实"
- "本卡片可替代尽调/审计/法务核查/投委会材料"
```

## Demo Sample

**测试公司：** 宁德时代新能源科技股份有限公司  
**截至日期：** 2026-07-07

### 一页摘要

- **公司定位：** 公开年报摘要将其表述为新能源科技公司，主要围绕动力电池、储能电池等业务展开。证据等级 High。
- **主营业务：** 动力电池、储能电池的研发、生产、销售。证据等级 High。
- **关键人物：** 曾毓群，董事长、执行董事兼总经理。证据等级 High。
- **核心产品/服务：** 动力电池、储能电池、电池材料/回收、换电及部分新应用场景解决方案。证据等级 High/Medium。
- **最近动态：** 2026-07-06 公司官网发布"天行Ⅱ轻商超充版电池"相关新闻；2026-06-26 东方财富公告列表显示公司有绿色科技创新债券发行完成、套期保值/衍生品相关公告。证据等级 High/Medium。

### 风险雷达

- **工商异常：** UNKNOWN，v0 样例未接入工商官方源，需人工核查。
- **舆情风险：** requires_manual_check，近期新闻较多，需区分公司官网新闻、主流媒体报道与市场传闻。
- **诉讼风险：** UNKNOWN，需接法院/仲裁/公告源确认。
- **股权/控制权风险：** requires_manual_check，上市公司股东结构可查，但本卡不作控制权稳定性结论。
- **经营波动风险：** signal_present，公司公告涉及套期保值/衍生品及债券融资事项，可作为拜访前核查信号，不等于经营风险事实。

### 不可推导边界

- 未取得审计财报时，不确认未经审计财务口径。
- 媒体估算不等于事实。
- 非上市公司收入/利润默认 UNKNOWN。
- 本报告不构成投资建议。
- 风险信号不等于风险事实。

### 人工核查问题

- 请确认当前主营收入来源及不同业务线占比。
- 是否存在大客户集中或区域集中情况？
- 最近融资、扩产或海外布局进度如何？
- 是否存在未披露诉讼、担保或关联交易风险？
- 当前主要合作方和销售区域是什么？

## Next Smoke Checklist

- [ ] API key 只进环境变量，不进日志、不进 Prompt
- [ ] 先跑 `resolve_company`，避免同名公司误配
- [ ] `raw_evidence` 必须经过 `source_rank / allowed_use / blocked_fields`
- [ ] Low evidence 只能进"待核查线索"
- [ ] 非上市公司财务字段默认 `UNKNOWN`
- [ ] Post-QC 扫描估值、评级、买卖、仓位、尽调替代等禁用表达
- [ ] 样例公司跑通后，再测一家非上市公司和一家发债主体

## 禁止

- ❌ 不接生产
- ❌ 不写真实投资结论
- ❌ 不宣传完整尽调
- ❌ 不把媒体估算当事实
- ❌ 不绕过 Trust Gate

## 输出物

生成文件：`{company_name}_visit_card_{YYYYMMDD}.json`

包含：
- 一页摘要
- 风险雷达
- 证据等级表
- 不可推导边界
- 人工核查问题清单
- 禁用表达检测结果
- 免责声明

## 参考来源

- [Choice量化接口手册](https://quantapi.eastmoney.com/Manual?from=web)
- [Choice App介绍](https://apps.apple.com/tt/app/choice%E6%95%B0%E6%8D%AE-%E4%B8%8B%E4%B8%80%E4%BB%A3%E6%99%BA%E8%83%BD%E9%87%91%E8%9E%8D%E7%BB%88%E7%AB%AF/id838045890)
- [Choice终端数据库介绍](https://library.gufe.edu.cn/info/1023/3535.htm)

## 历史执行记录

**2026-07-07 初始设计：**
- 完成 Skill 规格设计
- 定义 Trust Gate 架构
- 设置证据等级规则
- 创建 Blocked Claims List
- Demo Sample: 宁德时代
