#!/usr/bin/env python3
"""本地风格迁移：AnimeGANv2（bryandlee/animegan2-pytorch，MIT）封装。

用法:
  animegan.py SRC_DIR OUT_DIR [--weight face_paint_512_v2] [--device mps|cpu]

权重（位于 skill 的 vendor/animegan2-pytorch/weights/，首次运行前下载）:
  face_paint_512_v2  人脸卡通（最接近吉卜力人脸，默认）
  face_paint_512_v1  人脸卡通 v1
  paprika            动画电影场景风
  celeba_distill     webtoon 人脸风
"""
import os, sys, argparse
import torch
from torchvision.transforms.functional import to_tensor, to_pil_image
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "..", "vendor", "animegan2-pytorch")
sys.path.insert(0, VENDOR)
from model import Generator  # noqa: E402

WEIGHTS_DIR = os.path.join(VENDOR, "weights")
KNOWN = {
    "face_paint_512_v2": "https://github.com/bryandlee/animegan2-pytorch/raw/main/weights/face_paint_512_v2.pt",
    "face_paint_512_v1": "https://github.com/bryandlee/animegan2-pytorch/raw/main/weights/face_paint_512_v1.pt",
    "paprika": "https://github.com/bryandlee/animegan2-pytorch/raw/main/weights/paprika.pt",
    "celeba_distill": "https://github.com/bryandlee/animegan2-pytorch/raw/main/weights/celeba_distill.pt",
}

def to_32s(x):
    return 256 if x < 256 else x - x % 32

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--weight", default="face_paint_512_v2")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--x32", action="store_true", help="缩放到 32 的倍数（大图省内存）")
    args = ap.parse_args()

    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    ckpt = os.path.join(WEIGHTS_DIR, args.weight + ".pt")
    if not os.path.exists(ckpt):
        print(f"下载权重 {args.weight} ...")
        torch.hub.download_url_to_file(KNOWN[args.weight], ckpt)

    device = torch.device(args.device if torch.backends.mps.is_available() and args.device == "mps" else "cpu")
    net = Generator()
    net.load_state_dict(torch.load(ckpt, map_location="cpu"))
    net.to(device).eval()
    print(f"model loaded: {args.weight} on {device}")

    os.makedirs(args.out_dir, exist_ok=True)
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    for name in sorted(os.listdir(args.src_dir)):
        if os.path.splitext(name)[-1].lower() not in exts:
            continue
        img = Image.open(os.path.join(args.src_dir, name)).convert("RGB")
        if args.x32:
            img = img.resize((to_32s(img.width), to_32s(img.height)))
        with torch.no_grad():
            t = to_tensor(img).unsqueeze(0) * 2 - 1
            out = net(t.to(device), False).cpu().squeeze(0).clip(-1, 1) * 0.5 + 0.5
            out = to_pil_image(out)
        out.save(os.path.join(args.out_dir, name))
        print(f"saved: {name}")

if __name__ == "__main__":
    main()
