"""Genera los datos de una obra para el lector: web/data/<obra>.js (y web/data/<obra>.json de trabajo)
y el resumen web/data/obras.js que usa la página de inicio.

 - Palabras con <seg corresp="obj:demel_d..."> en el TEI: lema verificado por el DEMel (v=1).
 - Resto de las palabras: tabla manual, frecuencia, forma única, segmentación o terminación (ver lematizador.py).
Uso:  python3 scripts/build_obra.py [cid | oria | todas]        (sin argumento: todas)
Variable HYS_OUT=ruta.json: construir UNA obra sin tablas manuales y sin tocar la web (la usa proponer_manuales.py).
Para agregar una obra: sumar una entrada a OBRAS (TEI, recorte, meta), crear datos/manual/<obra>.csv y sumar su
tarjeta en la página de inicio (index.html).
Texto: DEMel, corpus de textos (CC BY-SA 4.0), doi:10.18453/rosdok_id00005463. Léxico: doi:10.18453/rosdok_id00005462.
"""
import csv, html, json, re, collections, os, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
H = str(AQUI.parent)                      # raíz del repositorio (funciona en cualquier carpeta)
sys.path.insert(0, str(AQUI))
import lematizador
LZ = lematizador

A_DOI_TXT = '<a href="https://doi.org/10.18453/rosdok_id00005463">doi:10.18453/rosdok_id00005463</a>'
OBRAS = {
    "cid": {
        "tei": "t0103", "docs": "cid_documentaciones.csv", "recorte": None,
        "meta": {"obra": "Cantar de mío Cid", "codice": "BNE, Vitr. 7-17", "autor": "Anónimo", "sigla": "Cid(ADMYTE 0)", "datacion": "c 1140?",
                 "periodo": "Original hacia 1140 · copia de 1300-1400",
                 "edicion": "Anónimo, Cantar de mío Cid. Madrid: Nacional, Vitrina 7-17, copiado 1300-1400. Transcr. Steven Kirby. In: ADMYTE 0.",
                 "texto": "DEMel, corpus de textos t0103 (CC BY-SA 4.0), doi:10.18453/rosdok_id00005463",
                 "lexico": "DEMel, publicación de datos (CC BY-SA 4.0), doi:10.18453/rosdok_id00005462",
                 "fuente_html": "Texto: <em>Cantar de mío Cid</em>, copia de 1300-1400 (BNE, Vitrina 7-17), transcripción de Steven Kirby en ADMYTE 0, tomada del corpus de textos del DEMel (" + A_DOI_TXT + ")."},
    },
    "oria": {
        "tei": "t0120", "docs": "santa_oria_documentaciones.csv",
        # el TEI de Berceo es un solo bloque: la Vida de Santa Oria va desde el folio 48v hasta su Amén final
        "recorte": ("48v", "nunca ueamos mal Amen"),
        "meta": {"obra": "Vida de Santa Oria", "codice": "RAE, Ms. 4 (códice F)", "autor": "Gonzalo de Berceo", "sigla": "Berceo(Baranowski)", "datacion": "c 1230-c 1256",
                 "periodo": "Siglo XIII",
                 "edicion": "Gago Jover, Francisco (ed.). 2011. «Obras de Gonzalo de Berceo». Spanish Poetic Texts. Digital Library of Old Spanish Texts. Hispanic Seminary of Medieval Studies.",
                 "texto": "DEMel, corpus de textos t0120 (CC BY-SA 4.0), doi:10.18453/rosdok_id00005463",
                 "lexico": "DEMel, publicación de datos (CC BY-SA 4.0), doi:10.18453/rosdok_id00005462",
                 "fuente_html": "Texto: <em>Vida de Santa Oria</em>, de Gonzalo de Berceo, según la edición de Francisco Gago Jover, «Obras de Gonzalo de Berceo» (2011), Spanish Poetic Texts, Hispanic Seminary of Medieval Studies (dominio público), tomada del corpus de textos del DEMel, texto t0120 (" + A_DOI_TXT + "). Se muestra el pasaje de esa edición que corresponde a este poema (fols. 48v-60r), sin las demás obras de Berceo ni el epitafio final. Las fechas del DEMel para las obras de Berceo son c. 1230-c. 1256."},
    },
    "reyes": {
        "tei": "t0006", "docs": "t0006_documentaciones.csv", "recorte": None,
        "meta": {"obra": "Auto de los Reyes Magos", "codice": "BNE (ex Catedral de Toledo, 6-8)", "autor": "Anónimo", "sigla": "AutoReyesMagos(CEM)", "datacion": "c 1180",
                 "periodo": "Hacia 1180",
                 "edicion": "Auto de los Reyes Magos, in: Crestomatía del español medieval, por Ramón Menéndez Pidal con la colaboración del Centro de Estudios Históricos, acabada y revisada por Rafael Lapesa y María Soledad de Andrés, vol. I, Madrid 1971, 71-77.",
                 "texto": "DEMel, corpus de textos t0006 (CC BY-SA 4.0), doi:10.18453/rosdok_id00005463",
                 "lexico": "DEMel, publicación de datos (CC BY-SA 4.0), doi:10.18453/rosdok_id00005462",
                 "fuente_html": "Texto: <em>Auto de los Reyes Magos</em> (hacia 1180), según la edición de la <em>Crestomatía del español medieval</em> de Ramón Menéndez Pidal (con el Centro de Estudios Históricos; rev. de Rafael Lapesa y María Soledad de Andrés, 1971, pp. 71-77), tomada del corpus de textos del DEMel, texto t0006 (" + A_DOI_TXT + "). Las acotaciones con el nombre de quien habla no se muestran. La numeración de folios es la de las páginas de la edición impresa."},
    },
    "millan": {
        "tei": "t0120", "docs": "t0120_documentaciones.csv",
        "recorte": ("61r", None, "66r"),
        "meta": {"obra": "Vida de San Millán (fragmento)", "codice": "RAE, Ms. 4 (códice F)", "autor": "Gonzalo de Berceo", "sigla": "Berceo(Baranowski)", "datacion": "c 1230-c 1256",
                 "periodo": "Siglo XIII",
                 "edicion": "Gago Jover, Francisco (ed.). 2011. «Obras de Gonzalo de Berceo». Spanish Poetic Texts. Digital Library of Old Spanish Texts. Hispanic Seminary of Medieval Studies.",
                 "texto": "DEMel, corpus de textos t0120 (CC BY-SA 4.0), doi:10.18453/rosdok_id00005463",
                 "lexico": "DEMel, publicación de datos (CC BY-SA 4.0), doi:10.18453/rosdok_id00005462",
                 "fuente_html": "Texto: <em>Vida de San Millán</em>, de Gonzalo de Berceo, según la edición de Francisco Gago Jover, «Obras de Gonzalo de Berceo» (2011), Spanish Poetic Texts, Hispanic Seminary of Medieval Studies (dominio público), tomada del corpus de textos del DEMel, texto t0120 (" + A_DOI_TXT + "). Se muestra el fragmento de este poema que contiene esa edición (fols. 61r-65v; la edición del corpus es parcial y marca los saltos con [...]), sin las demás obras de Berceo. Las fechas del DEMel para las obras de Berceo son c. 1230-c. 1256."},
    },
    "domingo": {
        "tei": "t0120", "docs": "t0120_documentaciones.csv",
        "recorte": ("66r", None, None),
        "meta": {"obra": "Vida de Santo Domingo de Silos", "codice": "RAE, Ms. 4 (códice F)", "autor": "Gonzalo de Berceo", "sigla": "Berceo(Baranowski)", "datacion": "c 1230-c 1256",
                 "periodo": "Siglo XIII",
                 "edicion": "Gago Jover, Francisco (ed.). 2011. «Obras de Gonzalo de Berceo». Spanish Poetic Texts. Digital Library of Old Spanish Texts. Hispanic Seminary of Medieval Studies.",
                 "texto": "DEMel, corpus de textos t0120 (CC BY-SA 4.0), doi:10.18453/rosdok_id00005463",
                 "lexico": "DEMel, publicación de datos (CC BY-SA 4.0), doi:10.18453/rosdok_id00005462",
                 "fuente_html": "Texto: <em>Vida de Santo Domingo de Silos</em>, de Gonzalo de Berceo, según la edición de Francisco Gago Jover, «Obras de Gonzalo de Berceo» (2011), Spanish Poetic Texts, Hispanic Seminary of Medieval Studies (dominio público), tomada del corpus de textos del DEMel, texto t0120 (" + A_DOI_TXT + "). Se muestra el pasaje de esa edición que corresponde a este poema (fols. 66r-113v), sin las demás obras de Berceo. Las fechas del DEMel para las obras de Berceo son c. 1230-c. 1256."},
    },
}

fold = lambda s: s.replace("v","u").replace("j","i").replace("y","i").replace("ç","z").replace("ſ","s").replace("ph","f")
LET = "a-záéíóúñçüſ"
ALT_OUT = os.environ.get("HYS_OUT")      # si está definida: construir sin tablas manuales y sin tocar la web
pedidas = [a for a in sys.argv[1:] if not a.startswith("-")] or ["todas"]
nombres = list(OBRAS) if "todas" in pedidas else pedidas
for n in nombres:
    if n not in OBRAS: sys.exit("Obra desconocida: %s (las que hay: %s)" % (n, ", ".join(OBRAS)))
if ALT_OUT and len(nombres) != 1: sys.exit("Con HYS_OUT hay que indicar una sola obra.")

# --- DEMel: lemario e índice de formas (comunes a todas las obras)
lemario = {r["lemmaId"]: r for r in csv.DictReader(open(f"{H}/datos/lemario.csv", encoding="utf-8"))}
fidx = collections.defaultdict(dict)     # forma plegada -> {lemmaId: n}
lemma_forms = collections.defaultdict(collections.Counter)
for r in csv.DictReader(open(f"{H}/datos/formas_indice.csv", encoding="utf-8")):
    n = int(r["n"]); fidx[fold(r["forma"])][r["lemmaId"]] = fidx[fold(r["forma"])].get(r["lemmaId"], 0) + n
    lemma_forms[r["lemmaId"]][r["forma"]] += n

NAMEIDX = LZ.build_index(lemario.values())
VERBOS = {lid for lid, r in lemario.items() if any(c.startswith("verb") for c in r["categorias"].split("|"))}
NOM = LZ.indice_nombres(lemario.values())
MAN_COM = {} if ALT_OUT else LZ.cargar_manual(f"{H}/datos/manual/comunes.csv")
TOK = re.compile(r"<pb[^>]*?n=\"([^\"]+)\"[^>]*/>|<seg\b([^>]*)>|</seg>|<[^>]+>|[^<\s]+")

def construir(obra, cfg):
    OUT = ALT_OUT or f"{H}/web/data/{obra}.json"
    fdocs = Path(f"{H}/datos/{cfg['docs']}")
    if fdocs.exists(): att = {r["id"]: r for r in csv.DictReader(open(fdocs, encoding="utf-8"))}
    else:
        att = {}
        print("AVISO: falta datos/%s (python3 scripts/extract_documentaciones.py): se construye sin las anotaciones del DEMel." % cfg["docs"])
    MAN_OBRA = {} if ALT_OUT else LZ.cargar_manual(f"{H}/datos/manual/{obra}.csv")
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
    body = open(f"{H}/Mueller_Corpus_2026_data/texts/tei/demel_{cfg['tei']}.tei.xml", encoding="utf-8").read()
    body = body[body.index("<body"):body.index("</body>")]
    if cfg["recorte"]:
        ini, fin_txt, *resto = cfg["recorte"]
        a = re.search(r'<pb[^>]*n="%s"[^>]*/>' % re.escape(ini), body).start()
        if fin_txt:                                         # termina en la línea que contiene fin_txt
            b = body.index("\n", body.index(fin_txt, a))
        elif resto and resto[0]:                            # termina donde empieza otro folio (pb)
            b = re.search(r'<pb[^>]*n="%s"[^>]*/>' % re.escape(resto[0]), body[a:]).start() + a
        else:
            b = len(body)
        body = body[a:b]
    body = re.sub(r"<speaker>.*?</speaker>", "", body, flags=re.S)
    folios, cur, verse = [], None, []
    seg_ids = []
    def flush():
        nonlocal verse
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
    meta = dict(cfg["meta"], id=obra)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"meta": meta, "folios": folios, "lemmas": lemmas}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    tot = sum(len(v) for f in folios for v in f["lines"])
    print(f"== {obra}: {meta['obra']}")
    print("folios:", len(folios), "| versos:", sum(len(f["lines"]) for f in folios), "| tokens:", tot)
    print("anotadas por el DEMel:", n_ver)
    for k, v in cnt.most_common(): print(f"  {k}: {v}")
    print("lemas usados:", len(lemmas), "(sintéticos:", len(SINT), ")")
    if not ALT_OUT:
        js = f"{H}/web/data/{obra}.js"
        open(js, "w", encoding="utf-8", newline="\n").write('window.HYS_DATA=window.HYS_DATA||{};window.HYS_DATA["%s"]=' % obra + open(OUT, encoding="utf-8").read() + ";")
    print("tamaño %s.json: %s MB" % (obra, round(os.path.getsize(OUT)/1e6, 2)))
    print("folios ej:", [f["n"] for f in folios[:4]], "... último:", folios[-1]["n"])

for n in nombres: construir(n, OBRAS[n])

def resumen():
    """web/data/obras.js: lo que necesita la página de inicio (sin cargar los textos enteros)."""
    out = []
    for obra in OBRAS:
        p = Path(f"{H}/web/data/{obra}.js")
        if not p.exists(): continue
        d = json.loads(p.read_text(encoding="utf-8").partition('"]=')[2].rstrip().rstrip(";"))
        m = d["meta"]
        pal = sum(1 for f in d["folios"] for v in f["lines"] for t in v if re.search(f"[{LET}]", t["w"], re.I))
        out.append({"id": obra, "titulo": m["obra"], "autor": m.get("autor", ""), "periodo": m.get("periodo", ""), "codice": m.get("codice", ""),
                    "versos": sum(len(f["lines"]) for f in d["folios"]), "folios": len(d["folios"]), "palabras": pal})
    open(f"{H}/web/data/obras.js", "w", encoding="utf-8", newline="\n").write("window.HYS_OBRAS=" + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")
    print("obras.js:", ", ".join("%s (%d versos)" % (o["id"], o["versos"]) for o in out))
if not ALT_OUT: resumen()
