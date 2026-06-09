# 跨平台字体配置

PDF-Transfer 模板的 font-family 顺序是**降级链** — 浏览器/weasyprint 自动选第一个可用的，无需手动切换。

---

## 字体降级链

```css
font-family: "PingFang SC", "Heiti SC", "Songti SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
```

| 顺序 | 字体名 | 适用平台 | 字重 |
|------|--------|---------|------|
| 1 | `PingFang SC` | macOS (10.11+) | Regular / Medium |
| 2 | `Heiti SC` | macOS (旧版) | Light / Medium |
| 3 | `Songti SC` | macOS | 衬线，作标题用 |
| 4 | `Microsoft YaHei` | Windows 7+ | Regular / Bold |
| 5 | `Noto Sans CJK SC` | Linux / UOS | Regular / Bold |
| 6 | `sans-serif` | 兜底 | 系统默认 |

---

## 平台字体安装

### macOS
系统自带，**无需安装**。检查命令：
```bash
fc-list :lang=zh
# 期望输出: PingFang.ttc / Heiti.ttc / Songti.ttc
```

如果缺失（极少见），重装 macOS 或拷贝字体到 `~/Library/Fonts/`。

---

### Linux (Ubuntu / Debian / 统信 UOS)

**UOS 注意**：统信是基于 Debian 的，`apt-get` 通用。Deepin 同理。

```bash
# 推荐: Noto Sans CJK
sudo apt-get install -y fonts-noto-cjk

# 备选: 文泉驿
sudo apt-get install -y fonts-wqy-zenhei fonts-wqy-microhei

# 检查
fc-list :lang=zh | head
# 期望: /usr/share/fonts/.../NotoSansCJKsc-Regular.otf
```

刷新字体缓存：
```bash
fc-cache -fv
```

---

### Windows

**Windows 7+ 系统自带**：
- `Microsoft YaHei` (msyh.ttc / msyh.ttf) — 无衬线
- `SimSun` (simfang.ttf) — 衬线

检查：
```powershell
Test-Path "C:\Windows\Fonts\msyh.ttc"
Test-Path "C:\Windows\Fonts\msyh.ttf"
```

如果缺失（精简版系统），从其他机器拷贝到 `C:\Windows\Fonts\` 即可。

---

## weasyprint 字体配置

weasyprint 默认使用系统字体（通过 fontconfig / Windows GDI）。**一般情况下无需额外配置**。

### 高级：自定义字体路径

如果字体没装在系统路径，可以：

**Linux/macOS**：放到 `~/.fonts/` 然后 `fc-cache -fv`

**Windows**：放到 `C:\Windows\Fonts\`

或在 HTML head 显式声明（不推荐，仅作 fallback）：
```css
@font-face {
  font-family: "CustomFont";
  src: url("file:///path/to/font.ttf");
}
```

---

## 验证脚本

`scripts/html2pdf.py` 自带字体检查：
```bash
$ python3 scripts/html2pdf.py input.html out.pdf
✓ 中文字体: 找到 4 个 (例: STHeiti Medium.ttc, PingFang.ttc, ...)
```

如果显示 "⚠ 未检测到中文字体"，按上述平台说明安装。

---

## 统信 UOS 特别说明

UOS 默认带的字体是 **Noto Sans CJK + 文泉驿**。
如果 weasyprint 渲染中文异常：

```bash
# 1. 装齐字体
sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei fonts-wqy-microhei

# 2. 检查 weasyprint 是否能找到
python3 -c "
from weasyprint import HTML
HTML(string='<html><body><p>中文测试</p></body></html>').write_pdf('/tmp/test.pdf')
"
# 用 PDF 阅读器打开 /tmp/test.pdf,确认中文不是方块
```

如果还是方块：
```bash
# 重装 pango
sudo apt-get install --reinstall libpango-1.0-0 libpangoft2-1.0-0
fc-cache -fv
```

---

## 添加自定义字体

如果业务需要品牌字体（如思源黑体、阿里巴巴普惠体）：

1. 把字体文件放到 `assets/fonts/` （需创建）
2. 在 HTML `<head>` 加：
   ```html
   <style>
   @font-face {
     font-family: "BrandFont";
     src: url("file:///path/to/assets/fonts/BrandFont.ttf");
   }
   </style>
   ```
3. 模板 font-family 加到最前：
   ```css
   font-family: "BrandFont", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
   ```

**注意**：跨平台分发时，把字体一起打包进 skill（注意版权）。
