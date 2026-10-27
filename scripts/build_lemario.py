"""Construye el lemario completo del DEMel (sin descomprimir el zip).

Uso: python3 build_lemario.py <zip> <carpeta_salida>
Salida:
  lemario.csv         un lema por fila: id, lema, categorías, documentaciones, fuentes,
                      primera documentación primaria (desde, hasta, fuente), última (hasta)
  formas_indice.csv   forma documentada (normalizada) -> lema, con nº de documentaciones
Datos: DEMel, Universidad de Rostock 2026, CC BY-SA 4.0, doi:10.18453/rosdok_id00005462
"""
import csv, json, re, sys, zipfile, collections

ZIP, OUT = sys.argv[1], sys.argv[2]

def norm(f):
    f = f.lower().replace("ſ", "s")
    f = re.sub(r"[\[\]{}<>()¿?¡!.,;:\"'«»…]", "", f)
    return f.strip()

z = zipfile.ZipFile(ZIP)
names = [i.filename for i in z.infolist()
         if i.filename.startswith("data/json/attestations/") and not i.filename.endswith("/")]
lem = {}                                   # lemmaId -> dict
forms = collections.Counter()              # (forma, lemmaId) -> n
for n in names:
    d = json.loads(z.read(n))
    lid = d.get("lemmaId")
    L = lem.setdefault(lid, {"name": d.get("lemmaName"), "pos": set(), "n": 0, "src": set(),
                             "prim": []})
    L["n"] += 1
    L["src"].add(d.get("sourceId"))
    L["pos"].update(d.get("lemmaPartOfSpeechs") or [])
    if d.get("type") == "primary" and d.get("datingFromSearch") is not None:
        L["prim"].append((d["datingFromSearch"], d["datingToSearch"], d.get("sourceName")))
    f = d.get("form")
    if f and d.get("type") == "primary" and not d.get("isMultiwordexpr"):
        k = norm(f)
        if k:
            forms[(k, lid)] += 1

with open(f"{OUT}/lemario.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["lemmaId", "lema", "categorias", "docs_total", "docs_primarias", "fuentes",
                "primera_desde", "primera_hasta", "primera_fuente", "ultima_hasta"])
    for lid, L in sorted(lem.items()):
        p = sorted(L["prim"], key=lambda r: (r[0], r[1]))
        first = p[0] if p else ("", "", "")
        w.writerow([lid, L["name"], "|".join(sorted(L["pos"])), L["n"], len(p), len(L["src"]),
                    first[0], first[1], first[2], max((r[1] for r in p), default="")])
with open(f"{OUT}/formas_indice.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["forma", "lemmaId", "n"])
    for (k, lid), c in sorted(forms.items()):
        w.writerow([k, lid, c])
print("lemas:", len(lem), "| pares forma-lema:", len(forms), "| formas distintas:", len({k for k, _ in forms}))
