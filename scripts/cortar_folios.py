#!/usr/bin/env python3
# Uso: python scripts/cortar_folios.py <carpeta con p-001.jpg… (pdfimages -j -f 2)> web/img/cid 1254 72
"""Corta las aperturas del PDF de la BNE (Vitr/7/17) en folios: p-k = [(k-1)v | k r]; p-075 = [74v | guarda]."""
import sys, os
from PIL import Image
import numpy as np
raw, out, alto, q = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
os.makedirs(out, exist_ok=True)
def medianil(im):
    # centro del libro (sin el fondo negro) y, cerca de él, la sombra del medianil
    g = np.asarray(im.convert("L"), dtype=float)
    col = g[int(g.shape[0]*.15):int(g.shape[0]*.85)].mean(axis=0)
    claro = np.where(col > 60)[0]; c = (claro[0] + claro[-1]) // 2
    r = int(g.shape[1] * .035); a, b = c - r, c + r
    suave = np.convolve(col, np.ones(25)/25, mode="same")[a:b]
    return a + int(np.argmin(suave))
tot = 0
for k in range(1, 76):
    im = Image.open(f"{raw}/p-{k:03d}.jpg").convert("RGB")
    x = medianil(im)
    partes = []
    if k >= 2: partes.append((f"{k-1}v", im.crop((0, 0, x, im.height))))
    if k <= 74: partes.append((f"{k}r", im.crop((x, 0, im.width, im.height))))
    for nom, p in partes:
        p = p.resize((round(p.width * alto / p.height), alto), Image.LANCZOS)
        f = f"{out}/{nom}.jpg"; p.save(f, "JPEG", quality=q, optimize=True, progressive=True); tot += os.path.getsize(f)
print("folios:", len(os.listdir(out)), "total MB: %.1f" % (tot/1e6))
