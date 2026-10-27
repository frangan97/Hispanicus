"""Genera web/data/cid.json: el Cantar de mio Cid por folios y versos, con cada palabra
enlazada a su lema del DEMel.

 - Palabras con <seg corresp="obj:demel_d..."> en el TEI: lema verificado por el DEMel (v=1).
 - Resto de las palabras: lemas candidatos por coincidencia de forma (índice de formas del DEMel).
Fuente del texto: DEMel, corpus de textos t0103 (ADMYTE 0, transcr. Steven Kirby), CC BY-SA 4.0,
doi:10.18453/rosdok_id00005463. Léxico: doi:10.18453/rosdok_id00005462.
"""
import csv, html, json, re, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lematizador
H = os.path.expanduser("~/mnt/Hispanicus")
TEI = f"{H}/Mueller_Corpus_2026_data/texts/tei/demel_t0103.tei.xml"
ALT_OUT = os.environ.get("HYS_OUT")      # si está definida: construir sin tablas manuales y sin tocar la web
OUT = ALT_OUT or f"{H}/web/data/cid.json"

fold = lambda s: s.replace("v","u").replace("j","i").replace("y","i").replace("ç","z").replace("ſ","s").replace("ph","f")
LET = "a-záéíóúñçüſ"

# --- DEMel: documentaciones del Cid, lemario, índice de formas
att = {r["id"]: r for r in csv.DictReader(open(f"{H}/datos/cid_documentaciones.csv", encoding="utf-8"))}
lemario = {r["lemmaId"]: r for r in csv.DictReader(open(f"{H}/datos/lemario.csv", encoding="utf-8"))}
fidx = collections.defaultdict(dict)     # forma plegada -> {lemmaId: n}
lemma_forms = collections.defaultdict(collections.Counter)
for r in csv.DictReader(open(f"{H}/datos/formas_indice.csv", encoding="utf-8")):
    n = int(r["n"]); fidx[fold(r["forma"])][r["lemmaId"]] = fidx[fold(r["forma"])].get(r["lemmaId"], 0) + n
    lemma_forms[r["lemmaId"]][r["forma"]] += n

NAMEIDX = lematizador.build_index(lemario.values())
LZ = lematizador
VERBOS = {lid for lid, r in lemario.items() if any(c.startswith("verb") for c in r["categorias"].split("|"))}
NOM = LZ.indice_nombres(lemario.values())
MAN_COM = {} if ALT_OUT else LZ.cargar_manual(f"{H}/datos/manual/comunes.csv")
MAN_OBRA = {} if ALT_OUT else LZ.cargar_manual(f"{H}/datos/manual/cid.csv")
SINT = {}
def ids_manual(texto):
    out = []
    for nombre in texto.split("|"):
        nombre = nombre.strip()
        if not nombre: continue
        lid = NOM.get(nombre.lower())
        if not lid: lid = "x:" + LZ.slug(nombre); SINT[lid] = nombre
        if lid not in out: out.append(lid)
    return out

# --- TEI -> folios / versos / palabras
body = open(TEI, encoding="utf-8").read()
body = body[body.index("<body"):body.index("</body>")]
TOK = re.compile(r"<pb[^>]*?n=\"([^\"]+)\"[^>]*/>|<seg\b([^>]*)>|</seg>|<[^>]+>|[^<\s]+")
folios, cur, verse = [], None, []
seg_ids = []
def flush():
    global verse
    if verse and cur is not None: cur["lines"].append(verse)
    verse = []
used = set(); n_ver = 0; cnt = collections.Counter()
for line in body.split("\n"):
    for m in TOK.finditer(line):
        t = m.group(0)
        if m.group(1):                                  # <pb n="..."/>
            flush(); cur = {"n": m.group(1), "lines": []}; folios.append(cur); continue
        if t.startswith("<seg"):
            seg_ids = re.findall(r"demel_(d\d+)", m.group(2) or ""); continue
        if t == "</seg>": seg_ids = []; continue
        if t.startswith("<"): continue
        w = html.unescape(t)
        core = "".join(re.findall(f"[{LET}]", w.lower()))
        tok = {"w": w}
        if core:
            key = LZ.clave(core)
            lids = []
            for i in seg_ids:
                r = att.get(i)
                if r and r["lemmaId"] not in lids: lids.append(r["lemmaId"])
            if lids: tok["v"] = 1; n_ver += 1
            if not lids:
                man = MAN_OBRA.get(key) or MAN_COM.get(key)
                if man:
                    lids = ids_manual(man[0]); tok["x"] = 1 if man[1] == "ok" else 2; cnt["manual"] += 1
            if not lids:
                c = fidx.get(fold(core), {})
                cand = [k for k, _ in sorted(c.items(), key=lambda kv: -kv[1])[:4]]
                top = LZ.elegir(c) if len(cand) > 1 else None
                if top: lids = [top]; tok["d"] = 1; cnt["frecuencia"] += 1
                elif cand: lids = cand; cnt["forma_unica" if len(cand) == 1 else "ambigua"] += 1
            if not lids:
                sg = LZ.segmentar(core, fidx, NAMEIDX, VERBOS)
                if sg and all(l in lemario for _, l in sg):
                    lids = [l for _, l in sg]; tok["g"] = [t for t, _ in sg]; cnt["segmentada"] += 1
            if not lids:
                r = [l for l in LZ.respaldo(core, NAMEIDX) if l in lemario]
                if r: lids = r; tok["m"] = 1; cnt["terminacion"] += 1
            if lids: tok["l"] = lids; used.update(lids)
            else: cnt["sin_lema"] += 1
        verse.append(tok)
    flush()

lemmas = {}
for lid in sorted(used):
    if lid in SINT:
        lemmas[lid] = {"n": SINT[lid], "c": [], "d": 0, "p": 0, "s": 0, "f": [None, None, ""], "u": None, "fm": [], "x": 1}; continue
    L = lemario.get(lid)
    if not L: continue
    def num(x): return int(x) if x not in ("", None) else None
    lemmas[lid] = {"n": L["lema"], "c": L["categorias"].split("|") if L["categorias"] else [],
                   "d": int(L["docs_total"]), "p": int(L["docs_primarias"]), "s": int(L["fuentes"]),
                   "f": [num(L["primera_desde"]), num(L["primera_hasta"]), L["primera_fuente"]],
                   "u": num(L["ultima_hasta"]),
                   "fm": [f for f, _ in lemma_forms[lid].most_common(8)]}
meta = {"obra": "Cantar de mío Cid", "sigla": "Cid(ADMYTE 0)", "datacion": "c 1140?",
        "edicion": "Anónimo, Cantar de mío Cid. Madrid: Nacional, Vitrina 7-17, copiado 1300-1400. Transcr. Steven Kirby. In: ADMYTE 0.",
        "texto": "DEMel, corpus de textos t0103 (CC BY-SA 4.0), doi:10.18453/rosdok_id00005463",
        "lexico": "DEMel, publicación de datos (CC BY-SA 4.0), doi:10.18453/rosdok_id00005462"}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"meta": meta, "folios": folios, "lemmas": lemmas}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
tot = sum(len(v) for f in folios for v in f["lines"])
print("folios:", len(folios), "| versos:", sum(len(f["lines"]) for f in folios), "| tokens:", tot)
print("anotadas por el DEMel:", n_ver)
for k, v in cnt.most_common(): print(f"  {k}: {v}")
print("lemas usados:", len(lemmas), "(sintéticos:", len(SINT), ")")
if not ALT_OUT: open(f"{H}/web/data/cid.js", "w", encoding="utf-8").write("window.HYS_CID=" + open(OUT, encoding="utf-8").read() + ";")
print("tamaño cid.json:", round(os.path.getsize(OUT)/1e6, 2), "MB")
print("folios ej:", [f["n"] for f in folios[:4]], "... último:", folios[-1]["n"])
