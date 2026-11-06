"""Measure identity transfer: ArcFace cosine similarity between source photo and target before/after swap.

用法:
  qc_identity.py SRC_IMG STYLIZED_IMG SWAPPED_IMG [--models DIR]

- 输出 style 图 vs 原图的相似度（换脸前，应接近 0），以及 swap 图 vs 原图（换脸后，应 ≥ 0.85）。
- 多人合照只取最大脸比对（单人为主用例）。
"""
import os, sys, argparse
import cv2
import numpy as np
from insightface.app import FaceAnalysis

DEFAULT_MODELS = os.path.expanduser("~/workspaces/coverlab/models")

ap = argparse.ArgumentParser()
ap.add_argument("src_img")
ap.add_argument("stylized_img")
ap.add_argument("swapped_img")
ap.add_argument("--models", default=DEFAULT_MODELS)
args = ap.parse_args()

app = FaceAnalysis(name="buffalo_l", root=args.models, providers=["CPUExecutionProvider"])
app.prepare(ctx_id=-1, det_size=(640, 640))


def emb(path):
    img = cv2.imread(path)
    faces = app.get(img)
    if not faces:
        return None
    faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
    return faces[0].normed_embedding


def cos(a, b):
    return float(np.dot(a, b))


e_src = emb(args.src_img)
e_base = emb(args.stylized_img)
e_swap = emb(args.swapped_img)

if e_src is None:
    print("原图没检出脸"); sys.exit(2)

print("src   ", args.src_img.split("/")[-1])
print("base  ", args.stylized_img.split("/")[-1], "-> sim to src:", round(cos(e_src, e_base), 4) if e_base is not None else "N/A")
print("swap  ", args.swapped_img.split("/")[-1], "-> sim to src:", round(cos(e_src, e_swap), 4) if e_swap is not None else "N/A")
if e_swap is not None and e_base is not None:
    print("delta (swap - base):", round(cos(e_src, e_swap) - cos(e_src, e_base), 4))
