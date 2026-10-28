"""Lematización morfológica de respaldo para español medieval.

Se usa cuando la forma no está documentada en el DEMel. Quita terminaciones verbales y de
número/género, arma infinitivos o formas base candidatas y las busca entre los nombres de lema
del DEMel, comparando por un "esqueleto" que absorbe variantes gráficas y fonéticas habituales
(l-/ll-/pl-, f-/h-, b/v/u, ç/z/c, ss/s, ñ/nn, y/i). Funciona con formas regulares; no resuelve
formas irregulares (dixo, fue) ni palabras pegadas.
"""
import re, unicodedata, collections

def _plain(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c)).replace("ſ", "s")

def sk(s):
    s = _plain(s)
    s = s.replace("ph", "f").replace("v", "u").replace("j", "i").replace("y", "i").replace("b", "u").replace("z", "c")
    s = re.sub(r"^pl", "l", s)
    s = s.replace("ll", "l").replace("nn", "n").replace("ss", "s")
    return re.sub(r"^f(?=[aeiou])", "h", s)

def sk2(s):                                   # además reduce diptongos: pienso ~ pensar
    return sk(s).replace("ie", "e").replace("ue", "o")

def nombres(n):
    out = []
    for p in n.split(" / "):
        p = re.sub(r"[\[\]]", "", p).strip()
        p = re.sub(r"\s+\d+$", "", p)
        p = re.sub(r",\s*(a|as)$", "", p)
        p = re.sub(r"\(se\)$", "", p).strip()
        if p and " " not in p and p != "#dudoso":
            out.append(p)
    return out

def build_index(rows):
    """rows: filas de lemario.csv. Devuelve {esqueleto: [(lemmaId, docs, es_verbo)]}."""
    idx, idx2 = collections.defaultdict(list), collections.defaultdict(list)
    for r in rows:
        cats = r["categorias"].split("|") if r["categorias"] else []
        if cats and all(c.startswith("name_") for c in cats):
            continue
        es_v = any(c.startswith("verb") for c in cats)
        for n in nombres(r["lema"]):
            item = (r["lemmaId"], int(r["docs_total"]), es_v)
            for tabla, k in ((idx, sk(n)), (idx2, sk2(n))):
                tabla[k].append(item)
                if k.startswith("h"): tabla[k[1:]].append(item)   # aver ~ haber
    return idx, idx2

# (terminación de la forma, terminaciones de infinitivo a probar)
VERBO = [
 ("ando", ["ar"]), ("ado", ["ar"]), ("ada", ["ar"]), ("ados", ["ar"]), ("adas", ["ar"]),
 ("iendo", ["er", "ir"]), ("endo", ["er", "ir"]), ("ido", ["er", "ir"]), ("ida", ["er", "ir"]),
 ("idos", ["er", "ir"]), ("idas", ["er", "ir"]),
 ("aron", ["ar"]), ("amos", ["ar"]), ("ades", ["ar"]), ("aua", ["ar"]), ("auan", ["ar"]), ("aba", ["ar"]),
 ("aban", ["ar"]), ("ara", ["ar"]), ("aran", ["ar"]), ("asse", ["ar"]), ("assen", ["ar"]), ("are", ["ar"]),
 ("as", ["ar"]), ("an", ["ar"]), ("ad", ["ar"]), ("o", ["ar", "er", "ir"]), ("a", ["ar"]),
 ("ieron", ["er", "ir"]), ("iesse", ["er", "ir"]), ("iessen", ["er", "ir"]), ("iera", ["er", "ir"]),
 ("ieran", ["er", "ir"]), ("ien", ["er", "ir"]), ("ia", ["er", "ir"]), ("ian", ["er", "ir"]),
 ("io", ["er", "ir"]), ("emos", ["er"]), ("imos", ["ir"]), ("edes", ["er"]), ("ides", ["ir"]),
 ("es", ["er", "ir", "ar"]), ("e", ["er", "ir", "ar"]), ("en", ["er", "ir", "ar"]),
 ("ed", ["er"]), ("id", ["ir"]), ("ar", [""]), ("er", [""]), ("ir", [""]),
]
NOMBRE = [("es", ""), ("s", ""), ("as", "o"), ("as", "a"), ("os", "o"), ("a", "o"), ("e", "")]

def respaldo(forma, idx, n_max=3):
    """forma: palabra en minúsculas, solo letras. Devuelve lista de lemmaId, o []."""
    w = forma
    if len(w) < 4:
        return []
    found = collections.OrderedDict()
    def probar(base, solo_verbo):
        for tabla in (idx[0], idx[1]):
            if tabla is idx[1] and not ("ie" in base.lower() or "ue" in base.lower()):
                continue
            clave = sk(base) if tabla is idx[0] else sk2(base)
            for lid, docs, es_v in tabla.get(clave, []):
                if solo_verbo and not es_v: continue
                found.setdefault(lid, docs)
            if found: return
    for suf, infs in VERBO:
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            raiz = w[:len(w) - len(suf)]
            for inf in infs:
                if suf in ("ar", "er", "ir"): probar(raiz + suf, True)
                else: probar(raiz + inf, True)
    if not found:
        for suf, rep in NOMBRE:
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                probar(w[:len(w) - len(suf)] + rep, False)
    return [l for l, _ in sorted(found.items(), key=lambda kv: -kv[1])[:n_max]]


# ---------------------------------------------------------------------------
# Capas añadidas: clave de grafías, elección por frecuencia, segmentación de formas pegadas
# y carga de las tablas manuales (datos/manual/*.csv).
# ---------------------------------------------------------------------------
import csv, os

def fold(s):
    return s.replace("v", "u").replace("j", "i").replace("y", "i").replace("ç", "z").replace("ſ", "s").replace("ph", "f")

def clave(s):
    return fold(s.lower().translate(str.maketrans("áéíóúü", "aeiouu")))

def slug(s):
    return re.sub(r"[^a-z0-9ñ]+", "_", _plain(s)).strip("_")

def elegir(c, th=0.8, minimo=10):
    """c: {lemmaId: n}. Devuelve el lema dominante o None."""
    tot = sum(c.values())
    if not c or tot < minimo: return None
    k, n = max(c.items(), key=lambda kv: kv[1])
    return k if n / tot >= th else None

PROCL = ["a", "de", "en", "con", "por", "que", "ni", "non", "sin", "pora"]
ENCL = ["los", "las", "lo", "la", "lis", "les", "li", "le", "nos", "uos", "vos", "me", "te", "se"]
ELID = {"l": "lo"}
CORTAS = {"el", "la", "lo", "los", "las", "uos", "vos", "mi", "mio", "su", "sus", "sos", "tu"}

def _directo(w, fidx, solo_verbo, verbos):
    c = fidx.get(fold(w), {})
    ids = [k for k, _ in sorted(c.items(), key=lambda kv: -kv[1])]
    if solo_verbo: ids = [i for i in ids if i in verbos]
    return ids[0] if ids else None

def segmentar(w, fidx, idx, verbos):
    """Separa formas pegadas: proclítico + palabra (enel, delos, atodos) o verbo + pronombre
    (dixoli, tomolo, dixol). Devuelve [(texto, lemmaId), ...] o None."""
    w = w.lower()
    if len(w) < 4: return None
    for p in sorted(PROCL, key=len, reverse=True):
        if w.startswith(p) and len(w) - len(p) >= 2:
            rest0 = w[len(p):]
            for rest in ([ "e" + rest0 ] if rest0.startswith("l") else []) + [rest0]:   # dellos = de + ellos
                if len(rest) < 3 and rest not in CORTAS: continue
                a, b = _directo(p, fidx, False, verbos), _directo(rest, fidx, False, verbos)
                if a and b: return [(p, a), (rest, b)]
    for e in ENCL + list(ELID):
        if w.endswith(e) and len(w) - len(e) >= 3:
            base = w[:len(w) - len(e)]
            b = _directo(base, fidx, True, verbos)
            if not b and e in ENCL:
                r = [i for i in respaldo(base, idx) if i in verbos]
                b = r[0] if r else None
            if b:
                x = _directo(ELID.get(e, e), fidx, False, verbos)
                return [(base, b), (e, x)] if x else [(base, b)]
    return None

def indice_nombres(rows):
    """nombre de lema -> lemmaId (el más documentado). Admite 'en 1' exacto o 'en' a secas."""
    m = {}
    for r in rows:
        docs = int(r["docs_total"])
        for n in {r["lema"]} | set(nombres(r["lema"])):
            k = n.strip().lower()
            if k and (k not in m or docs > m[k][1]): m[k] = (r["lemmaId"], docs)
    return {k: v[0] for k, v in m.items()}

def _abrir(path):
    try:
        t = open(path, encoding="utf-8-sig").read()
    except UnicodeDecodeError:
        t = open(path, encoding="cp1252").read()
    return t

def cargar_manual(path):
    """CSV con columnas forma, lema, estado (ok | propuesta | descartar). Acepta , ; o tabulador, y UTF-8 o cp1252.
    Devuelve {clave(forma): (lema, estado)}."""
    out = {}
    if not os.path.exists(path): return out
    texto = _abrir(path)
    cab = texto.split("\n", 1)[0]
    delim = max([";", ",", "\t"], key=cab.count)      # Excel puede guardar con ; , o tabulador
    for r in csv.DictReader(texto.splitlines(), delimiter=delim):
        f = clave((r.get("forma") or "").strip()); l = (r.get("lema") or "").strip()
        est = (r.get("estado") or "propuesta").strip().lower()
        if f and l and est != "descartar": out[f] = (l, "ok" if est == "ok" else "propuesta")
    return out
