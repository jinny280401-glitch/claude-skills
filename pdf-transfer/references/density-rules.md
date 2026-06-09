# PDF-Transfer 排版规则 — "技术不要留白"

> 核心约束：每页都要塞满有意义的内容，最后一页不能 < 半页。

---

## 1. 分页策略

### ❌ 禁用：强制分页
```css
.spread { page-break-after: always; }  /* 反模式 */
```

### ✅ 正确：自然流 + 关键节点分页
```css
/* 默认：内容自然填满一页 */
/* 封面/章首：唯一允许的强制分页 */
.masthead { page-break-after: always; }
.chapter-start { page-break-before: always; }
```

**为什么**：强制分页适合"封面+独立章节"的 premium 文档；不适合"密度优先"的报告。

---

## 2. 抗孤行 / 抗断页

每条规则都对应一个反模式：

| 反模式 | CSS 修法 | 说明 |
|---|---|---|
| 标题单独在页尾 | `h1, h2, h3 { page-break-after: avoid; }` | 标题后面紧跟正文 |
| 表格断在两页 | `table { page-break-inside: avoid; }` | 整表换页 |
| 章节断成两半 | `.chapter-intro { page-break-inside: avoid; }` | 章节标题+引言一起 |
| 警告框断页 | `.warn-box { page-break-inside: avoid; }` | 警告框保持完整 |

---

## 3. 边距 / 字号 / 行高（密度黄金参数）

```css
@page { size: A4; margin: 16mm 16mm 16mm 16mm; }  /* 比 premium 18mm 更紧 */
body { font-size: 9.2pt; line-height: 1.55; }       /* 比 premium 9.4pt 略小 */
h2 { font-size: 11pt; }
h1 { font-size: 15pt; }                             /* 章节标题别太大 */
```

**调节原则**：内容密 → 用更小边距；内容稀 → 退回 18mm。

---

## 4. 表格密度（最易出留白的地方）

### 行高 / 内边距
```css
.data-table th { padding: 1.4mm 2mm; }     /* 别用 3mm */
.data-table td { padding: 1.5mm 2mm; }     /* 紧凑即可 */
```

### 避免：把表格切碎成多张
```html
<!-- ❌ 反模式:三段小表 -->
<table>...</table>
<p>说明文字</p>
<table>...</table>

<!-- ✅ 合并成一张表 + 表头分组 -->
<table>
  <thead><tr><th colspan="4">第一组</th></tr></thead>
  ...
  <thead><tr><th colspan="4">第二组</th></tr></thead>
  ...
</table>
```

### 列宽
| 列类型 | 宽度 | 例子 |
|---|---|---|
| 代码/编号 | 14% | `601208` |
| 名称 | 18% | `东材科技` |
| 数值（右对齐） | 12% | `+10.00%` |
| 文本说明 | auto | `60 日新高` |

---

## 5. 自检清单（导出后必过）

- [ ] 最后一页 > 半页（如果 < 半页，合并到倒数第二页）
- [ ] 没有空白页（99% 是空 `<section>` 或多余 page-break）
- [ ] 没有孤行标题
- [ ] 没有跨页断表格
- [ ] 每页字符数 ≥ 200（脚本自动检查）

**判断留白过度的标准**：
- 最后一页 < 50% 高度 → 必须重排
- 任何一页 < 200 字符 → 警告但不阻塞

---

## 6. 反模式速查

| 反模式 | 修法 |
|---|---|
| 每个 section 都 `class="spread"` 强制分页 | 只在 `.masthead` 强制，其他自然流 |
| 表格 cell padding 3mm | 改 1.5mm |
| 字号 10pt + 行高 1.8 | 改 9.2pt + 1.55 |
| 把章节标题 h2 写到 18pt | 改 11pt |
| 表格断两页不在意的 | 加 `page-break-inside: avoid` |
| 封面留白多 | 加 cover-index 4 列模块索引 |

---

## 7. 性能 & 字体

### macOS 默认字体链（已验证）
```css
font-family: "PingFang SC", "Heiti SC", "Songti SC", "Noto Sans CJK SC", sans-serif;
```

### weasyprint 依赖
```bash
brew install pango harfbuzz libdatrie libthai  # 一次性安装
```

### Chrome fallback（如果 weasyprint 渲染异常）
```bash
ENGINE=chrome ./scripts/html2pdf.sh input.html out.pdf
```

---

## 8. 命名规范

| 文件类型 | 命名 | 例子 |
|---|---|---|
| 工作 HTML | kebab-case, ASCII | `auction-report.html` |
| 输出 PDF | 用户可见的中文标题 | `集合竞价-2026-06-09.pdf` |

参考命名风格：`<主题>-<日期>.{html,pdf}`
