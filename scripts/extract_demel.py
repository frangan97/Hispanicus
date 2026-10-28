"""Extrae del zip del DEMel (sin descomprimirlo) lo necesario para Hispanicus.

Uso: python3 extract_demel.py <zip> <carpeta_salida>
Salida:
  cid_documentaciones.csv          documentaciones primarias de Cid(ADMYTE 0) (b0159)
  santa_oria_documentaciones.csv   documentaciones de Berceo StaOria (b0105)
  lemas_resumen.csv                por cada lema de esas dos obras: documentaciones totales,
                                   fuentes, fecha más temprana (desde-hasta) y su fuente
Datos: DEMel, Universidad de Rostock 2026, CC BY-SA 4.0, doi:10.18453/rosdok_id00005462
"""
import csv, json, sys, zipfile, collections

ZIP, OUT = sys.argv[1], sys.argv[2]
OBRAS = {"b0159": "cid_documentaciones.csv", "b0105": "santa_oria_documentaciones.csv"}
CAMPOS = ["id", "type", "form", "lemmaId", "lemmaName", "isMultiwordexpr", "multiwordexpr",
          "datingDisplaySearch", "datingFromSearch", "datingToSearch", "isDatingSearchExact",
          "sourceId", "sourceName", "contextExists", "contextTeitextId", "contextLocation", "contextKwic"]

z = zipfile.ZipFile(ZIP)
nombres = [i.filename for i in z.infolist() if i.filename.startswith("data/json/attestations/") and not i.filename.endswith("/")]
filas = {k: [] for k in OBRAS}
lemas_obra = collections.defaultdict(set)      # lemmaId -> obras donde aparece
por_lema = collections.defaultdict(list)       # lemmaId -> [(from, to, sourceName, type)]
nombre_lema = {}
for n in nombres:
    d = json.loads(z.read(n))
    lid = d.get("lemmaId")
    nombre_lema[lid] = d.get("lemmaName")
    por_lema[lid].append((d.get("datingFromSearch"), d.get("datingToSearch"),
                          d.get("sourceName"), d.get("type"), d.get("sourceId")))
    if d.get("sourceId") in OBRAS:
        filas[d["sourceId"]].append({c: d.get(c, "") for c in CAMPOS})
        lemas_obra[lid].add(d["sourceId"])

for sid, fn in OBRAS.items():
    with open(f"{OUT}/{fn}", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, CAMPOS); w.writeheader(); w.writerows(filas[sid])
    print(fn, len(filas[sid]), "filas")

with open(f"{OUT}/lemas_resumen.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["lemmaId", "lemma", "en_cid", "en_santa_oria", "docs_total", "docs_primarias",
                "fuentes_distintas", "primera_desde", "primera_hasta", "primera_fuente", "ultima_hasta"])
    for lid in sorted(lemas_obra):
        reg = por_lema[lid]
        prim = [r for r in reg if r[3] == "primary" and r[0] is not None]
        prim.sort(key=lambda r: (r[0], r[1]))
        p = prim[0] if prim else (None, None, "", "", "")
        ult = max((r[1] for r in prim), default="")
        w.writerow([lid, nombre_lema[lid], int("b0159" in lemas_obra[lid]), int("b0105" in lemas_obra[lid]),
                    len(reg), len(prim), len({r[4] for r in reg}), p[0], p[1], p[2], ult])
print("lemas_resumen.csv", len(lemas_obra), "lemas")
