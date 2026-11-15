"""Puente entre la tabla curada y el motor.

1. validar_fila(): compara lo que dice la tabla (forma medieval / actual) con lo que deriva el motor y
   clasifica: regular | semicultismo (propuesto) | cultismo (propuesto) | sin_explicar. Nunca corrige la tabla:
   sólo avisa y muestra dónde se separan las formas (la tabla manda; el motor audita).
2. a_formato_evolucion(): arma el objeto que lee la página (web/data/evolucion.js): cadena, cambios, fuentes.
3. exportar_reglas(): reglas.json con nombre, etapa, fuente y ejemplo de cada regla (para la interfaz y el PDF).
"""
import csv, json, re, sys, unicodedata
from pathlib import Path
from motor_fonetico import derivar, adaptacion_culta, REG, R

def _plano(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c) or c == "̃")

def esq(s):
    """Esqueleto gráfico: absorbe b/v/u, c/ç/z, y/i/j, ss/s, h- y -e final (variantes de época)."""
    s = unicodedata.normalize("NFC", _plano(s))
    s = s.replace("ñ", "N").replace("ç", "z")
    s = re.sub(r"c(?=[ei])", "z", s)
    s = s.replace("ph", "f").replace("ch", "X").replace("qu", "k").replace("c", "k")
    s = s.replace("v", "u").replace("b", "u").replace("j", "i").replace("y", "i").replace("w", "u")
    s = s.replace("ll", "L").replace("nn", "N").replace("ss", "s").replace("x", "X")
    s = re.sub(r"^[fh](?=[aeiou])", "H", s)
    return re.sub(r"(?<=[^aeiou])e$", "", s)

def _distancia(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def validar_fila(etimo, medieval="", actual=""):
    """Devuelve dict(estado, candidato, avisos, diferencia, traza). `etimo` debe llevar las cantidades (ĕ, ŏ, ā…) siempre que se sepan."""
    objetivos = {esq(x) for x in (medieval, actual) if x}
    ds, motivo = derivar(etimo)
    if not ds:
        return {"estado": "no_aplica", "motivo": motivo, "candidato": None}
    def coincide(d):
        ok_m = (not medieval) or esq(d.medieval) == esq(medieval)
        ok_a = (not actual) or esq(d.actual) == esq(actual)
        return ok_m and ok_a
    exactos = [d for d in ds if coincide(d)]
    if exactos:
        d = exactos[0]
        sin_sync = any("sin síncopa" in a for a in d.avisos)
        return {"estado": "semicultismo (propuesto)" if sin_sync else "regular", "candidato": d, "avisos": d.avisos,
                "diferencia": None, "n_candidatos": len(ds)}
    culto, _ = adaptacion_culta(etimo)
    if culto and (esq(culto) in objetivos):
        return {"estado": "cultismo (propuesto)", "candidato": None, "culto": culto, "avisos": [],
                "diferencia": None, "n_candidatos": len(ds)}
    # el más cercano, para mostrar dónde se separan
    ref = esq(actual or medieval)
    mejor = min(ds, key=lambda d: _distancia(esq(d.actual if actual else d.medieval), ref))
    return {"estado": "sin_explicar", "candidato": mejor, "avisos": mejor.avisos,
            "diferencia": {"motor": (mejor.medieval, mejor.actual), "tabla": (medieval, actual)}, "n_candidatos": len(ds)}

def a_formato_evolucion(d, marca=None, estado="pendiente"):
    """Convierte una Derivacion en la entrada de evolucion.js."""
    cambios, vistos = [], set()
    for p in d.traza:
        if p.regla == "vulgar" or p.etapa == "variante":
            continue
        if p.regla in vistos:
            continue
        vistos.add(p.regla)
        cambios.append(f"{p.nombre} ({p.antes} > {p.despues}) [{p.fuente}]")
    return {
        "cadena": d.cadena,
        "cambios": cambios,
        "marca": marca,
        "fuentes": sorted({p.fuente for p in d.traza if p.regla != "vulgar" and p.etapa != "variante"}),
        "estado": estado,
        "nota": "Derivación calculada por el motor de reglas; no verificada contra la bibliografía." if estado != "verificado" else "",
    }

def exportar_reglas(destino):
    datos = [{"id": r.id, "etapa": r.etapa, "nombre": r.nombre, "fuente": r.fuente, "ejemplo": r.ejemplo} for r in R]
    Path(destino).write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(datos)

def validar_csv(ruta_entrada, ruta_salida):
    """Lee la tabla curada (`;`, UTF-8) con columnas lema;etimo;forma_medieval;forma_actual;... y escribe un informe CSV."""
    filas = list(csv.DictReader(open(ruta_entrada, encoding="utf-8-sig"), delimiter=";"))
    out = []
    for r in filas:
        res = validar_fila(r.get("etimo_marcado") or r.get("etimo", ""), r.get("forma_medieval", ""), r.get("forma_actual", ""))
        dif = res.get("diferencia")
        out.append({
            "lema": r.get("lema"), "etimo": r.get("etimo_marcado") or r.get("etimo"), "marca_tabla": r.get("marca", ""),
            "estado_motor": res["estado"],
            "motor_medieval": res["candidato"].medieval if res.get("candidato") else "",
            "motor_actual": res["candidato"].actual if res.get("candidato") else (res.get("culto") or ""),
            "tabla_medieval": r.get("forma_medieval", ""), "tabla_actual": r.get("forma_actual", ""),
            "avisos": " | ".join(res.get("avisos") or []),
        })
    with open(ruta_salida, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(out)
    return out

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        res = validar_csv(sys.argv[1], sys.argv[2])
        from collections import Counter
        print(Counter(r["estado_motor"] for r in res))
    else:
        print(exportar_reglas("reglas.json"), "reglas exportadas")
