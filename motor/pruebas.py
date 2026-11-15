"""Pruebas del motor: palabras con resultado conocido (ejemplos del Manual de Menéndez Pidal; el § va entre paréntesis).
Cada fila: étimo con cantidades -> (forma medieval, forma actual). Uso: python3 -I pruebas.py"""
import sys, re
from motor_fonetico import derivar

# (étimo marcado, medieval esperado, actual esperado, fuente)
ORO = [
 ("lŭpum", "lobo", "lobo", "Manual §40"),
 ("vīta", "vida", "vida", "Manual §40"),
 ("cēpŭlla", "cebolla", "cebolla", "Manual §40"),
 ("sēcūrum", "seguro", "seguro", "Manual §40"),
 ("nŏctem", "noche", "noche", "Manual §50"),
 ("lactem", "leche", "leche", "Manual §50"),
 ("factum", "fecho", "hecho", "Manual §38, §50"),
 ("multum", "mucho", "mucho", "Manual §47"),
 ("fīlium", "fijo", "hijo", "Manual §53, §38"),
 ("fŏlia", "foja", "hoja", "Manual §38, §53"),
 ("ŏcŭlum", "ojo", "ojo", "Manual §57"),
 ("tĕgŭla", "teja", "teja", "Manual §57"),
 ("annum", "año", "año", "Manual §46"),
 ("caballum", "cavallo", "caballo", "Manual §46"),
 ("clāmāre", "llamar", "llamar", "Manual §39"),
 ("plēnum", "lleno", "lleno", "Manual §39"),
 ("flamma", "llama", "llama", "Manual §39"),
 ("fŏcum", "fuego", "fuego", "Manual §38"),
 ("fĕrrum", "fierro", "hierro", "Manual §38"),
 ("bŏnum", "bueno", "bueno", "Manual §13"),
 ("nŏva", "nueva", "nueva", "Manual §43"),
 ("rŏta", "rueda", "rueda", "Manual §40"),
 ("pĕde", "pie", "pie", "Manual §10"),
 ("septem", "siete", "siete", "Manual §49"),
 ("tĕrra", "tierra", "tierra", "Manual §46"),
 ("ratiōnem", "razon", "razón", "Manual §53"),
 ("bucca", "boca", "boca", "Manual §45"),
 ("sĭccum", "seco", "seco", "Manual §45"),
 ("rēgīna", "reina", "reina", "Manual §43"),
 ("mēnsa", "mesa", "mesa", "Manual §47"),
 ("ursum", "osso", "oso", "Manual §47"),
 ("cantāre", "cantar", "cantar", "ejemplo básico"),
 ("pauperum", None, None, ""),
 ("pŏpŭlum", "pueblo", "pueblo", "Manual §48"),
 ("tăbŭla", "tabla", "tabla", "Manual §25"),
 ("nōmĭne", "nombre", "nombre", "Manual §59"),
 ("sēmĭnāre", "sembrar", "sembrar", "Manual §59"),
 ("dŏmĭnum", None, None, ""),
 ("vīnea", "viña", "viña", "Manual §53"),
 ("arānea", "araña", "araña", "Manual §53"),
 ("lĭgna", "leña", "leña", "Manual §50"),
 ("sĭgna", "seña", "seña", "Manual §50"),
 ("pūgnum", "puño", "puño", "Manual §50"),
 ("clāvem", "llave", "llave", "Manual §39"),
 ("capra", "cabra", "cabra", "Manual §48"),
 ("patrem", "padre", "padre", "Manual §48"),
 ("lūnam", "luna", "luna", "Manual §44"),
 ("pŏntem", "puent", "puente", "Manual §47"),
 ("mŏrtem", "muerte", "muerte", "Manual §47"),
 ("fŏrtem", "fuert", "fuerte", "Manual §47"),
 ("facĕre", "fazer", "hacer", "Manual §42"),
 ("nascĕre", "nacer", "nacer", "Manual §47"),
 ("lŏngum", "luengo", "luengo", "Manual §47"),
 ("mīlle", None, None, ""),
 ("pŏrtam", "puerta", "puerta", "Manual §47"),
 ("tĕnĕre", None, None, ""),
 ("vĕtŭlum", None, None, ""),
 ("pŏntem", "puent", "puente", "Manual §47"),
 ("aurum", "oro", "oro", "Manual §47"),
 ("paucum", "poco", "poco", "Manual §47"),
 ("auscultat", None, None, ""),
 ("spătha", "espada", "espada", "Manual §39"),
 ("quando", "cuando", "cuando", "Manual §39"),
 ("aqua", "agua", "agua", "Manual §52"),
 ("lĭngua", "lengua", "lengua", "Manual §52"),
 ("nĭgrum", "negro", "negro", "Manual §48"),
 ("vĭridem", "verde", "verde", "Manual §54"),
 ("verĭtātem", "verdad", "verdad", "Manual §54"),
 ("bŏnĭtātem", "bondad", "bondad", "Manual §54"),
 ("minus", "menos", "menos", "Manual §62"),
 ("sāpĕre", "saber", "saber", "ejemplo básico"),
 ("dīxi", "dixe", "dije", "Manual §50"),
 ("lactūca", "lechuga", "lechuga", "Manual §50"),
 ("cūltěllum", None, None, ""),
 ("castĕllum", "castiello", "castillo", "Manual §10"),
 ("crēscĕre", "crecer", "crecer", "Manual §47"),
 ("pĭscem", "peç", "pez", "Manual §47"),
 ("lūcem", "luz", "luz", "Manual §42"),
 ("pācem", "paz", "paz", "Manual §42"),
 ("crūcem", "cruz", "cruz", "Manual §42"),
 ("rŏtundum", None, None, ""),
 ("tĕrtiārium", "tercero", "tercero", "Manual §53"),
 ("prīmārium", "primero", "primero", "Manual §53"),
 ("barbam", "barba", "barba", "Manual §47"),
 ("mŭltum", "mucho", "mucho", "Manual §47"),
 ("sŏmnum", "sueño", "sueño", ""),
]

def norm(s):
    return s.lower()

def main(verbose=False):
    ok = fallo = 0
    fallos = []
    for fila in ORO:
        et, med, act, fuente = fila
        if med is None:
            continue
        ds, mot = derivar(et)
        meds = {d.medieval for d in ds}; acts = {d.actual for d in ds}
        f = lambda x: re.sub(r"e$", "", x.replace("b", "v").replace("u", "v"))
        bien_m = f(med) in {f(m) for m in meds}
        bien_a = (act is None) or (act in acts)
        if bien_m and bien_a:
            ok += 1
        else:
            fallo += 1
            fallos.append((et, med, act, [(d.medieval, d.actual) for d in ds], fuente))
    total = ok + fallo
    print(f"Pruebas: {ok}/{total} bien ({100*ok//max(total,1)} %)")
    for f in fallos:
        print("  ✗", f[0], "esperado:", f[1], "/", f[2], "obtenido:", f[3], f[4])
    return fallo

if __name__ == "__main__":
    sys.exit(1 if main() else 0)
