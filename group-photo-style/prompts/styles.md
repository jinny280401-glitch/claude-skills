# 风格预设（prompt 库）

每个预设是一段**可直接填进 `belt` gemini 或 AnimeGANv2 无**的整图重绘提示词。字段化后可用脚本变量替换 `{主体}`、`{风格}`。

> 纪律：整图模型会重绘人脸，所以"保持每个人脸不变"这类话**对换脸无效**——身份靠身份层（swap_faces.py）回贴，提示词只负责氛围与配色。

## 1. 吉卜力（已验证）

```
Transform this photo into Studio Ghibli / Hayao Miyazaki hand-drawn animation style.
Redraw every human FACE as a classic Ghibli cartoon face: large soft expressive eyes,
gentle clean linework, warm natural skin tones, simplified features — NOT pixelation or blur.
Keep each person's original hairstyle, expression, head pose, body posture, gestures,
clothing and the background composition unchanged.
Apply an overall Ghibli color grade: bright, warm, healing, high natural saturation,
soft golden sunlight, clean summer daylight, subtle retro film warmth.
Preserve the original aspect ratio and layout.
```

## 2. 皮克斯 3D

```
Transform this photo into a Pixar-style 3D render. Soft rounded 3D characters,
subsurface-scattering skin, big expressive eyes, gentle rim lighting, warm saturated colors.
Keep every person's hairstyle, expression, pose, clothing and the background composition
unchanged. Preserve the original aspect ratio.
```

## 3. 水彩手绘

```
Transform this photo into a soft watercolor illustration. Loose translucent washes,
light pigment granulation, delicate ink outlines, generous white space, muted pastel palette.
Keep every person's pose, expression, clothing and the scene composition unchanged.
Preserve the original aspect ratio.
```

## 4. 热血漫画（黑白网点）

```
Transform this photo into a bold manga / comic ink style. Heavy black ink outlines,
dramatic cross-hatching, screentone halftone shading, high contrast, energetic poses.
Keep every person's pose, expression, clothing and composition unchanged.
Preserve the original aspect ratio.
```

## 使用方式

- 云端：填进 `scripts/stylize.sh` 的 `PROMPT` 变量。
- 本地：AnimeGANv2 只有固定的 4 个权重（paprika / face_paint_512_v1 / face_paint_512_v2 / celeba_distill），无法用文字改风格，直接选权重即可。
