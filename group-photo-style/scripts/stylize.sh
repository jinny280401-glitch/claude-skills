#!/bin/zsh
# 云端批量风格化：belt + google/gemini-3-pro-image
# 用法: stylize.sh <SRC_DIR> <OUT_DIR> [STYLE_KEY]
#   STYLE_KEY 见 prompts/styles.md（ghibli|pixar|watercolor|manga），默认 ghibli
# 改进点（相对首版脚本）：比例自动探测，不再手写 ITEMS 表；输出靠 belt 返回的 saved 路径，不再 ls -t 兜底。
set -u
SRC="${1:?用法: stylize.sh SRC_DIR OUT_DIR [STYLE_KEY]}"
OUT="${2:?用法: stylize.sh SRC_DIR OUT_DIR [STYLE_KEY]}"
STYLE="${3:-ghibli}"

case "$STYLE" in
  ghibli) PROMPT="Transform this photo into Studio Ghibli / Hayao Miyazaki hand-drawn animation style. Redraw every human FACE as a classic Ghibli cartoon face: large soft expressive eyes, gentle clean linework, warm natural skin tones, simplified features — NOT pixelation or blur. Keep each person's original hairstyle, expression, head pose, body posture, gestures, clothing and the background composition unchanged. Apply an overall Ghibli color grade: bright, warm, healing, high natural saturation, soft golden sunlight, clean summer daylight, subtle retro film warmth. Preserve the original aspect ratio and layout." ;;
  pixar) PROMPT="Transform this photo into a Pixar-style 3D render. Soft rounded 3D characters, subsurface-scattering skin, big expressive eyes, gentle rim lighting, warm saturated colors. Keep every person's hairstyle, expression, pose, clothing and the background composition unchanged. Preserve the original aspect ratio." ;;
  watercolor) PROMPT="Transform this photo into a soft watercolor illustration. Loose translucent washes, light pigment granulation, delicate ink outlines, generous white space, muted pastel palette. Keep every person's pose, expression, clothing and the scene composition unchanged. Preserve the original aspect ratio." ;;
  manga) PROMPT="Transform this photo into a bold manga / comic ink style. Heavy black ink outlines, dramatic cross-hatching, screentone halftone shading, high contrast, energetic poses. Keep every person's pose, expression, clothing and composition unchanged. Preserve the original aspect ratio." ;;
  *) echo "未知 STYLE_KEY: $STYLE (可选 ghibli|pixar|watercolor|manga)"; exit 2 ;;
esac

APP="google/gemini-3-pro-image"
mkdir -p "$OUT"
LOG="$OUT/_batch.log"; : > "$LOG"

# 比例自动探测：读原图宽高 → 映射到 gemini 支持的枚举（AspectRatioAutoEnum）
detect_aspect() {
  local f="$1" w h r
  read w h <<< "$(sips -g pixelWidth -g pixelHeight "$f" 2>/dev/null | awk '/pixelWidth/{w=$2}/pixelHeight/{h=$2}END{print w,h}')"
  [ -n "$w" ] || { echo "auto"; return; }
  r=$(python3 -c "print(f'{$w/$h:.3f}')")
  python3 - "$r" <<'PY'
import sys
r=float(sys.argv[1])
def close(a,b): return abs(a-b)
pairs=[(21/9,"21:9"),(16/9,"16:9"),(3/2,"3:2"),(4/3,"4:3"),(5/4,"5:4"),(1,"1:1"),(4/5,"4:5"),(3/4,"3:4"),(2/3,"2:3"),(9/16,"9:16")]
best=min(pairs,key=lambda p:close(p[0],r))
print(best[1])
PY
}

for f in "$SRC"/*.(jpg|jpeg|png|JPG|PNG); do
  [ -f "$f" ] || continue
  name="${f:t:r}"
  aspect="$(detect_aspect "$f")"
  jq -n --arg p "$PROMPT" --arg s "$f" --arg a "$aspect" \
    '{prompt:$p, images:[$s], aspect_ratio:$a, resolution:"2K", output_format:"png", num_images:1, safety_tolerance:"BLOCK_NONE"}' > /tmp/gps_in.json
  echo "=== $name ($aspect) <- $f:t ===" >> "$LOG"
  saved=$(belt app run "$APP" --input @/tmp/gps_in.json --download="$OUT" --no-input 2>>"$LOG" | sed -n 's/^.*saved \(.*\.png\).*/\1/p' | head -1)
  if [ -n "$saved" ] && [ -f "$OUT/$saved" ]; then
    mv "$OUT/$saved" "$OUT/风格-$name.png"
    echo "OK -> 风格-$name.png" >> "$LOG"
  else
    echo "FAIL: $name (无 saved 路径)" >> "$LOG"
  fi
done
echo "=== DONE ===" >> "$LOG"
ls -1 "$OUT"/风格-*.png 2>/dev/null >> "$LOG"
