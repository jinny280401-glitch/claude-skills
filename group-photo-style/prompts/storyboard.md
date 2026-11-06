# 同一人物跨镜一致性（storyboard / 连续镜头）

做视频分镜、连续画面时，最大痛点是**每一帧脸都不一样**。解法：把"主体身份"锚定成一段可复用的描述，所有镜头共用同一段锚点 + 各自场景。

## 主体锚点（每镜都带上）

```
The main character is the SAME {主体特征描述} as in the reference image:
{发型、五官、肤色、服装一句话}. Realistic Studio Ghibli hand-drawn watercolor style.
Keep her/his identity and face consistent with the reference.
```

## 场景锚点（每镜换）

```
Scene: {该镜场景一句话，含地点/动作/人物数量/字幕要求}.
Studio Ghibli hand-drawn watercolor, warm healing nostalgic palette, soft natural light,
16:9 cinematic composition.
```

## 示例（占位，勿填真名）

- 主体锚点：`The main character is the SAME young woman as in the reference image: long black wavy hair, gentle warm face, white blouse.`
- 镜头 1：`Scene: she stands proudly with both hands on hips, chest out, inside a spacious modern corporate open-plan office that is still empty and new.`

## 纪律

1. 每镜都**带参考图**（belt 的 `images` 字段传参考图），不要只靠文字描述身份。
2. 先做一张**定妆图**（纯正面、无场景），确认脸对了再展开批量分镜。
3. 分镜图里的人物数量、站位、字幕必须和原图一致——这是整图重绘最容易漏的，逐张核。
