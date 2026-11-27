#!/usr/bin/env python3
# Uso: python scripts/folios_berceo.py <carpeta Ms_4a (pdfimages -j)> <carpeta Ms_4b> web/img/berceo 1254 72
"""Folios de Berceo (RAE, Ms. 4a y 4b): un folio por página del PDF, nombrados como los <pb> del TEI t0120.
Ms 4a: p-005 = 1r; a partir del fol. 32 (faltan los fols. 30-31 de los Milagros), fol. k r = p(2k-1), k v = p(2k).
       Se toman 48v-65v (Santa Oria y San Millán).
Ms 4b: p-005 = 66r; fol. k r = p(2k-127), k v = p(2k-126), hasta 113v (Santo Domingo)."""
import sys, os
from PIL import Image
a, b, out, alto, q = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
os.makedirs(out, exist_ok=True)
tareas = []
for k in range(48, 66):
    if k > 48: tareas.append((f"{k}r", a, 2*k - 1))
    tareas.append((f"{k}v", a, 2*k))
for k in range(66, 114):
    tareas += [(f"{k}r", b, 2*k - 127), (f"{k}v", b, 2*k - 126)]
tot = 0
for nom, d, p in tareas:
    im = Image.open(f"{d}/p-{p:03d}.jpg").convert("RGB")
    im = im.resize((round(im.width * alto / im.height), alto), Image.LANCZOS)
    f = f"{out}/{nom}.jpg"; im.save(f, "JPEG", quality=q, optimize=True, progressive=True); tot += os.path.getsize(f)
print("folios:", len(tareas), "total MB: %.1f" % (tot/1e6))
