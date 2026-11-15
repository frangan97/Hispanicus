"""Precálculo para la página: de un étimo latino a la cadena (latín > latín vulgar > romance > medieval > actual)
y la lista breve de cambios, SOLO si la derivación queda corroborada por formas documentadas.

Política (regla de oro del proyecto: no se inventa nada):
  - La derivación se muestra únicamente si su forma actual coincide con el lema, o si su forma medieval
    coincide con una forma documentada del lema (esqueleto gráfico de tabla.esq).
  - Si no hay coincidencia, devuelve None: la página queda con «Origen etimológico posible».
  - El resultado nunca es «verificado»: eso sólo lo decide la hoja de verificación con su fuente.
"""
import re
from motor_fonetico import derivar
from tabla import esq


def nombre_simple(lema):
    p = lema.split(" / ")[0]
    p = re.sub(r"[\[\]]", "", p).strip()
    p = re.sub(r"\s+\d+$", "", p)
    p = re.sub(r",\s*(a|as)$", "", p)
    return re.sub(r"\(se\)$", "", p).strip()


def derivacion_corroborada(etimo, lema, formas=()):
    """Devuelve (Derivacion, por_que) o (None, motivo). `etimo`: una sola palabra latina."""
    if not etimo or ":" in etimo or " " in etimo.strip() or " | " in etimo:
        return None, "étimo no latino o múltiple"
    ds, motivo = derivar(etimo.strip())
    if not ds:
        return None, motivo or "sin derivación"
    nombre = nombre_simple(lema)
    sk_form = {esq(f.lstrip("*")) for f in formas} | {esq(nombre)}
    por_actual = [d for d in ds if esq(d.actual) == esq(nombre)]
    por_med = [d for d in ds if esq(d.medieval) in sk_form]
    if por_actual:
        return por_actual[0], "coincide con el lema actual"
    if por_med:
        # la forma medieval coincide pero la actual no: no se muestra (puede ser cultismo o falsa coincidencia)
        return None, "sólo coincide la forma medieval; la actual difiere del lema (¿cultismo?)"
    return None, "no coincide con el lema ni con formas documentadas"


CORTO = {  # nombre breve de cada cambio para mostrar en la página; la fuente va aparte
}


def cambios_cortos(d):
    out, vistos = [], set()
    for p in d.traza:
        if p.regla == "vulgar" or p.etapa == "variante" or p.regla in vistos:
            continue
        vistos.add(p.regla)
        out.append(f"{p.nombre} ({p.antes} > {p.despues})")
    return out


def fuentes_motor(d):
    return sorted({p.fuente for p in d.traza if p.regla != "vulgar" and p.etapa != "variante" and p.fuente})
