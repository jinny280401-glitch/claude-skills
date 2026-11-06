# paged 引擎 API 与快捷键

## 文件
- `assets/deck.js` — 分页引擎（命名空间 `Deck`）
- `assets/deck.css` — 结构版式（Theme 无关）
- `assets/theme-default.css` — 默认视觉 token；换 `themes/<name>/theme.css` 切主题
- `serve.py` — 本地预览（`python3 serve.py [端口]`）

## 页面结构
每页一个 `<section class="slide" data-key="..." data-title="...">`：
- `data-key`：稳定 narration key（录音时间轴接口），全局唯一，改页序前先校验。
- `data-title`：讲师备注标题。
- 深色页加 `class="slide dark"`。
- 讲师备注写进该页 `<template class="notes-src">…</template>`，与屏幕内容分离。
- 设计分辨率 1280×720（16:9），引擎自动等比缩放塞进任意视口。

## 快捷键（现场）
| 键 | 作用 |
|---|---|
| ← / → · 空格 · PageUp/Down | 翻页 |
| Home / End | 首页 / 末页 |
| F | 全屏 / 退出 |
| S 或 N | 讲师备注开关 |
| ? | 快捷键帮助 |

## URL 参数
- `?p=N` — 直接定位到第 N 页（1-based；也支持 `#N`）。刷新自动恢复上次所在页（localStorage）。
- `?qa=1` — 关闭过渡动画（截图/QA 用，避免抓在淡入中途）。
- `?notes=1` — 载入即展开讲师备注。

## 控制台 API
- `Deck.go(n)` / `Deck.next()` / `Deck.prev()` — 1-based 跳转。
- `Deck._stop` — 当前页 narration key（供录音对齐读取）。

## 录音时间轴接口（预留，未实现）
每页 `data-key` 即停靠点 key。未来 narration manifest 形如
`{stops:[{key, script, audio, dur}]}`，按 key 对齐讲稿/音频；key 缺失或页序变动需先校验。
