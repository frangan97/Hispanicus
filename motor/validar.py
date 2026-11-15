"""Mide el motor contra los lemas del Cid: para cada lema con étimo latino (columna `etimo` de
datos/evolucion_wiktionary_prioritarios.csv) deriva la forma medieval y la actual y las compara con
(a) el nombre del lema en el DEMel (forma moderna/normalizada) y
(b) las formas gráficas documentadas del lema (datos/formas_indice.csv).
Las comparaciones usan un «esqueleto» que absorbe variantes gráficas (b/v/u, ç/z/c, ss/s, y/i, h-, -e final).
Uso: python3 validar.py [--detalle]"""
import csv, re, sys, unicodedata, collections
from pathlib import Path
from motor_fonetico import derivar, adaptacion_culta

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"


def plano(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c) or c == "̃").replace("ſ", "s")


def esqueleto(s):
    s = plano(s).replace("ñ", "N")
    s = unicodedata.normalize("NFC", s)
    s = s.replace("ph", "f").replace("v", "u").replace("b", "u").replace("j", "i").replace("y", "i")
    s = s.replace("ç", "z").replace("c", "z").replace("g", "z") if False else s.replace("ç", "z")
    s = re.sub(r"c(?=[ei])", "z", s).replace("ch", "X").replace("c", "k").replace("qu", "k")
    s = s.replace("ll", "L").replace("nn", "N").replace("ss", "s").replace("x", "X")
    s = re.sub(r"^h", "f", s) if False else s
    s = re.sub(r"^[fh](?=[aeiouyu])", "H", s)
    s = re.sub(r"(?<=[^aeiou])e$", "", s)
    s = s.replace("w", "u").replace("z", "z")
    return s


def nombre_simple(lema):
    p = lema.split(" / ")[0]
    p = re.sub(r"[\[\]]", "", p).strip()
    p = re.sub(r"\s+\d+$", "", p)
    p = re.sub(r",\s*(a|as)$", "", p)
    p = re.sub(r"\(se\)$", "", p).strip()
    return p


def cargar():
    filas = list(csv.DictReader(open(DATOS / "evolucion_wiktionary_prioritarios.csv", encoding="utf-8-sig"), delimiter=";"))
    ids = {}
    for r in csv.DictReader(open(DATOS / "lemas_resumen.csv", encoding="utf-8")):
        ids[r["lemma"]] = r["lemmaId"]
    formas = collections.defaultdict(set)
    ids_necesarios = set(ids.values())
    for r in csv.DictReader(open(DATOS / "formas_indice.csv", encoding="utf-8-sig")):
        if r["lemmaId"] in ids_necesarios:
            formas[r["lemmaId"]].add(r["forma"].lstrip("*"))
    return filas, ids, formas


def main(detalle=False, csv_salida=None):
    filas, ids, formas = cargar()
    tot = con_derivacion = ok_moderno = ok_medieval = ok_alguno = 0
    ambiguos = 0
    cultos = []
    filas_out = []
    sin_latin = []
    fallos = []
    aciertos = []
    for r in filas:
        et = (r["etimo"] or "").strip()
        if not et:
            continue
        primero = et.split(" | ")[0]
        if ":" in primero or " " in primero.strip():
            sin_latin.append((r["lemma"], et)); continue
        tot += 1
        ds, motivo = derivar(primero)
        if not ds:
            sin_latin.append((r["lemma"], et)); continue
        con_derivacion += 1
        nombre = nombre_simple(r["lemma"])
        atest = formas.get(ids.get(r["lemma"]), set()) | {nombre}
        sk_atest = {esqueleto(f) for f in atest}
        sk_mod = {esqueleto(d.actual) for d in ds}
        sk_med = {esqueleto(d.medieval) for d in ds}
        bien_mod = esqueleto(nombre) in sk_mod
        bien_med = bool(sk_med & sk_atest)
        culto, _ = adaptacion_culta(primero)
        es_culto = bool(culto) and not (bien_mod or bien_med) and esqueleto(culto) in (sk_atest | {esqueleto(nombre)})
        if es_culto:
            cultos.append((r["lemma"], primero, culto))
        if len(ds) > 1:
            ambiguos += 1
        ok_moderno += bien_mod; ok_medieval += bien_med; ok_alguno += (bien_mod or bien_med)
        info = (r["lemma"], primero, [(d.medieval, d.actual) for d in ds], sorted(atest)[:6])
        estado = "regular" if (bien_mod or bien_med) else ("cultismo (propuesto)" if es_culto else "sin explicar")
        filas_out.append({"lema": r["lemma"], "etimo": primero, "estado": estado,
                          "motor_medieval": " / ".join(dict.fromkeys(d.medieval for d in ds)),
                          "motor_actual": " / ".join(dict.fromkeys(d.actual for d in ds)),
                          "candidatos": len(ds), "adaptacion_culta": culto or "",
                          "formas_documentadas": " ; ".join(sorted(atest)[:8])})
        (aciertos if (bien_mod or bien_med) else fallos).append(info)
    print(f"Lemas con étimo latino de una sola palabra: {tot}")
    print(f"  con derivación posible: {con_derivacion}   (sin derivar: {len(sin_latin)})")
    print(f"  coincide con el lema moderno: {ok_moderno}   coincide con forma medieval documentada: {ok_medieval}")
    print(f"  alguna de las dos: {ok_alguno} ({100*ok_alguno//max(con_derivacion,1)} %)   derivaciones con ambigüedad: {ambiguos}")
    print(f"  no coincide la vía patrimonial pero sí la adaptación culta (¿cultismo?): {len(cultos)}")
    print(f"  sin explicar: {len(fallos) - len(cultos)}")
    if detalle:
        print("\n— CULTISMOS PROPUESTOS —")
        for c in cultos: print("  ~", c)
    if detalle:
        print("\n— ACIERTOS —")
        for a in aciertos: print("  ✓", a[0], a[1], a[2][:2])
        print("\n— FALLOS —")
        for f in fallos: print("  ✗", f[0], "|", f[1], "|", f[2][:3], "| documentadas:", f[3])
    if csv_salida:
        with open(csv_salida, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(filas_out[0].keys()), delimiter=";")
            w.writeheader(); w.writerows(filas_out)
    return fallos, aciertos


if __name__ == "__main__":
    salida = sys.argv[sys.argv.index("--csv") + 1] if "--csv" in sys.argv else None
    main("--detalle" in sys.argv, salida)
