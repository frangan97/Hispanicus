"""Extrae del zip del DEMel (sin descomprimirlo) las documentaciones anotadas en uno o más textos del corpus.

Uso: python3 scripts/extract_documentaciones.py <zip> <carpeta_salida> <t0006> [<t0120> ...]
Salida: <carpeta_salida>/<tNNNN>_documentaciones.csv, con las documentaciones cuyo id (obj:demel_dNNN) aparece
anotado en ese texto del corpus (sirve para cualquier texto, aunque una obra se componga de varias fuentes).
Datos: DEMel, Universidad de Rostock 2026, CC BY-SA 4.0, doi:10.18453/rosdok_id00005462
"""
import csv, json, re, sys, zipfile
from pathlib import Path

ZIP, OUT, TEXTOS = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
RAIZ = Path(__file__).resolve().parent.parent
CAMPOS = ["id", "type", "form", "lemmaId", "lemmaName", "isMultiwordexpr", "multiwordexpr",
          "datingDisplaySearch", "datingFromSearch", "datingToSearch", "isDatingSearchExact",
          "sourceId", "sourceName", "contextExists", "contextTeitextId", "contextLocation", "contextKwic"]
ids = {}
for t in TEXTOS:
    tei = (RAIZ / "Mueller_Corpus_2026_data" / "texts" / "tei" / ("demel_%s.tei.xml" % t)).read_text(encoding="utf-8")
    ids[t] = set(re.findall(r"demel_(d\d+)", tei))
    print(t, len(ids[t]), "documentaciones anotadas en el TEI")
z = zipfile.ZipFile(ZIP)
filas = {t: [] for t in TEXTOS}
for i in z.infolist():
    if not i.filename.startswith("data/json/attestations/") or i.filename.endswith("/"): continue
    d = json.loads(z.read(i.filename))
    for t in TEXTOS:
        if d.get("id") in ids[t]: filas[t].append({c: d.get(c, "") for c in CAMPOS})
for t in TEXTOS:
    fn = OUT / ("%s_documentaciones.csv" % t)
    with open(fn, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, CAMPOS); w.writeheader(); w.writerows(filas[t])
    print(fn.name, len(filas[t]), "filas")
