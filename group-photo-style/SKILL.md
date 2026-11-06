---
name: group-photo-style
description: "把一批真人合照批量转成指定插画/动漫风格，并在风格化后把真人脸贴回、保持本人可辨识。三条通道：云端 gemini（整图重绘）、本地 AnimeGANv2（离线风格迁移）、本地 insightface+inswapper（身份回贴）。基于一个已验证案例（吉卜力风合照批量）。触发：合照、合影、团队照片、卡通化、动漫化、吉卜力、照片换脸、漫画风格、风格化照片"
---

# group-photo-style

把一批真人照片（尤其多人合照）批量转成指定风格，核心难点是**换脸后还认得出是谁**。

## 1. 核心矛盾（先读这个）

- 整图编辑模型（gemini/AnimeGANv2）做风格迁移时会**重绘人脸**，身份丢失（实测 ArcFace 相似度会掉到 0.02 附近，基本是陌生人）。
- 所以多人合照的完整链路是三层，各用各的工具，不要让一个模型干全部：
  - **底图层（风格）**：云端 gemini 或本地 AnimeGANv2，只负责把场景/氛围/配色变成目标风格。
  - **身份层（换脸）**：本地 insightface + inswapper，把真人脸像素级贴回风格图，身份相似度拉回 0.9。
  - **修饰层（光照/修复）**：换脸后必须重光照，否则源照平光会暴露；糊脸可用 GFPGAN 修复。
- 单人照可跳过身份层（卡通脸本来就不像本人）；**多人合照必须走身份层**。

## 2. 三条通道

| 通道 | 工具 | 何时用 | 成本 | 保身份 |
|---|---|---|---|---|
| A 云端风格化 | `belt` + `google/gemini-3-pro-image` | 质量优先、要精细控制风格 | 按张计费、照片上传云端 | 否（需配身份层） |
| B 本地风格化 | `vendor/animegan2-pytorch`（AnimeGANv2） | 离线、免费、快速批处理 | 0，纯本地 | 否（需配身份层） |
| C 身份回贴 | `scripts/swap_faces.py`（insightface+inswapper） | 多人合照、要认得出人 | 0，0.1s/张 | 是 |

## 3. 环境要求

- **通道 A（云端）**：`belt` CLI + `google/gemini-3-pro-image`，需能联网（本机走 Clash 7897 代理时 `export HTTPS_PROXY=http://127.0.0.1:7897`）。
- **通道 B（本地风格）**：需要 torch + torchvision。用 `~/workspaces/coverlab/bin/python`（有 insightface 无 torch）跑不了，需单独 torch 环境；本机已有 torch 2.15 + MPS 可用。
- **通道 C（身份回贴）**：`~/workspaces/coverlab/bin/python`（insightface 2.1 + onnxruntime），模型在 `~/workspaces/coverlab/models/`（`buffalo_l` + `inswapper_128.onnx`）。

## 4. 输入要求

- `SRC_DIR`：原始照片目录（jpg/png）
- `STYLE`：目标风格，默认吉卜力，见 `prompts/styles.md`
- 人脸模型路径：insightface 依赖 `~/workspaces/coverlab/models/`（`buffalo_l` + `inswapper_128.onnx`），换机器先确认存在。

## 5. 流程

**方案 A+B（推荐，多人合照）**：
1. 风格化底图 → `scripts/stylize.sh`（A 云端）或 `scripts/animegan.py`（B 本地）
2. 身份回贴 → `scripts/swap_faces.py`（逐张：原图 vs 风格图，按位置配对多张脸）
3. 重光照 → `scripts/relight.py`（可选，换脸后有接缝时用）
4. 验收 → `scripts/qc_identity.py`（ArcFace 相似度，阈值 0.85）

**方案 A only（单人/不要求认人）**：只跑第 1 步。

## 6. 提示词库

- `prompts/styles.md` — 风格预设（吉卜力/皮克斯/水彩/漫画…），含已验证措辞
- `prompts/storyboard.md` — 同一人物跨镜一致性的锚定写法（做视频分镜/连续镜时用）

## 7. 注意事项

- **禁止**把某个具体同事/艺人的脸照、姓名写进本 skill；这是通用工具，示例一律用占位符 `{主体}`。
- 换脸顺序陷阱：`inswapper.get(img, target_face, source_face)` —— 身份来自 `source_face`，要换的是 `target_face`，参数反了会静默失败。
- 验收不要靠肉眼，跑 ArcFace 相似度（`qc_identity.py`）。
- 云端通道（A）会把照片上传到 inference.sh，涉及他人肖像/内部照片时先确认授权。
