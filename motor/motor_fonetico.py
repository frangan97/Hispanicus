"""Motor de reglas fonéticas de Hispanicus: del étimo latino al español medieval y actual.

Idea central: cada paso es una REGLA con nombre, fuente (párrafo del Manual de Menéndez Pidal o
capítulo de Ariza) y ejemplos. El motor las aplica en orden cronológico y guarda la traza
(forma antes -> forma después) para que la interfaz pueda mostrar cada cambio.

El motor NO inventa etimologías: parte del étimo que da la tabla curada. Cuando una regla no
alcanza (excepción léxica, cultismo, analogía) lo declara en `avisos` en vez de adivinar.

Notación interna (una letra por sonido, para poder escribir las reglas como expresiones regulares):
  vocales  a e i o u   y  E O  (e, o abiertas del latín vulgar: las que diptongan)
  '        marca la sílaba tónica; va ANTES de la vocal tónica
  k g p t b d f v  l m n r s z      (z = s sonora intervocálica; ss = s sorda doble)
  ç = ts   ʣ = dz   ʧ = ch   ʃ = x (medieval)   ʒ = j/g medieval   ʎ = ll   ɲ = ñ
  j = yod (semiconsonante)   w = semiconsonante u   θ = z/c actual   x = jota actual
"""
import re
import unicodedata
from dataclasses import dataclass, field

V = "aeiouEO"
VS = "'?[aeiouEO]"          # vocal, con o sin marca de tónica delante
ENCLITICAS_US = {"minus", "plus", "magis", "nisi", "tamen"}      # -us que NO es nominativo en -o


# ───────────────────────────── 1. Del latín escrito al latín vulgar ─────────────────────────────
LARGAS = {"ā": "a", "ē": "e", "ī": "i", "ō": "o", "ū": "u", "ȳ": "i"}
BREVES = {"ă": "a", "ĕ": "e", "ĭ": "i", "ŏ": "o", "ŭ": "u"}
ACUTAS = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u"}


@dataclass
class Tok:
    t: str            # 'V' o 'C'
    ch: str
    q: str = None     # 'L', 'S' o None (cantidad desconocida)
    ac: bool = False  # tónica marcada con acento agudo en la entrada


def normalizar_entrada(etimo):
    """Limpia el étimo. Devuelve (forma, avisos) o (None, [motivo]) si no es latín procesable."""
    avisos = []
    s = unicodedata.normalize("NFC", etimo.strip().lower()).replace("*", "")
    if not s or " " in s or any(c in s for c in "|:/,()"):
        return None, ["el étimo no es una sola palabra latina (varios étimos, frase o lengua no latina)"]
    if re.search(r"[^a-zāăēĕīĭōŏūŭȳáéíóú-]", s):
        return None, ["el étimo trae caracteres no latinos"]
    s = s.replace("-", "")
    # genitivo de 3.ª declinación (barōnis, nomĭnis, navis): se trabaja con la forma en -e
    if re.search(r"[ntrdc]is$", re.sub(r"[āăēĕīĭōŏūŭȳ]", lambda m: LARGAS.get(m.group(), BREVES.get(m.group(), "")), s)) \
            or s.endswith("navis"):
        s = s[:-2] + "e"
        avisos.append("terminación -is (genitivo) normalizada a -e: el romance sale del acusativo")
    # nominativos en -or, -ar, -al: el romance sale del acusativo/oblicuo (sapor > sapōrem: sabor; altar > altāre)
    plano0 = re.sub(r"[āăēĕīĭōŏūŭȳ]", lambda m: LARGAS.get(m.group(), BREVES.get(m.group(), "")), s)
    if len(re.sub(r"[^aeiou]", "", plano0)) >= 2 and not re.search(r"[āăēĕīĭōŏūŭȳáéíóú]$", s):
        for fin, nuevo_fin in (("or", "ōre"), ("ar", "āre"), ("al", "āle")):
            if plano0.endswith(fin) and not any(c in s[-3:] for c in "áéíóúāēīōū"):
                s = s[:-len(fin)] + nuevo_fin
                avisos.append(f"nominativo en -{fin} tratado como -{nuevo_fin} (acentuación del oblicuo)")
                break
    # nominativos que el romance toma del acusativo: -tas > -tatem, -tio > -tionem, -tudo > -tudinem
    for nom, acu in (("tas", "tate"), ("tio", "tione"), ("tudo", "tudine")):
        plano_ = re.sub(r"[āăēĕīĭōŏūŭȳ]", lambda m: LARGAS.get(m.group(), BREVES.get(m.group(), "")), s)
        if plano_.endswith(nom) and len(plano_) > 4:
            s = s[:len(s) - len(nom)] + acu
            avisos.append(f"-{nom} normalizado a -{acu}: el romance sale del acusativo")
            break
    s = re.sub(r"m$", "", s) if len(re.sub(r"[^aeiouāăēĕīĭōŏūŭȳáéíóú]", "", s)) > 1 else s
    return s, avisos


def tokenizar(s):
    toks, i, n = [], 0, len(s)
    def vocal_al(j):
        return j < n and (s[j] in "aeiouy" or s[j] in LARGAS or s[j] in BREVES or s[j] in ACUTAS)
    while i < n:
        c = s[i]
        # dígrafos de vocales
        if c in "ao" and i + 1 < n and s[i + 1] == "e" and c + "e" in ("ae", "oe"):
            toks.append(Tok("V", c + "e", "L")); i += 2; continue
        if c == "a" and i + 1 < n and s[i + 1] == "u":
            toks.append(Tok("V", "au", "L")); i += 2; continue
        if c in LARGAS: toks.append(Tok("V", LARGAS[c], "L")); i += 1; continue
        if c in BREVES: toks.append(Tok("V", BREVES[c], "S")); i += 1; continue
        if c in ACUTAS: toks.append(Tok("V", ACUTAS[c], None, ac=True)); i += 1; continue
        if c == "y": toks.append(Tok("V", "i")); i += 1; continue
        if c in "aeou" or c == "i":
            if c == "i":
                prev_v = toks and toks[-1].t == "V"
                if (i == 0 and vocal_al(i + 1)) or (prev_v and vocal_al(i + 1)):
                    toks.append(Tok("C", "j")); i += 1; continue
            toks.append(Tok("V", c)); i += 1; continue
        if c == "u":
            toks.append(Tok("V", "u")); i += 1; continue
        if c == "q" and i + 1 < n and s[i + 1] == "u":
            toks.append(Tok("C", "kw")); i += 2; continue
        if c == "g" and i + 1 < n and s[i + 1] == "u" and toks and toks[-1].ch == "n" and vocal_al(i + 2):
            toks.append(Tok("C", "gw")); i += 2; continue
        if c == "x": toks.append(Tok("C", "ks")); i += 1; continue
        if c == "h":
            i += 1; continue
        if c in "pcrt" and i + 1 < n and s[i + 1] == "h":
            toks.append(Tok("C", {"p": "f", "c": "k", "r": "r", "t": "t"}[c])); i += 2; continue
        toks.append(Tok("C", c)); i += 1
    # vocal ante vocal es breve en latín (vocalis ante vocalem corripitur) si no trae marca
    for k in range(len(toks) - 1):
        if toks[k].t == "V" and toks[k + 1].t == "V" and toks[k].q is None and toks[k].ch not in ("ae", "oe", "au"):
            toks[k].q = "S"
    return toks


def peso_tras(toks, k):
    """Peso de la sílaba cuya vocal está en toks[k]: nº de consonantes hasta la próxima vocal (muta cum liquida = 1)."""
    cons = []
    j = k + 1
    while j < len(toks) and toks[j].t == "C":
        cons.append(toks[j].ch); j += 1
    if j >= len(toks):            # final de palabra: no cuenta para el acento
        return 0
    n = sum(2 if c == "ks" else (2 if c == "j" else 1) for c in cons)
    if len(cons) == 2 and cons[0] in "ptkcbdgf" and cons[1] in "lr":
        n = 1
    return n


def candidatos_acento(toks, etimo_limpio):
    """Devuelve lista de (índice_de_vocal_tónica_en_toks, aviso|None)."""
    vs = [k for k, t in enumerate(toks) if t.t == "V"]
    if not vs:
        return []
    marcadas = [k for k in vs if toks[k].ac]
    if marcadas:
        return [(marcadas[0], None)]
    if len(vs) == 1:
        return [(vs[0], None)]
    if len(vs) == 2:
        return [(vs[0], None)]
    pen, ante = vs[-2], vs[-3]
    # infinitivos en -ere (breve): el romance acentúa la penúltima por analogía con -ēre (verbos de la 3.ª conj.)
    if etimo_limpio.endswith("ere"):
        return [(pen, "infinitivo en -ere: tónica en la penúltima por analogía con -ēre (Manual, conjugación)")]
    t = toks[pen]
    pw = peso_tras(toks, pen)
    if t.q == "L" or t.ch in ("ae", "oe", "au") or pw >= 2:
        return [(pen, None)]
    if t.q == "S":
        return [(ante, None)]
    return [(pen, "cantidad de la penúltima desconocida: se supuso larga (poner macrón/breve en la tabla)"),
            (ante, "cantidad de la penúltima desconocida: se supuso breve (poner macrón/breve en la tabla)")]


def calidad_vocal(tok, tonica, cerrada, hay_final, sig=""):
    """Vocal del latín vulgar. Devuelve lista de (vocal, aviso|None). `sig` = consonantes que siguen."""
    ch, q = tok.ch, tok.q
    if q is None and sig in ("ns", "nf"):
        q = "L"                                       # vocal larga ante ns, nf (alargamiento compensatorio)
    if ch == "u" and sig == "lt":
        return [("u", None)]                          # ŭlt > uit > uch (Manual §47): se conserva u
    if ch == "ae": return [("E" if tonica else "e", None)]
    if ch == "oe": return [("e", None)]
    if ch == "au": return [("au", None)]
    if ch == "a": return [("a", None)]
    pares = {"e": ("e", "E"), "i": ("i", "e"), "o": ("o", "O"), "u": ("u", "o")}[ch]   # (larga, breve)
    if q == "L": return [(pares[0], None)]
    if q == "S": return [(pares[1], None)]
    if not tonica:
        return [(pares[1] if ch in "eo" else pares[0], None)] if ch in "eo" else [(ch, None)]
    if cerrada:
        return [(pares[1], f"vocal tónica «{ch}» en sílaba cerrada sin marca de cantidad: se supuso breve")]
    return [(pares[0], f"cantidad de «{ch}» tónica desconocida: se probó larga"),
            (pares[1], f"cantidad de «{ch}» tónica desconocida: se probó breve")]


def a_latin_vulgar(etimo):
    """Genera candidatos de latín vulgar. Devuelve [(cadena_interna, avisos)]."""
    s, avisos0 = normalizar_entrada(etimo)
    if s is None:
        return [], avisos0
    toks = tokenizar(s)
    limpio = "".join(LARGAS.get(c, BREVES.get(c, ACUTAS.get(c, c))) for c in s)
    if limpio.endswith("ere"):
        vs0 = [k for k, t in enumerate(toks) if t.t == "V"]
        toks[vs0[-2]].q = "L"                       # -ĕre > -ēre (cambio de conjugación)
    out = []
    for k_ton, av_ac in candidatos_acento(toks, limpio):
        vs = [k for k, t in enumerate(toks) if t.t == "V"]
        # combinaciones de calidad para la tónica (las átonas son deterministas)
        variantes = [("", [])]
        cadenas = [[]]
        avs = [[]]
        for k, t in enumerate(toks):
            if t.t == "C":
                cadenas = [c + [("C", t.ch)] for c in cadenas]; continue
            es_ton = (k == k_ton)
            pos = vs.index(k)
            final = pos == len(vs) - 1
            sig, jj = "", k + 1
            while jj < len(toks) and toks[jj].t == "C":
                sig += toks[jj].ch; jj += 1
            opciones = calidad_vocal(t, es_ton, peso_tras(toks, k) >= 2, final, sig)
            nuevas, nav = [], []
            if not es_ton:
                opciones = [(v.lower() if v in ("E", "O") else v, av) for v, av in opciones]
            for c, a in zip(cadenas, avs):
                for v, av in opciones:
                    nuevas.append(c + [("V", v, es_ton)]); nav.append(a + ([av] if av else []))
            cadenas, avs = nuevas, nav
        for c, a in zip(cadenas, avs):
            partes = []
            for k, e in enumerate(c):
                if e[0] == "C":
                    partes.append(e[1])
                else:
                    partes.append(("'" if e[2] else "") + e[1])
            w = "".join(partes)
            w = re.sub(r"au", "au", w)
            # c y g ante vocal anterior (palatalizan); k ante el resto
            w = re.sub(r"c(?!(?:'?[eiE]))", "k", w)
            # final -us (nominativo 2.ª decl.) -> -o ; -u -> -o ; -i -> -e
            if re.search(r"us$", w) and limpio not in ENCLITICAS_US:
                w = w[:-2] + "o"
            elif limpio in ENCLITICAS_US:
                w = re.sub(r"us$", "os", w)       # adverbios en -us que conservan la -s: minus > menos
            else:
                w = re.sub(r"u$", "o", w)
            w = re.sub(r"i$", "e", w)
            av_tot = list(avisos0) + ([av_ac] if av_ac else []) + a
            out.append((w, av_tot))
    # sin duplicados
    vistos, res = set(), []
    for w, a in out:
        if w not in vistos:
            vistos.add(w); res.append((w, a))
    return res, []


# ───────────────────────────── 2. Reglas ─────────────────────────────
@dataclass
class Regla:
    id: str
    etapa: str            # 'vulgar' | 'romance' | 'medieval' | 'actual'
    nombre: str
    patron: str = None
    repl: object = None
    fuente: str = ""
    ejemplo: str = ""
    funcion: object = None
    nota: str = ""


def _son(m):
    return {"p": "b", "t": "d", "k": "g"}[m.group(1)]


GRUPO3_OK = re.compile(r"^[nmrls][ptkbdgfv][lr]$|^str$|^[nm]br$")


def grupo_posible(w):
    """False si una síncopa dejó tres consonantes seguidas que el romance no admite (p. ej. «brt»)."""
    for m in re.finditer(r"[^aeiouEO'\sıj]{3,}", w):
        g = m.group()
        if len(g) > 3 or not GRUPO3_OK.match(g):
            return False
    return True


def _sincopa(w, quitar):
    m = re.search(r"'([aeiouEO]|au)", w)
    if not m:
        return w
    cola = w[m.end():]
    vocs = [(i, c) for i, c in enumerate(cola) if c in V]
    if len(vocs) >= 2:
        i, c = vocs[-2]
        nuevo = w[:m.end()] + cola[:i] + cola[i + 1:]
        if quitar(cola, i, c) and grupo_posible(nuevo):
            return nuevo
    return w


def sincopa_temprana(w):
    """Síncopa latina vulgar tras l, r, s (sol(i)du > sueldo, vir(i)de > verde, quass(i)co > casco). Manual §25.1."""
    return _sincopa(w, lambda cola, i, c: c in "eiou" and i > 0 and cola[i - 1] in "lrs")


def sincopa_postonica(w):
    """Pierde la vocal postónica penúltima (pópulu > pobl'o); no la «a». Manual §25.2, §54."""
    return _sincopa(w, lambda cola, i, c: c != "a")


def sincopa_intertonica(w, activa=True):
    """Pierde las vocales e, i, o, u protónicas internas (no la inicial, no «a»): ver(i)tate > verdad. Manual §54.
    Variable (muchas palabras cultas la conservan): el motor genera con y sin síncopa."""
    m = re.search(r"'", w)
    if not m or not activa:
        return w
    ant, resto = w[:m.start()], w[m.start():]
    pos = [i for i, c in enumerate(ant) if c in V]
    for i in reversed(pos[1:]):
        if ant[i] in "eiou":
            cand = ant[:i] + ant[i + 1:]
            if grupo_posible(cand + resto):
                ant = cand
    return ant + resto


def contraer(w):
    """ee, aa, ii, oo, uu -> una vocal (veer > ver); conserva la marca de tónica."""
    prev = None
    while prev != w:
        prev = w
        w = re.sub(r"('?)([aeiou])\2", r"\1\2", w)
        w = re.sub(r"('?)E([e])", r"\1E", w)
        w = re.sub(r"('?)O([o])", r"\1O", w)
    return w


def prostesis(w):
    return re.sub(r"^(?=s[ptkmnl])", "e", w)


R = []


def regla(*a, **k):
    R.append(Regla(*a, **k))


# ---- etapa 'romance': del latín vulgar al protorromance (hasta ~s. X) ----
regla("hiato", "romance", "e, i átonas en hiato se hacen yod",
      r"(?<!')(?<![aeiouEO])([ei])(?='?[aeiouEO])", "j", "Manual §8 bis, §53", "fílius > fílju")
regla("j_inicial", "romance", "J- inicial ante o, u > ʒ", r"^j(?='?[oOu])", "ʒ", "Manual §38.3", "iocu > ʒuego (juego)")
regla("sc_ante_e_i", "romance", "sc ante e, i > ts", r"sc(?='?[eiE])", "ç", "Manual §47.2", "nascere > naçer")
regla("tj_kj_vocal", "romance", "-tj-, -kj- tras vocal > dz", r"(?<=[aeiouEO])[kt]j", "ʣ", "Manual §53.4", "ratione > raʣón")
regla("tj_kj_cons", "romance", "tj, kj tras consonante o inicial > ts", r"(?<![aeiouEO])[kt]j", "ç", "Manual §53.4", "fortia > fuerça")
regla("c_ante_e_i_vocal", "romance", "-c- ante e, i entre vocales > dz", r"(?<=[aeiouEO])c(?='?[eiE])", "ʣ", "Manual §42.3", "dicere > diʣir")
regla("c_ante_e_i", "romance", "c ante e, i > ts", r"c(?='?[eiE])", "ç", "Manual §34, §42.3", "centum > çiento")
regla("g_inicial_e_i", "romance", "g- inicial ante e, i > yod", r"^g(?='?[eiE])", "j", "Manual §38.3", "gelu > jelo (yelo)")
regla("dj_gj", "romance", "-dj-, -gj- > yod", r"(?<=[aeiouEO])[dg]j", "j", "Manual §53.3", "radiu > rajo (rayo)")
regla("dj_cons", "romance", "dj tras consonante > ts", r"(?<=[^aeiouEO'])dj", "ç", "Manual §53.3", "hordeolu > orçuelo")
regla("lj", "romance", "lj > ʒ", r"lj", "ʒ", "Manual §53.6", "filiu > fiʒo")
regla("nj", "romance", "nj > ɲ", r"nj", "ɲ", "Manual §53.5", "vinea > viɲa")
regla("labial_yod", "romance", "yod tras labial se queda como i", r"(?<=[bvpmf])j", "i", "Manual §53.1", "labiu > labio")
regla("ns", "romance", "-ns- > s sonora", r"(?<=[aeiouEO])ns(?='?[aeiouEO])", "z", "Manual §47.2", "mensa > meza (mesa)")
regla("mb", "romance", "-mb- > m", r"(?<=[aeiouEO])mb", "m", "Manual §47.2", "palumba > paloma")
regla("pt_ps", "romance", "pt > t, ps > s (asimilación)", None, None, "Manual §49", "septem > sette > siete")
regla("ct", "romance", "ct > it > ch", r"(?<=i)kt", "t", "Manual §50.1", "fictu > fito")
regla("ct2", "romance", "-ct- > ich (yod 4.ª)", r"kt", "ıʧ", "Manual §50.1", "nocte > noiʧe > noche")
regla("x", "romance", "x (cs) > ʃ", None, None, "Manual §50.2", "dixi > diʃe (dije)")
regla("ult", "romance", "ult > uich > uch", r"ult", "uıʧ", "Manual §47.2", "multu > muitu > mucho")
regla("gn", "romance", "gn > ɲ", r"gn", "ɲ", "Manual §50.3", "ligna > leɲa")
regla("nct", "romance", "nkt > nt", r"nkt", "nt", "Manual §51.2", "punctu > punto")
regla("rs", "romance", "rs > ss", r"rs", "ss", "Manual §47.2", "ursu > osso")
regla("grupo_inicial_l", "romance", "pl-, cl-, fl- iniciales > ʎ", r"^(?:pl|kl|fl)", "ʎ", "Manual §39.2", "plenu > ʎeno (lleno)")
regla("gl_inicial", "romance", "gl- inicial > l-", r"^gl", "l", "Manual §39.2", "glandula > landre")
regla("prostesis", "romance", "prótesis de e- ante s + consonante", None, None, "Manual §39.3", "scribere > escribir")
regla("qu_inicial_ei", "romance", "qu- ante e, i pierde la u", r"^kw(?='?[eiE])", "k", "Manual §39.4", "quem > quien")
regla("qua_atona", "romance", "qua- átono pierde la u", r"^kw(?=a)", "k", "Manual §39.4", "quattuordecim > catorze")
regla("perdida_g_d", "romance", "-g-, -d- ante e, i se pierden", r"(?<=[aeiouEO])[gd](?='?[eiE])", "", "Manual §41, §43", "regina > reina, pede > pie")
regla("f_v_inter", "romance", "-f- intervocálica > v", r"(?<=[aeiouEO])f(?='?[aeiouEO])", "v", "Manual §42.2", "profectu > provecho")
regla("perdida_v_ivu", "romance", "-v- entre i y u/o final se pierde (-ivu > -io)", r"(?<=i)v(?=[ou]$|o$)", "", "Manual §43.2", "vacivu > vacio")
regla("sonorizacion", "romance", "oclusivas sordas intervocálicas > sonoras", None, None, "Manual §40, §48; Ariza cap. 7", "lupu > lobo, vita > vida")
regla("s_sonora", "romance", "-s- intervocálica > s sonora", r"(?<=[aeiouEO])s(?='?[aeiouEO])", "z", "Manual §42.1", "casa > caza (sonora)")
regla("perdida_j", "romance", "yod intervocálica junto a vocal anterior se pierde", None, None, "Manual §43.1", "pejore > peor")
regla("geminadas", "romance", "geminadas simplificadas o palatalizadas", None, None, "Manual §45-46", "bucca > boca, annu > aɲo")
regla("au", "romance", "au > o", r"au", "o", "Manual §47.3 (paucu > poco)", "paucu > poco")
regla("sincopa_post", "romance", "pérdida de la vocal postónica penúltima", None, None, "Manual §25, §54", "tabula > tabla")
regla("sincopa_inter", "romance", "pérdida de vocales intertónicas", None, None, "Manual §54", "veritate > verdad")
regla("grupos_romances", "romance", "grupos romances secundarios (m'd > nd, m'n > mbr, g'l > ʒ…)", None, None, "Manual §54-59", "nomine > nombre, comite > conde")
regla("ai_yod", "romance", "a + yod de ch/x > e", r"a(?=ı[ʧʃ])", "e", "Manual §8 bis, §50 (lacte > leche)", "lacte > leche")
regla("eir", "romance", "-airo > -eiro (-ariu > -ero)", None, None, "Manual §53", "tertiariu > terçero")

# ---- etapa 'medieval' ----
regla("diptongo_E", "medieval", "Ĕ tónica > ie (salvo ante yod/palatal)", None, None, "Manual §10; Ariza cap. 4.2", "pĕde > pie")
regla("diptongo_O", "medieval", "Ŏ tónica > ue (salvo ante yod/palatal)", None, None, "Manual §13; Ariza cap. 4.2", "fŏcu > fuego")
regla("absorcion_yod", "medieval", "la yod absorbida por ch / x", r"ı(?=[ʧʃ])", "", "Manual §50", "noiʧe > noʧe")
regla("apocope", "medieval", "apócope de -e tras d, n, l, r, s, z (regular)", r"(?<=[dnlrsʣçz])e$", "", "Manual §28.3, §63.1", "mare > mar, sale > sal")
regla("apocope_extrema", "medieval", "apócope extrema de -e (siglos XII-XIII): tras t, ch, ñ, ll, x…", r"(?<=[tʧʃɲʎ])e$|(?<=[nr][dt])e$|(?<=[ns][t])e$", "", "Manual §63.2", "noche > noch, siete > siet, monte > mont")
regla("eiro", "medieval", "-eiro > -ero", r"'eir(?=[oa]$)", "'er", "Manual §53", "primeiro > primero")

# ---- etapa 'actual' ----
regla("f_inicial", "actual", "f- inicial > h- muda (se conserva ante ue)", r"^f(?='?[aeiouEO])(?!u'?e)", "h", "Manual §38; Ariza cap. 7.3", "ferro > hierro")
regla("ie_inicial", "actual", "ie- inicial se escribe ye-", r"^i'e", "y'e", "Manual §10", "equa > yegua")
regla("ue_inicial", "actual", "ue- inicial se escribe hue-", r"^u'e", "hu'e", "Manual §13", "ossu > hueso")
regla("sibilantes", "actual", "reajuste de sibilantes (ç, z > θ; ʃ, ʒ > jota)", None, None, "Manual §35 bis; Ariza cap. 8.3", "ʣ > θ")
regla("iello_illo", "actual", "-iello > -illo", r"i'eʎ(?=[oa]$)", "'iʎ", "Manual §10.2", "castiello > castillo")
regla("restituye_e", "actual", "el español actual restituye -e salvo tras d, n, l, r, s, z", None, None, "Manual §63.3", "mont > monte")

REG = {r.id: r for r in R}


# ───────────────────────────── 3. Motor ─────────────────────────────
@dataclass
class Paso:
    regla: str
    nombre: str
    fuente: str
    antes: str
    despues: str
    etapa: str


def mostrar(w):
    """Forma interna -> forma legible (tónica con acento, E/O abiertas como ɛ/ɔ)."""
    s = w
    s = re.sub(r"'([aeiouEO])", lambda m: {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú", "E": "ɛ́", "O": "ɔ́"}[m.group(1)], s)
    return s.replace("E", "ɛ").replace("O", "ɔ").replace("ı", "j").replace("Ñ", "ɲ")


def _aplicar(w, reg, pasos):
    nuevo = w
    if reg.patron is not None:
        nuevo = re.sub(reg.patron, reg.repl, w)
    elif reg.funcion is not None:
        nuevo = reg.funcion(w)
    if nuevo != w:
        pasos.append(Paso(reg.id, reg.nombre, reg.fuente, mostrar(w), mostrar(nuevo), reg.etapa))
    return nuevo


def _ap(w, rid, pasos):
    return _aplicar(w, REG[rid], pasos)


def romance(w, pasos, inter=True):
    w = _ap(w, "hiato", pasos)
    nuevo = sincopa_temprana(w)
    if nuevo != w: pasos.append(Paso("sincopa_temprana", "síncopa latina temprana entre l/r y consonante dental o velar", "Manual §25, §54", mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    for rid in ("j_inicial", "sc_ante_e_i", "tj_kj_vocal", "tj_kj_cons", "c_ante_e_i_vocal", "c_ante_e_i",
                "g_inicial_e_i", "dj_gj", "dj_cons", "lj", "nj", "labial_yod", "ns", "mb"):
        w = _ap(w, rid, pasos)
    # pt, ps
    nuevo = re.sub(r"pt", "tt", w); nuevo = re.sub(r"ps", "ss", nuevo)
    if nuevo != w: pasos.append(Paso("pt_ps", REG["pt_ps"].nombre, REG["pt_ps"].fuente, mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    for rid in ("ct", "ct2"):
        w = _ap(w, rid, pasos)
    # x
    nuevo = re.sub(r"ks$", "is", w)
    nuevo = re.sub(r"(?<=i)ks", "ʃ", nuevo)
    nuevo = re.sub(r"ks", "ıʃ", nuevo)
    if nuevo != w: pasos.append(Paso("x", REG["x"].nombre, REG["x"].fuente, mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    w = _ap(w, "ai_yod", pasos)
    for rid in ("ult", "gn", "nct", "rs", "grupo_inicial_l", "gl_inicial"):
        w = _ap(w, rid, pasos)
    for rid in ("qu_inicial_ei", "qua_atona"):
        w = _ap(w, rid, pasos)
    # kw medial: ante a -> gw (sonoriza); ante otra vocal -> g (pierde la w)
    nuevo = re.sub(r"(?<=[aeiouEO])kw(?='?a)", "gw", w)
    nuevo = re.sub(r"(?<=[aeiouEO])kw(?='?[eiEoOu])", "k", nuevo)
    if nuevo != w: pasos.append(Paso("qu_medial", "-qu- medial: sonoriza o pierde la u", "Manual §52", mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    for rid in ("perdida_g_d", "f_v_inter", "perdida_v_ivu"):
        w = _ap(w, rid, pasos)
    nuevo = contraer(w)
    if nuevo != w: pasos.append(Paso("contraccion", "contracción de vocales iguales tras perder -d-, -g-", "Manual §41 (ver > veer > ver)", mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    nuevo = re.sub(r"(?<=[aeiouEO])b(?='?[aeiouEO])", "β", w)
    if nuevo != w: pasos.append(Paso("b_fricativa", "-b- intervocálica > fricativa β (se confunde con -v-)", "Manual §43.2", mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    # sonorización (p, t, k > b, d, g), también ante l, r; no tras au
    nuevo = re.sub(r"(?<=[aeiouEO])(?<!au)([ptk])(?='?[aeiouEO]|[lr])", _son, w)
    if nuevo != w: pasos.append(Paso("sonorizacion", REG["sonorizacion"].nombre, REG["sonorizacion"].fuente, mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    w = _ap(w, "s_sonora", pasos)
    # yod intervocálica que se pierde junto a vocal anterior
    nuevo = re.sub(r"(?<=[ei])j(?='?[aeiouEO])|(?<=[aeiouEO])j(?='?[ei])", "", w)
    if nuevo != w: pasos.append(Paso("perdida_j", REG["perdida_j"].nombre, REG["perdida_j"].fuente, mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    # geminadas
    nuevo = re.sub(r"ll", "ʎ", w); nuevo = re.sub(r"nn", "ɲ", nuevo)
    nuevo = re.sub(r"(pp|tt|kk|mm|bb|dd|gg|ff)", lambda m: m.group()[0], nuevo)
    if nuevo != w: pasos.append(Paso("geminadas", REG["geminadas"].nombre, REG["geminadas"].fuente, mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    w = _ap(w, "au", pasos)
    # síncopas
    for rid, fn in (("sincopa_post", sincopa_postonica), ("sincopa_inter", lambda x: sincopa_intertonica(x, inter))):
        nuevo = fn(w)
        if nuevo != w: pasos.append(Paso(rid, REG[rid].nombre, REG[rid].fuente, mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    # grupos romances secundarios (Manual §55-59)
    nuevo = re.sub(r"m(?=[dtgk])", "n", w)
    nuevo = re.sub(r"nm", "lm", nuevo)
    nuevo = re.sub(r"mn(?=o$)", "Ñ", nuevo)
    nuevo = re.sub(r"m[nr]", "mbr", nuevo)
    nuevo = re.sub(r"ml", "mbl", nuevo)
    nuevo = re.sub(r"(?<=[aeiouEO])[gk]l|[td]l", "ʒ", nuevo)
    nuevo = re.sub(r"(?<=[aeiouEO])kl", "ʒ", nuevo)
    if nuevo != w: pasos.append(Paso("grupos_romances", REG["grupos_romances"].nombre, REG["grupos_romances"].fuente, mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    nuevo = prostesis(w)
    if nuevo != w: pasos.append(Paso("prostesis", REG["prostesis"].nombre, REG["prostesis"].fuente, mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    # -arj- > -eir-
    nuevo = re.sub(r"'arj(?=[oa]$)", "'eir", w)
    if nuevo != w: pasos.append(Paso("eir", REG["eir"].nombre, REG["eir"].fuente, mostrar(w), mostrar(nuevo), "romance")); w = nuevo
    return w


BLOQUEO_DIPT = r"(?!j|i|ı|ʒ|ɲ)"     # Ñ (de mn) no bloquea: domnu > dueño


def medieval(w, pasos):
    nuevo = re.sub(r"'E" + BLOQUEO_DIPT, "i'e", w)
    if nuevo != w: pasos.append(Paso("diptongo_E", REG["diptongo_E"].nombre, REG["diptongo_E"].fuente, mostrar(w), mostrar(nuevo), "medieval")); w = nuevo
    nuevo = re.sub(r"'O" + BLOQUEO_DIPT, "u'e", w)
    if nuevo != w: pasos.append(Paso("diptongo_O", REG["diptongo_O"].nombre, REG["diptongo_O"].fuente, mostrar(w), mostrar(nuevo), "medieval")); w = nuevo
    w = w.replace("E", "e").replace("O", "o")     # abiertas sin diptongar se cierran
    for rid in ("absorcion_yod", "apocope", "eiro"):
        w = _ap(w, rid, pasos)
    return w


def variante_apocope_extrema(w):
    """Variante medieval con apócope extrema (noche > noch): frecuente en el Cid, no se hereda al español actual."""
    r = REG["apocope_extrema"]
    nuevo = re.sub(r.patron, r.repl, w)
    return nuevo if nuevo != w else None


def restituir_e(w):
    """Español actual: sólo terminan en l, n, r, s, d, z, j (o vocal, y); si no, vuelve la -e (monte, noche, hombre)."""
    plano = w.replace("'", "")
    if not plano or plano[-1] in "aeiouEOjy":
        return w
    if len(plano) >= 2 and plano[-2] not in "aeiouEO":
        return w + "e"                       # grupo consonántico final: mont > monte, nombr > nombre, verd > verde
    if plano[-1] in "lnrsdθ":
        return w
    return w + "e"                           # siet > siete, noch > noche


def actual(w, pasos):
    for rid in ("f_inicial", "ie_inicial", "ue_inicial"):
        w = _ap(w, rid, pasos)
    nuevo = w.replace("ʣ", "θ").replace("ç", "θ").replace("ʃ", "x").replace("ʒ", "x").replace("ss", "s").replace("z", "s")
    if nuevo != w: pasos.append(Paso("sibilantes", REG["sibilantes"].nombre, REG["sibilantes"].fuente, mostrar(w), mostrar(nuevo), "actual")); w = nuevo
    w = _ap(w, "iello_illo", pasos)
    nuevo = restituir_e(w)
    if nuevo != w: pasos.append(Paso("restituye_e", REG["restituye_e"].nombre, REG["restituye_e"].fuente, mostrar(w), mostrar(nuevo), "actual")); w = nuevo
    return w


# ───────────────────────────── 4. Ortografía ─────────────────────────────
M = "'?"          # marca de tónica opcional


def _comun(s):
    s = s.replace("E", "e").replace("O", "o").replace("ı", "i")
    s = re.sub(r"k(?=" + M + "[eiE])", "qu", s).replace("k", "c")
    return s.replace("gw", "gu").replace("kw", "cu").replace("w", "u")


def ortografia_medieval(w):
    """Ortografía medieval normalizada (a la manera de las ediciones del Cid): ç, z, ss, x, j/g, ll, nn, v."""
    s = w.replace("j", "y")                                  # yod
    s = re.sub(r"ç(?=" + M + "[eiE])", "c", s)
    s = re.sub(r"(?<=[aeiouEO])z(?=" + M + "[aeiouEO])", "s", s)    # s sonora intervocálica se escribía s
    s = s.replace("ʣ", "z").replace("ʧ", "ch").replace("ʃ", "x").replace("ʎ", "ll").replace("ɲ", "ñ").replace("Ñ", "ñ")
    s = s.replace("β", "v")
    s = re.sub(r"ʒ(?=" + M + "[eiE])", "g", s).replace("ʒ", "j")
    return _comun(s).replace("'", "")


def acentuar(s):
    """Pone la tilde según las reglas ortográficas actuales. `s` lleva ' delante de la vocal tónica."""
    if "'" not in s:
        return s
    # núcleos (con hiatos entre vocales fuertes, o débil tónica junto a fuerte)
    t = s
    mudas = {m.start() + 1 for m in re.finditer(r"[qg]u(?=" + M + "[ei])", t)}
    nuc = []
    i = 0
    while i < len(t):
        c = t[i]
        if c in "aeiou" and i not in mudas:
            # extiende el grupo de vocales
            j = i + 1
            while j < len(t) and (t[j] in "aeiou'") and j not in mudas:
                j += 1
            grupo = t[i:j]
            # partir el grupo en núcleos
            cur_start = i
            k = i
            chars = [(idx, t[idx]) for idx in range(i, j) if t[idx] != "'"]
            inicio = chars[0][0]; prev = chars[0]
            for (idx, ch) in chars[1:]:
                ton_prev = idx - 1 >= 0 and t[prev[0] - 1] == "'" if prev[0] > 0 else False
                ton_cur = t[idx - 1] == "'"
                fuerte_prev = prev[1] in "aeo"; fuerte_cur = ch in "aeo"
                hiato = (fuerte_prev and fuerte_cur) or (ton_prev and prev[1] in "iu" and fuerte_cur) or (ton_cur and ch in "iu" and prev[1] in "ao")
                if hiato:
                    nuc.append((inicio, idx)); inicio = idx
                prev = (idx, ch)
            nuc.append((inicio, j))
            i = j
        else:
            i += 1
    if len(nuc) <= 1:
        return s.replace("'", "")
    pos_t = None
    for n, (a, b) in enumerate(nuc):
        if "'" in t[a:b] or (a > 0 and t[a - 1] == "'"):
            pos_t = n
    if pos_t is None:
        return s.replace("'", "")
    desde_fin = len(nuc) - 1 - pos_t
    final = t.rstrip("'")[-1]
    termina_vns = final in "aeiouns"
    lleva = (desde_fin == 0 and termina_vns) or (desde_fin == 1 and not termina_vns) or desde_fin >= 2
    # el hiato con débil tónica siempre lleva tilde
    a, b = nuc[pos_t]
    seg = t[a:b].replace("'", "")
    if len(seg) == 1 and seg in "iu" and (pos_t > 0 and nuc[pos_t - 1][1] == a or pos_t + 1 < len(nuc) and nuc[pos_t + 1][0] == b):
        lleva = True
    if not lleva:
        return s.replace("'", "")
    # vocal que recibe la tilde dentro del núcleo
    base = t[a:b].replace("'", "")
    fuertes = [x for x in base if x in "aeo"]
    if fuertes: objetivo = fuertes[0]
    elif len(base) == 2: objetivo = base[1]
    else: objetivo = base[0]
    pos_rel = base.index(objetivo) if not fuertes else base.index(fuertes[0])
    tilde = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}[objetivo]
    nuevo_seg = base[:pos_rel] + tilde + base[pos_rel + 1:]
    return (t[:a] + nuevo_seg + t[b:]).replace("'", "")


def ortografia_actual(w):
    """Ortografía actual con tilde: θ = z/c; s = s; x (jota) = j; ʎ = ll; ɲ = ñ; h muda ya viene escrita."""
    s = w.replace("j", "y")
    s = re.sub(r"θ(?=" + M + "[eiE])", "c", s).replace("θ", "z")
    s = s.replace("ʧ", "ch").replace("ʎ", "ll").replace("ɲ", "ñ").replace("Ñ", "ñ").replace("x", "j")
    s = s.replace("β", "b")
    s = _comun(s)
    # 'y' final tras vocal o 'i' en diptongo: rey, ley; y intervocálica: mayor
    return acentuar(s)


# ───────────────────────────── 5. API ─────────────────────────────
@dataclass
class Derivacion:
    etimo: str
    cadena: list
    traza: list
    avisos: list
    medieval: str
    actual: str
    nota: str = ""


def _construir(etimo, w, avisos, inter):
    pasos = []
    vl = w
    pasos.append(Paso("vulgar", "pérdida de la cantidad vocálica y de -m final", "Manual §7-8, §62; Ariza cap. 1.2", etimo, mostrar(vl), "vulgar"))
    rom = romance(vl, pasos, inter=inter)
    med = medieval(rom, pasos)
    act = actual(med, pasos)
    avisos = list(avisos)
    for pat, msg in ((r"[sr]j", "grupo con yod no cubierto por las reglas (Manual §53.2)"),
                     (r"nr|lr", "grupo romance no cubierto (Manual §59)")):
        if re.search(pat, act):
            avisos.append(msg)
    if not inter:
        avisos.append("variante sin síncopa de vocales intertónicas (frecuente en voces semicultas)")
    var = variante_apocope_extrema(med)
    medieval_txt = ortografia_medieval(med)
    cadena = [
        {"forma": etimo.replace("*", ""), "etapa": "latín"},
        {"forma": mostrar(vl), "etapa": "latín vulgar"},
        {"forma": mostrar(rom), "etapa": "romance temprano"},
        {"forma": medieval_txt, "etapa": "medieval"},
        {"forma": ortografia_actual(act), "etapa": "actual"},
    ]
    if var:
        v_txt = ortografia_medieval(var)
        cadena[3]["variantes"] = [v_txt]
        pasos.append(Paso("apocope_extrema", REG["apocope_extrema"].nombre, REG["apocope_extrema"].fuente, mostrar(med), mostrar(var), "variante"))
    return Derivacion(etimo, cadena, pasos, avisos, medieval_txt, ortografia_actual(act))


def derivar(etimo):
    """Devuelve (lista de derivaciones patrimoniales posibles, motivo_si_no_hay).
    Hay más de una cuando: (a) el étimo no marca la cantidad vocálica o (b) la síncopa intertónica es dudosa."""
    cands, motivo = a_latin_vulgar(etimo)
    if not cands:
        return [], motivo
    res, vistos = [], set()
    for w, avisos in cands:
        for inter in (True, False):
            d = _construir(etimo, w, avisos, inter)
            clave = (d.medieval, d.actual)
            if clave in vistos:
                continue
            vistos.add(clave)
            res.append(d)
    return res, []


# ───────────────────────────── 6. Adaptación culta ─────────────────────────────
def adaptacion_culta(etimo):
    """Forma que tendría la palabra si se tomó del latín escrito (cultismo): sólo se adapta la terminación y
    la ortografía; no hay sonorización, diptongación ni síncopa. Manual §3, §46 (nota), §47 (notas).
    Devuelve (forma_actual, avisos) o (None, motivo)."""
    s, avisos0 = normalizar_entrada(etimo)
    if s is None:
        return None, avisos0
    toks = tokenizar(s)
    limpio = "".join(LARGAS.get(c, BREVES.get(c, ACUTAS.get(c, c))) for c in s)
    cands = candidatos_acento(toks, limpio)
    if not cands:
        return None, ["sin vocales"]
    k_ton = cands[0][0]
    partes = []
    for k, t in enumerate(toks):
        if t.t == "V":
            ch = {"ae": "e", "oe": "e"}.get(t.ch, t.ch)
            partes.append(("'" if k == k_ton else "") + ch)
        else:
            partes.append({"kw": "qu", "gw": "gu", "ks": "x", "j": "i"}.get(t.ch, t.ch))
    w = "".join(partes)
    w = re.sub(r"us$", "o", w) if limpio not in ENCLITICAS_US else w
    w = re.sub(r"u$", "o", w)
    w = re.sub(r"(?<=[aeiou])lis$", "l", w); w = re.sub(r"(?<=a)ris$", "r", w)
    w = re.sub(r"ll", "l", w)
    w = re.sub(r"ti(?='?[aou])", "ci", w)
    w = re.sub(r"'?c(?!['aeiou])", lambda m: m.group(), w)
    return acentuar(w), avisos0


if __name__ == "__main__":
    import sys
    for e in sys.argv[1:]:
        ds, mot = derivar(e)
        print(e, "->", mot if not ds else "")
        for d in ds:
            print("  ", " > ".join(c["forma"] for c in d.cadena), "|", "; ".join(d.avisos))
            for p in d.traza:
                print(f"      [{p.regla}] {p.antes} → {p.despues}   ({p.fuente})")
