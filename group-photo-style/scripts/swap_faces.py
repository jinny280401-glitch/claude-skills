#!/usr/bin/env python3
"""身份回贴：把真人脸贴回风格化后的照片（支持多人合照，按位置配对）。

用法:
  swap_faces.py SRC_IMG STYLIZED_IMG OUT_IMG [--models DIR] [--relight]

- SRC_IMG: 原始真人照片（身份来源）
- STYLIZED_IMG: 风格化后的照片（要换脸的目标）
- 多张脸按归一化中心坐标排序后配对，适用于站位不变的合照。

inswapper.get(img, target_face, source_face) 语义：
  身份来自 source_face，绘制到 target_face 所在的 img。参数反了会静默失败。
"""
import os, sys, argparse
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from insightface.model_zoo.inswapper import INSwapper

DEFAULT_MODELS = os.path.expanduser("~/workspaces/coverlab/models")

def detect(app, img):
    return app.get(img)

def sort_faces(faces, img_h, img_w):
    """按归一化 (中心y, 中心x) 排序，保证原图与风格图同一人配对。"""
    def key(f):
        cy = (f.bbox[1] + f.bbox[3]) / 2 / img_h
        cx = (f.bbox[0] + f.bbox[2]) / 2 / img_w
        return (cy, cx)
    return sorted(faces, key=key)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_img")
    ap.add_argument("stylized_img")
    ap.add_argument("out_img")
    ap.add_argument("--models", default=DEFAULT_MODELS)
    ap.add_argument("--relight", action="store_true", help="换脸后做重光照")
    args = ap.parse_args()

    app = FaceAnalysis(name="buffalo_l", root=args.models, providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))

    src = cv2.imread(args.src_img)
    sty = cv2.imread(args.stylized_img)
    if src is None or sty is None:
        print("读取失败"); sys.exit(2)
    sh, sw = src.shape[:2]; th, tw = sty.shape[:2]

    src_faces = sort_faces(detect(app, src), sh, sw)
    sty_faces = sort_faces(detect(app, sty), th, tw)
    print(f"原图 {len(src_faces)} 张脸 / 风格图 {len(sty_faces)} 张脸")

    if not src_faces or not sty_faces:
        print("有一张图没检出脸，退出"); sys.exit(2)
    if len(src_faces) != len(sty_faces):
        print("警告：两图脸数不一致（可能风格化时丢了脸/多画了脸），按最小数配对")

    swapper = INSwapper(os.path.join(args.models, "inswapper_128.onnx"))
    result = sty.copy()
    for i, (sf, tf) in enumerate(zip(src_faces, sty_faces)):
        result = swapper.get(result, tf, sf, paste_back=True)
        print(f"换第 {i+1} 张脸")

    cv2.imwrite(args.out_img, result)
    print(f"WROTE {args.out_img}")

if __name__ == "__main__":
    main()
