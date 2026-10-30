# 质量检查清单

每项给结论:PASS / FAIL / NOT_CHECKED,并写依据。

## A. 前置

- [ ] 已用 Read 看过所有输入图,没有 `[Unsupported Image]`
- [ ] 输入文件已记录路径与 sha256(`shasum -a 256`)

## B. 人物

- [ ] 脸与脸照是同一人,角度与构图一致
- [ ] 肤色、高光、阴影与场景光一致,没有"贴上去"感
- [ ] 与 Owner 确认过发型、耳朵、服饰等越界改动是否接受

## C. 文字

- [ ] 歌名逐字核对,含大小写与空格
- [ ] 署名逐字核对
- [ ] 无多余文字、无乱码
- [ ] 缩略图(约 300px)下歌名可读

## D. 未改动区域(像素 diff)

对"应保持不变"的区域做前后对比:裁切并排目测,再算数值。

```python
import numpy as np
from PIL import Image
a = np.array(Image.open(before).convert("RGB")).astype(int)
b = np.array(Image.open(after).convert("RGB")).astype(int)
diff = np.abs(a - b).sum(axis=2)
outside = diff[mask == 0]   # mask 为被允许修改的区域
print(outside.max(), outside.mean(), (outside > 10).sum(), outside.size)
```

先检查 `a.shape == b.shape`。整图编辑模型的输出尺寸可能与输入不同,需先缩放对齐再比对(此时数值只作参考)。

参考结果(局部擦除):mask 外平均差 0.137,仅 0.25% 像素差大于 10(mask 边缘过渡)。

## E. 权利与发布

- [ ] 参考图来源与权利:burn_it_down 以第三方发行方封面为编辑底图,该成品**仅作私人练习**。对外发行的封面应基于原创或已授权素材
- [ ] 艺人本人脸照:未经本人授权不使用;不把私人照片放进可分发目录
- [ ] 不自行发布,发布由 Owner 决定

## F. 导出规范

- 格式 png,正方形,默认 2048×2048(平台要求更小则另存缩放版,保留母版)
- 成品使用新文件名,例:`{song_slug}_final.png`,不覆盖输入
- 同目录保存过程文件(提示词、mask)以便复现
- 记录成品 sha256 与字节数

## G. QC_RECEIPT 模板

```
COVER = {path}
SHA256 = {hash}
SIZE = {w}x{h}
INPUTS_UNCHANGED = {yes/no, sha256 对比}
IDENTITY = {PASS/FAIL, 依据}
TEXT = {PASS/FAIL, 逐字}
UNCHANGED_REGIONS = {数值}
OWNER_ACCEPTED_DEVIATIONS = {列表}
RIGHTS_NOTE = {说明}
VERDICT = {…}
```
