# 提示词模式

标注说明:**[已验证]** = 在 burn_it_down 中实际跑通;**[未验证]** = 推演模板,首次使用需 Owner 看图确认。

## 模式 A:在参考封面上换脸 + 改字 [已验证]

调用:`google/gemini-3-pro-image-preview`,`images` = [主图, 脸照],`aspect_ratio` 1:1,`resolution` 2K,`output_format` png,`num_images` 1。

结构:
1. 描述第一张图(是什么、光色、取景),让模型知道要保留什么
2. 声明"只做两处改动"
3. 换脸段:身份取自第二张图;保持头部角度、姿态、取景、构图不变;要求重新渲染皮肤,使肤色、阴影、高光匹配原图的光与调色,"像在该场景拍摄,不是贴上去"
4. 文字段:旧文字 → 新文字,逐字给出;声明字体风格、字重、位置与原图一致
5. 禁止段:列出不许动的元素(字标、背景、光、角标线条)
6. 比例声明

实际发送的提示词原文见 `examples/burn-it-down.md`。

## 模式 B:局部擦除 [已验证]

整图编辑模型对"去 logo"会拦截(见案例)。改用:
1. 用 PIL/numpy 生成二值 mask(白=要擦除)
2. 先把 mask 叠红色回看,确认只盖住目标
3. `bria/erase`,`mask_type` = `manual`

mask 生成参数见案例文档。

## 模式 C:原创构图封面 [未验证]

```
Square 1:1 music cover, {MOOD} atmosphere, {GENRE}.
Subject: {ARTIST_DESCRIPTION}, {FRAMING}, {POSE}.
Lighting: {LIGHT_DIRECTION}, {COLOR_TEMPERATURE}.
Palette: {PALETTE}. Background: {BACKGROUND}.
Title text "{SONG_TITLE}" in {TYPE_STYLE}, placed {POSITION}.
Credit text "{ARTIST_NAME}" small, {POSITION}.
No other text, no logos, no watermarks.
```

用于艺人脸照参考时,在 `images` 传入脸照并写"identity from the reference photo"。

## 通用写法

- 写"保留什么",比只写"改什么"更能减少越界重绘,但**不能保证**(本案例中发型与耳朵仍被重绘)。
- 文字内容用引号包住,逐字给。
- 一次只改一类事(先换脸改字,再单独去字标),便于定位问题。
