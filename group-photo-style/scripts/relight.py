"""Relight a swapped face patch to match the target scene's illumination.

Keeps the swapped identity's high-frequency detail, replaces the low-frequency
illumination with the target face's, and matches the target's chroma.
"""
import os
import sys

import cv2
import numpy as np


def relight(swapped_img, orig_img, swapped_path, out_path, feather=18):
    sw = cv2.imread(swapped_path)
    og = cv2.imread(orig_img)
    if sw.shape != og.shape:
        sw = cv2.resize(sw, (og.shape[1], og.shape[0]))

    diff = cv2.absdiff(sw, og).max(axis=2)
    mask = (diff > 8).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=2)
    if mask.max() == 0:
        cv2.imwrite(out_path, sw)
        return
    mask = cv2.GaussianBlur(mask, (feather * 2 + 1, feather * 2 + 1), 0).astype(np.float32) / 255.0

    sw_lab = cv2.cvtColor(sw, cv2.COLOR_BGR2LAB).astype(np.float32)
    og_lab = cv2.cvtColor(og, cv2.COLOR_BGR2LAB).astype(np.float32)

    m = mask
    sel = m > 0.05

    # --- L: keep swapped detail, take illumination from original ---
    ksize = 61
    sw_blur = cv2.blur(sw_lab[:, :, 0], (ksize, ksize))
    og_blur = cv2.blur(og_lab[:, :, 0], (ksize, ksize))
    detail = sw_lab[:, :, 0] - sw_blur
    l_new = og_blur + detail

    # --- a/b: match target chroma, keep swapped relative chroma ---
    sw_ab = sw_lab[:, :, 1:3]
    og_ab = og_lab[:, :, 1:3]
    d_sw = sw_ab - cv2.blur(sw_ab, (ksize, ksize))
    d_og = og_ab - cv2.blur(og_ab, (ksize, ksize))
    ab_new = og_ab + (d_sw - d_og)

    new_lab = sw_lab.copy()
    new_lab[:, :, 0] = l_new
    new_lab[:, :, 1:3] = ab_new
    out = cv2.cvtColor(np.clip(new_lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)

    blended = (sw.astype(np.float32) * (1 - m[:, :, None]) + out.astype(np.float32) * m[:, :, None])
    result = np.clip(blended, 0, 255).astype(np.uint8)
    cv2.imwrite(out_path, result)

    sw_face = sw_lab[:, :, 0][sel]
    og_face = og_lab[:, :, 0][sel]
    out_face = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)[:, :, 0][sel]
    print("L mean  orig=%.1f swapped=%.1f relit=%.1f" % (og_face.mean(), sw_face.mean(), out_face.mean()))
    print("L std   orig=%.1f swapped=%.1f relit=%.1f" % (og_face.std(), sw_face.std(), out_face.std()))


if __name__ == "__main__":
    relight(None, sys.argv[1], sys.argv[2], sys.argv[3])
