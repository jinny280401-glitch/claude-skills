---
name: music-cover-art
description: "Music single/album cover production workflow: analyze reference covers, fuse an artist's face and style into the composition, set title/credit typography, iterate with image-edit models, and QC with pixel diffs. Based on one verified case (burn_it_down). Use for: song cover, single cover, album art, replace face on a reference cover, change cover title text, remove a logo from a cover. Triggers: 专辑封面, 歌曲封面, 单曲封面, 封面换脸, 封面改字, music cover, album cover, single artwork, cover art"
---

# music-cover-art

把 burn_it_down 封面的制作经验封装成可复用流程。**只有一个已验证案例**,其他风格的做法在文档中标为"未验证模板"。

## 1. 适用场景

- 给新歌做封面(原创构图,或在参考封面上做编辑)
- 把艺人的脸融合进已有构图,并改歌名/署名
- 去掉参考图上与艺人无关的第三方字标

不适用:不要假设新歌沿用 burn_it_down 的视觉风格(暖橙逆光、深蓝暗角、条形无衬线标题)。风格由歌曲决定。

**禁止**把 burn_it_down 的参考图(第三方游戏发行方的单曲封面)当作新歌的默认模板或默认输入。它只是一次性案例;新歌的参考图必须由 Owner 为该歌指定,并先确认权利状态。

## 2. 输入要求

| 字段 | 说明 |
|---|---|
| SONG_TITLE / ARTIST_NAME | 封面上要出现的文字,逐字确认大小写 |
| GENRE / MOOD | 决定色调与字体气质 |
| REFERENCE_IMAGES | 视觉参考,只记路径,不复制进 Skill |
| ARTIST_PHOTO | 脸照,先看图确认身份与角度 |
| TARGET_PLATFORM / OUTPUT_SIZE | 默认 1:1 正方形,2048×2048 |

## 3. 前置检查(先做,省返工)

1. 用 Read 打开两张图,确认真的"看到"了。若返回 `[Unsupported Image]`,先查 `env | grep ANTHROPIC` 的 `*_MODEL_NAME` 是否指向无视觉模型(本案例根因是 cc-switch 路由到 DeepSeek),让 Owner 切 provider 后重启会话。看不到图就不能验图,不要盲跑。
2. 确认参考图的权利状态,见 `references/quality-checklist.md` 的"权利与发布"。

## 4. 流程

按 `references/workflow.md` 的 10 步执行:理解风格 → 分析参考 → 提创意 → 写提示词 → 初版 → 查人物 → 查文字 → 查构图 → 迭代 → 导出。

- 风格分析、人物与背景融合、迭代策略:`references/workflow.md`
- 提示词模板与已验证措辞:`references/prompt-patterns.md`
- 歌名与署名排版:`references/typography.md`
- 验收与导出:`references/quality-checklist.md`
- 完整案例:`examples/burn-it-down.md`

## 5. 工具选择(已验证)

| 任务 | 工具 | 备注 |
|---|---|---|
| 换脸 + 改字 | `google/gemini-3-pro-image-preview`(belt) | `images` 直接传本地绝对路径,主图在前、脸照在后,约 35 秒 |
| 精确去除局部元素 | `bria/erase` + 自制 mask | 整图编辑模型会拒绝"去 logo"(判为去水印),且会重绘无关区域 |
| QC 对比 | PIL + numpy 像素 diff | 系统无 cv2,不要依赖 |

## 6. 已知陷阱

- 整图指令编辑会把"脸"以外的发型、耳朵一并重绘,无法靠提示词完全锁死。需要保留原样的区域,用 mask 局部方案。
- 署名行要求小型大写时,模型会输出全大写,写提示词时就按大写给。
- 模型会放大相似字体,不保证与原字体字形一致。需要字形精确一致时,用字体文件后期合成。

## 7. 输出

每次交付四件套:`FINAL_COVER`(png)、`PROMPT_RECORD`(实际发送的提示词原文)、`DESIGN_NOTES`、`QC_RECEIPT`。命名与导出规范见质量检查清单。

## 8. 资产保护

不删除、不覆盖、不移动原始素材;最终成品另存新文件名;不把私人照片或受版权保护的参考图复制进本 Skill 目录;不 commit、不 push、不发布。
