# 三层管线方法论 + 上游归因

## 为什么必须分层

整图编辑模型（gemini-3-pro-image、AnimeGANv2）在像素级重绘全图时，人脸这类高语义区域会被重新生成，即使提示词明确写"保持不变"也一样——这是模型能力边界，不是提示词问题。实测：原脸 ArcFace 相似度会被拉到 0.02（陌生人）。

所以把流程拆成三层，每层用各自正确的工具：

| 层 | 工具 | 职责 | 关键点 |
|---|---|---|---|
| 底图层 | gemini / AnimeGANv2 | 场景、配色、氛围 | 别让它动脸，脸交给下一层 |
| 身份层 | insightface + inswapper | 把真人脸像素级贴回 | `get(img, target_face, source_face)` 参数顺序，反了静默失败 |
| 修饰层 | relight.py / GFPGAN | 重光照、修复糊脸 | 换脸后必须重光照，否则源照平光暴露 |

## 上游项目（vendored / 依赖）

- **AnimeGANv2 PyTorch**（`vendor/animegan2-pytorch/`）：`bryandlee/animegan2-pytorch`，MIT License。`model.py` + `LICENSE` 已 vendor；权重运行时从上游 GitHub raw 下载。
- **insightface**（`pip install insightface`，Apache-2.0）：`deepinsight/insightface`。模型 `buffalo_l`（人脸检测/ArcFace）与 `inswapper_128.onnx`（换脸）位于 `~/workspaces/coverlab/models/`，不随本 skill 分发（体积大，且含第三方权重）。
- **inswapper**（inswapper_128.onnx）：`deepinsight/inswapper`，非商用研究用途，未 vendor。

## 已实测事实（本机 MAC-002）

- insightface + inswapper：0.1–0.2s/张，纯本地 CPU，无 API 成本。
- 身份相似度（ArcFace cosine）：换脸前 0.02 → 换脸后 0.90。
- AnimeGANv2 face_paint_512_v2 在 MPS 上跑通（torch 2.15，3 张样例出图）。
- gemini-3-pro-image 云端 app 的 `aspect_ratio` 支持 `auto` 及 21:9 到 9:16 共 10 档枚举；`resolution` 1K/2K/4K；`output_format` png/jpeg/webp；`safety_tolerance` BLOCK_NONE。

## QC 纪律

- 验收不靠肉眼，跑 `qc_identity.py`，ArcFace 相似度阈值 0.85。
- 多人合照换脸前先比对原图/风格图各检出几张脸，不一致就停下来（可能漏脸或凭空多画脸）。

## belt 批处理三个坑（实测 2026-11-06/07）

1. **必须显式设代理**：Clash TUN 关掉后 belt 不会自动走系统代理，先 `export HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=... ALL_PROXY=...`。
2. **中文文字必糊**：整图重绘时 Gemini 会把中文（工牌姓名、招牌、字幕）写成乱码。小范围改字别重绘，用本地 PIL 像素编辑（连通分量擦除 + `ImageFont.truetype` 画新字，中文用 `Hiragino Sans GB.ttc` index=2）。
3. **`--download` 并发写同一目录会覆盖/截断**：每个 job 用独立 `--download=/tmp/gen_xxx`，完成后再 cp 到目标目录；失败时 belt 返回图片 URL，可 `curl -sL` 补拉。落盘后逐张用 PIL `Image.open().load()` 校验是否截断（全黑像素占比 <5% 且能 load）。

相关：[[feedback_belt_gemini_scene_pipeline]] [[feedback_album_cover_three_layer_pipeline]]
