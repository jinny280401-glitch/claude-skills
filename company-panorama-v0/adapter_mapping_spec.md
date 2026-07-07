# Choice/MX Adapter Mapping Spec

**Status:** PHASE 2 + COMPANY ID COMPLETE — Real Evidence Integration NOT AUTHORIZED
**Date:** 2026-07-08
**Scope:** Announcements + News adapter 设计完成，Company Identification adapter 设计+Smoke 完成

---

## 最终状态（给 CC 的回执）

```
Choice/MX Adapter Mapping 当前状态
──────────────────────────────────────────────────────
Announcements + News Mapping:     DESIGN COMPLETE ✓
Company Identification:           DESIGN COMPLETE / SMOKE PASS ✓
Company Match Filter:             RESOLVED (3-tier routing with position anchor)
Real Evidence Integration:        NOT AUTHORIZED
Production Ready:                 NO
──────────────────────────────────────────────────────
Freeze Rule: No notice/news record may enter Real
Evidence Integration unless company_match_confidence
is present and above the accepted threshold.
```

### 已完成

1. ✅ 盘点 MX MCP 主体识别能力：mx_ashare_finance_data / mx_comprehensive_finance_data
2. ✅ Key-Value Format → company_name_normalized + stock_code + entity_type 提取
3. ✅ company_match_confidence 三级规则 (high 0.9+ / medium 0.5-0.9 / low <0.5)
4. ✅ Trust Gate 路由：eligible_fact_input / pending_manual_review / reject_before_trust_gate
5. ✅ 张冠李戴防护：`_title_starts_with_other_company()` 检测
6. ✅ 实测验证：恒翼能:宁德时代 → 正确识别为 OTHER company，confidence 0.30 → REJECT

### Blocker 状态

**Company Match Filter 已从 UNRESOLVED 升级为 RESOLVED**，但以下不变：

- Real Evidence Integration: NOT AUTHORIZED（需 notice/news + company_id 联调 Smoke）
- Production Ready: NO
- 字段映射完成 ≠ 可生产接入

---

## 前置事实（Phase 2 实测）

两个工具返回相同的表格结构：

```json
{
  "data": [
    {
      "sheetName": "...",
      "columns": ["标题", "摘要", "发布时间", "来源", "跳转链接"],
      "items": [
        ["标题文本", "摘要文本", "2026-07-07 23:21:00", "新浪网", "https://..."],
        ...
      ]
    }
  ]
}
```

实测返回：
- mx_finance_search_notice: 20 items（公告）
- mx_finance_search_news: 20 items（新闻）

---

## 1. Announcements Adapter

**Tool:** `mx_finance_search_notice`

### 列映射

| MX 列名 | 内部字段 | 说明 |
|---------|---------|------|
| 标题 | source_title | 公告标题 |
| 摘要 | extracted_claim | 摘要作为提取声明 |
| 发布时间 | publish_date | 格式 `YYYY-MM-DD HH:MM:SS` |
| 来源 | source_type | 公告来源 |
| 跳转链接 | source_url | 原文链接 |

### 固定字段

```yaml
evidence_level: High          # 公告默认 High（官方披露）
source_rank: High
allowed_use: "可作为事实，但必须带来源"
```

### 关键判断：evidence_level 不是无条件 High

⚠️ **根因问题**：`mx_finance_search_notice` 返回的"来源"字段实测出现「新浪网」等媒体源，不全是交易所/公司官方公告。

因此不能对整个 notice 工具无脑打 High。规则：

```yaml
announcement_level_rule:
  if 来源 in [交易所, 证监会, 公司公告, 巨潮, 官方]:
    evidence_level: High
  elif 来源 in [主流财经媒体]:
    evidence_level: Medium
  else:
    evidence_level: Low
```

**默认值 High 仅作为 notice 工具的起点，必须按"来源"字段二次降级。**

---

## 2. News Adapter

**Tool:** `mx_finance_search_news`

### 列映射

同 announcements（列结构相同）：

| MX 列名 | 内部字段 |
|---------|---------|
| 标题 | source_title |
| 摘要 | extracted_claim |
| 发布时间 | publish_date |
| 来源 | source_type |
| 跳转链接 | source_url |

### 证据分级（按来源）

```yaml
news_level_rule:
  High:
    - 官方/监管/交易所/证监会
  Medium:
    - 新华社/人民网/证券时报/中国证券报/上海证券报/第一财经/财新/东方财富
  Low:
    - 其他自媒体/未知来源/搜狐号/百家号/头条号
```

实测样本判级：
- "来源:新浪网" → Medium（主流媒体）
- "来源:搜狐" → Low（搜狐通常是自媒体聚合，标题含 `_公司_行业_` 模式）

### allowed_use

```yaml
High:   "可作为事实，但必须带来源"
Medium: "可作为背景或据公开资料显示，不得作最终结论"
Low:    "只能作为待核查线索，不得写成事实"
```

---

## 3. blocked_fields 检测

对 title + 摘要 做扫描，命中即标记：

```yaml
blocked_fields_scan:
  valuation:      [估值, 目标价, 合理市值, 市值空间]
  rating:         [评级, 买入, 卖出, 增持, 减持, 强烈推荐]
  advice:         [建议加仓, 建议减仓, 配置比例, 仓位]
```

命中处理：
- 该条 evidence 的 `needs_blocked_fields: YES`
- 命中字段进入 `blocked_fields: [...]`
- **不删除该 evidence，但禁止其内容进入最终卡片的事实层**

⚠️ 实测发现：新闻标题/摘要里普遍出现"投资需谨慎""PE突击入股""高负债"等表述，这些是**信号词**不是**结论词**，不应误杀。blocked_fields 只拦"建议性/结论性"表达，不拦描述性风险词。

---

## 4. 统一输出 schema（两个 adapter 共用）

```json
{
  "source_title": "string",
  "extracted_claim": "string (摘要)",
  "publish_date": "YYYY-MM-DD HH:MM:SS",
  "source_type": "string (来源名)",
  "source_url": "string",
  "source_rank": "High | Medium | Low",
  "evidence_level": "High | Medium | Low",
  "allowed_use": "string",
  "needs_blocked_fields": "YES | NO",
  "blocked_fields": ["valuation", "rating", ...],
  "tool_origin": "mx_finance_search_notice | mx_finance_search_news",
  "company_match_confidence": "float (待定 - 见下方 OPEN 问题)"
}
```

---

## 5. OPEN 问题（未解决，不得跳过）

| # | 问题 | 影响 | 状态 |
|---|------|------|------|
| 1 | **company_match_confidence 无法从 notice/news 直接得出** | 查"宁德时代"可能返回"恒翼能"相关新闻（宁德时代只是被提及） | UNRESOLVED |
| 2 | notice 工具来源混杂媒体源，不全是官方公告 | High 默认值不可靠 | 已给降级规则，待验证 |
| 3 | 发布时间时区/格式未标准化 | 跨源对比可能错位 | UNRESOLVED |
| 4 | 摘要可能被截断 | extracted_claim 不完整 | UNRESOLVED |

### 问题 1 是最大风险

实测 news 第一条：查询"宁德时代"返回的是「恒翼能:宁德时代既是股东又是客户...」——**主体其实是恒翼能，宁德时代只是被提及**。

这意味着：
- 不能假设 news/notice 返回结果都属于目标公司
- 必须有 company_match 过滤，否则 evidence 会张冠李戴
- 但 notice/news 工具本身不返回"这条属于哪家公司"的结构化字段

**结论：Announcements + News adapter 的字段映射可以设计，但 company_match_confidence 这一必填字段目前只能靠标题文本匹配启发式，不可靠。这是进入 Real Evidence Integration 前必须先解决的 blocker。**

---

## 6. 本 Spec 的边界

已完成：
- ✓ notice / news 两个 adapter 的列→字段映射
- ✓ evidence_level 分级规则（含来源降级）
- ✓ allowed_use 映射
- ✓ blocked_fields 扫描规则

未完成 / 不在本 Spec：
- ✗ company identification mapping
- ✗ company_match 过滤（OPEN 问题 1）
- ✗ 完整 pipeline 接线
- ✗ 正式拜访卡生成
- ✗ 生产接入

**下一步不是写代码，而是先决策 OPEN 问题 1（company_match 怎么做）。**
