"""Genera las tablas manuales de lemas (datos/manual/comunes.csv y cid.csv) con propuestas.

 - comunes.csv: formas ambiguas (de, al, se, es...). Valen para TODAS las obras.
 - cid.csv: formas sin lema (nombres propios, formas raras) de esta obra.
Las filas ya existentes no se tocan (se conservan tus correcciones); solo se agregan formas nuevas.
Columnas: forma; lema; estado; tipo; apariciones; ejemplo; candidatos
  estado: propuesta (sin revisar) | ok (revisada) | descartar (no aplicar)
  lema:   nombre del lema como figura en el DEMel (p. ej. "en 1"); varios separados por |.
          Si no existe en el DEMel se crea como lema propio, marcado "sin datos del DEMel".
Uso: python3 proponer_manuales.py
"""
import csv, json, os, re, subprocess, sys, tempfile, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lematizador as LZ

H = os.path.expanduser("~/mnt/Hispanicus")
LET = "a-záéíóúñçüſ"
COLS = ["forma", "lema", "estado", "tipo", "apariciones", "ejemplo", "candidatos"]
# Siempre se parte de una construcción SIN tablas manuales, para ver qué falta de verdad.
_tmp = os.path.join(tempfile.gettempdir(), "hys_cid_auto.json")
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_cid.py")],
               check=True, env=dict(os.environ, HYS_OUT=_tmp), stdout=subprocess.DEVNULL)
d = json.load(open(_tmp, encoding="utf-8")); lem = d["lemmas"]
core = lambda w: "".join(re.findall(f"[{LET}]", w.lower()))

def leer(path):
    if not os.path.exists(path): return []
    t = LZ._abrir(path); cab = t.split("\n", 1)[0]
    return list(csv.DictReader(t.splitlines(), delimiter=";" if cab.count(";") > cab.count(",") else ","))
def escribir(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, COLS, delimiter=";", extrasaction="ignore"); w.writeheader(); w.writerows(rows)

P_COM, P_OBRA = f"{H}/datos/manual/comunes.csv", f"{H}/datos/manual/cid.csv"
com, obra = ([], []) if "--regenerar" in sys.argv else (leer(P_COM), leer(P_OBRA))
hechas = {LZ.clave(r["forma"]) for r in com + obra}

sin, amb = {}, {}
for f in d["folios"]:
    for v in f["lines"]:
        texto = " ".join(t["w"] for t in v)
        for i, t in enumerate(v):
            c = core(t["w"])
            if not c: continue
            k = LZ.clave(c)
            if "l" not in t:
                s = sin.setdefault(k, {"n": 0, "cap": collections.Counter(), "ej": texto, "forma": c}); s["n"] += 1
                w = "".join(re.findall(f"[{LET}]", t["w"], flags=re.I))
                if i > 0 and w[:1].isupper(): s["cap"][w] += 1
            elif len(t["l"]) > 1 and not any(t.get(x) for x in ("v", "x", "d", "m", "g")):
                a = amb.setdefault(k, {"n": 0, "l": t["l"], "ej": texto, "forma": c}); a["n"] += 1

def preferido(forma, ids):
    ids = [i for i in ids if i in lem]
    for i in ids:                                   # primero, nombre idéntico a la forma (mas -> «mas», no «más»)
        if forma.lower() in {n.lower() for n in LZ.nombres(lem[i]["n"])}: return i
    for i in ids:
        if LZ.clave(forma) in {LZ.clave(n) for n in LZ.nombres(lem[i]["n"])}: return i
    return ids[0]

# Semilla: formas muy frecuentes del Cantar cuyo lema no es dudoso (nombres de personajes y lugares,
# una forma de «oír» y la abreviatura de «cristianos»). Quedan como "propuesta" hasta que las revises.
SEMILLA = {"minaya": "Minaya", "mynaya": "Minaya", "alfonsso": "Alfonso", "albarfanez": "Albarfáñez", "martin": "Martín",
           "diaz": "Díaz", "ruy": "Ruy", "antolinez": "Antolínez", "vermuez": "Bermúdez", "eluira": "Elvira", "gustioz": "Gustioz",
           "rachel": "Raquel", "ximena": "Jimena", "alcocer": "Alcocer", "munoz": "Muñoz", "xpistianos": "cristiano", "oyd": "oír"}
SEMILLA = {LZ.clave(k): v for k, v in SEMILLA.items()}
nuevas_com = nuevas_obra = nombres = 0
for k, a in sorted(amb.items(), key=lambda kv: -kv[1]["n"]):
    if k in hechas or a["n"] < 4: continue
    ids = [i for i in a["l"] if i in lem]
    if not ids: continue
    p = preferido(a["forma"], ids)
    com.append({"forma": a["forma"], "lema": lem[p]["n"], "estado": "propuesta", "tipo": "ambigua", "apariciones": a["n"],
                "ejemplo": a["ej"][:110], "candidatos": " | ".join(lem[i]["n"] for i in ids)}); nuevas_com += 1
for k, s in sorted(sin.items(), key=lambda kv: -kv[1]["n"])[:420]:
    if k in hechas or s["n"] < 2: continue
    es_nombre = s["n"] >= 2 and sum(s["cap"].values()) >= 0.6 * s["n"]
    lema = SEMILLA.get(k) or (s["cap"].most_common(1)[0][0] if es_nombre else "")
    es_nombre = es_nombre or k in SEMILLA
    nombres += es_nombre
    obra.append({"forma": s["forma"], "lema": lema, "estado": "propuesta" if lema else "", "tipo": ("nombre propio" if k not in (LZ.clave("xpistianos"), LZ.clave("oyd")) else "forma") if es_nombre else "revisar",
                 "apariciones": s["n"], "ejemplo": s["ej"][:110], "candidatos": ""}); nuevas_obra += 1
os.makedirs(os.path.dirname(P_COM), exist_ok=True)
escribir(P_COM, com); escribir(P_OBRA, obra)
print(f"comunes.csv: {len(com)} filas ({nuevas_com} nuevas) | cid.csv: {len(obra)} filas ({nuevas_obra} nuevas; {nombres} nombres propios propuestos, {nuevas_obra-nombres} para completar)")
