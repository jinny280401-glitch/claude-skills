---
name: html-presentation
description: 用自然语言生成分页式 HTML 演示。←/→ 翻页、页码、全屏、讲师备注、刷新恢复，适合培训/路演/产品介绍。中文优先，统一视觉主题，零构建打开即用，预留录音时间轴接口。触发：做 HTML 演示 / 培训演示 / 投影讲稿 / 分页 PPT / 路演文稿。
---

# HTML Presentation

把主题/大纲/讲稿做成一套可现场投影、可翻页的 HTML 演示。四层解耦：Content（文案/数据）→ Theme（CSS 变量）→ Scene/Slide（每页）→ Engine（播放）。

## 播放模式
- **paged（分页式）**：一页一观点，键盘翻页。用于培训、路演、产品介绍。引擎见 `template/paged/assets/deck.js`。

## 工作流（paged）
1. 问清：主题、受众、页数与大纲、每页要点、是否投影、用哪个 Theme。
2. 从 `template/paged/` 复制骨架到目标目录（不覆盖已有文件）。
3. 选 Theme：默认 `theme-default.css`；要中性黑灰 + 蓝 accent 配色，额外引入 `themes/counterpoint/theme.css`。
4. 把大纲映射成每页一个 `.slide`，屏上文字≤20 字（指令全文类页例外）。
5. 讲师备注写进该页 `<template class="notes-src">`，与屏幕内容分离。
6. 本地 `python3 serve.py` 预览；`?p=N` 定位、`?qa=1` 关动画截图、`?notes=1` 展开备注。
7. 投影前确认：F 全屏、←/→ 翻页、S 备注、刷新恢复页码。

## 约束
- 四层解耦：产品内容只写在 Content，不写进 Engine/Theme。
- 零构建：原生 JS 多文件 `<script>` 顺序加载，不引打包器。
- 颜色只用 CSS 变量；一页一观点；中文优先。
- 每页 `data-key` 为稳定 narration key（录音时间轴接口），改页序前先校验。
- 截图类界面：有真实截图才用，否则用明确标注的示意占位，不伪造产品界面。

## 参考
- references/engine-api.md       引擎 API 与快捷键
