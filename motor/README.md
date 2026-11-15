# Motor de reglas fonéticas de Hispanicus

Pasa del **étimo latino** a la **forma medieval** y a la **forma actual**, y guarda cada cambio con su regla, su ejemplo y su fuente (párrafo del *Manual* de Menéndez Pidal). Está pensado para tres usos:

1. **Auditar la tabla curada**: dado un étimo con sus formas, dice si el camino es regular, si parece cultismo o semicultismo, o si no lo puede explicar (y entonces muestra dónde se separan las formas).
2. **Rellenar la cadena que ve el usuario** (`latín → latín vulgar → romance → medieval → actual`) con los cambios nombrados, para los lemas cuya tabla todavía no está verificada.
3. **Mostrar las reglas** en la página (`reglas.json`, `REGLAS.md`) y en el PDF del concurso.

## Regla de oro (la misma del proyecto)
El motor **no inventa etimologías**. Parte del étimo que da la tabla. Si una regla no alcanza (excepción léxica, analogía, préstamo) lo dice en `avisos`; no adivina. La tabla manda; el motor audita.

## Archivos
| Archivo | Para qué |
|---|---|
| `motor_fonetico.py` | El motor: reglas en orden cronológico, traza de cada paso, ortografía medieval y actual (con tildes). |
| `tabla.py` | `validar_fila()`, `a_formato_evolucion()`, `validar_csv()` y exportación de reglas. |
| `pruebas.py` | 78 palabras con resultado conocido (ejemplos del Manual). Sirve de red de seguridad al tocar reglas. |
| `validar.py` | Mide el motor contra los lemas del Cid y las formas documentadas del DEMel. |
| `informe_validacion_cid.csv` | Resultado palabra por palabra (para revisar en Excel). |
| `reglas.json`, `REGLAS.md` | Catálogo de las 53 reglas con fuente y ejemplo. |

Se usa sin instalar nada (solo Python 3):

```bash
cd motor
python3 motor_fonetico.py nŏctem fīlium castĕllum     # derivación paso a paso
python3 pruebas.py                                     # 78/78
python3 validar.py --detalle                           # medición contra el Cid
python3 tabla.py tu_tabla.csv informe.csv              # audita una tabla curada
```

## Cómo se escribe el étimo (importante)
La cantidad vocálica decide el resultado: `nŏctem` da *noche*, pero una ŏ larga no diptongaría. Los étimos del Wikcionario casi nunca la marcan, así que el motor, cuando no la sabe, **prueba las dos posibilidades** y lo avisa. Para que la derivación sea única, la tabla curada necesita una columna **`etimo_marcado`** con macrones y breves (`ĕ ŏ ē ō ĭ ŭ ī ū ā`), tomados de Corominas/DLE/Menéndez Pidal. Reglas de notación:

- El nominativo en `-us`/`-um` y el acusativo dan lo mismo (`lŭpum`, `lŭpus` → *lobo*). Un genitivo en `-is` se trata como `-e` (`barōnis` → `barōne`).
- Los infinitivos en `-ĕre` pasan a `-ēre` (cambio de conjugación). Si el romance salió en `-ir` (*decir*, *escribir*), escribir el étimo hipotético: `*dīcīre`.
- Un asterisco inicial (`*nīnnus`) se ignora.
- Étimos con varias palabras, griego, árabe o germánico quedan «sin derivar»: no son latinos.

## Qué hace (resumen de las reglas)
Ver `REGLAS.md` para el catálogo completo. En orden: pérdida de la cantidad y de -m → hiato e yod → palatalizaciones (tj, kj, lj, nj, ct, x, gn) → grupos (ns, mb, pt, ult…) → grupos iniciales (pl-, cl-, fl-, prótesis de e-, qu-) → pérdida de -g-/-d- ante e/i → **sonorización** → geminadas → síncopas → grupos romances (m'n > mbr, m'd > nd, g'l > j…) → **diptongación** (ĕ > ie, ŏ > ue, salvo ante yod) → apócope de -e → f- > h- → reajuste de sibilantes → restitución de -e.

Dos decisiones de diseño que vienen del Manual:
- **Síncopa temprana vs. tardía** (§25, §54): `vir(i)de > verde` ocurre antes de perder la -d-; `ver(i)tate > verdad` después de sonorizar. El motor aplica las dos en el orden documentado.
- **Apócope de -e** (§28.3, §63): la regular (tras d, n, l, r, s, z) forma parte de la cadena; la «extrema» del Cid (*noch*, *siet*, *mont*) se muestra como **variante** (`cadena[3].variantes`), porque el español actual no la heredó.

## Cultismos, semicultismos y analogías
- **Cultismo (propuesto)**: la vía patrimonial no explica la forma, pero la **adaptación culta** del latín sí (`adaptacion_culta`: sin sonorizar, sin diptongar). Ej.: *natura*, *nulo*, *abstinencia*.
- **Semicultismo (propuesto)**: la forma sólo se explica si no hay síncopa de la vocal intertónica.
- **Analogía / irregular**: el motor no la detecta sola; aparece como `sin_explicar` con la diferencia a la vista, y es la tabla la que decide.
Todas son **propuestas**: la marca definitiva (`marca` en la tabla) la confirma la bibliografía.

## Resultados (honestos)
- **Pruebas** (`pruebas.py`): 78/78. Ojo: son ejemplos del Manual con los que fui calibrando las reglas; sirven como red de seguridad, **no** como medida independiente.
- **Medición contra el Cid** (`validar.py`), sobre los lemas de `evolucion_wiktionary_prioritarios.csv` con étimo latino de una palabra: **88 con derivación posible → 58 coinciden (65 %)** con el lema moderno o con alguna forma medieval documentada en el DEMel; **7 más se explican como posibles cultismos**; **23 quedan sin explicar**.
  - Esta medición usa los étimos **sin cantidades** y acepta que coincida cualquiera de las variantes (hasta 3). Con `etimo_marcado` debería subir y ser más exigente. Es una cota de partida, no el número final.
  - Lo que queda sin explicar es, sobre todo: partículas y pronombres (*allí*, *allá*, *mí*, *ni*), étimos hipotéticos o dudosos (*\*imbarricāre*, *\*barica*), asimilaciones de prefijo (*applicāre > llegar*, *\*admanescĕre > amanecer*) y germanismos (*werra > guerra*). Cada uno pide una regla propia o una excepción documentada.

## Límites conocidos
- Sólo lemas, no flexión (formas verbales, plurales).
- No cubre: grupos con yod de r, s, p (*sapiat > sepa*, §53.2), metátesis, disimilaciones léxicas (*anima > alma* está; *arbor > árbol* no), pérdida de -d- variable (§41: hoy se aplica sólo ante e/i), asimilación de prefijos, germanismos ni arabismos.
- El motor decide **un** camino por regla; las dudas reales de la bibliografía (p. ej. la pérdida de -d-) deberían pasar a `avisos` o a variantes cuando las verifiques.
- Las referencias al *Manual* (§) se comprobaron contra el texto de tu escaneo (OCR). **Las del libro de Ariza se tomaron del índice, no de una lectura del contenido**: revisarlas en el papel antes de citarlas en el PDF.

## Cómo llevarlo a Hispanicus (opciones)
**A. Precalcular (recomendada).** `scripts/build_evolucion.py` llama al motor y escribe en `web/data/evolucion.js` la cadena y los cambios de cada lema (`a_formato_evolucion`). La página no cambia de arquitectura ni carga Python; funciona en GitHub Pages tal cual. Para los lemas verificados manda la tabla; para el resto se muestra la derivación del motor marcada «propuesta, sin verificar» (el formato de `evolucion.js` ya tiene `estado` y `nota`). El motor además audita la tabla (`validar_csv`) y te lista las filas que no coinciden.

**B. Colab (entrega alternativa del concurso).** Un cuaderno que importa `motor_fonetico` y ofrece una caja de texto: escribís un étimo y ves la derivación con las reglas. Cero infraestructura y muy buena demostración para el jurado.

**C. «Probá tu étimo» en la página.** Dos caminos: (1) portar el motor a JavaScript (las reglas ya son expresiones regulares; JS admite lookbehind, así que la mayoría pasa casi directo; las funciones de síncopa, contracción y tilde hay que reescribirlas, ~150 líneas), o (2) Pyodide, que corre este mismo Python en el navegador (carga ~10 MB; no hay que reescribir nada). Conviene hacerlo al final, si sobra tiempo.

**D. Reglas como datos.** Si querés que la lista de reglas sea editable desde Excel (para el curso o para mostrar el trabajo filológico), el siguiente paso es mover `nombre`, `fuente` y `ejemplo` de `motor_fonetico.py` a una hoja y cargarlas al arrancar. Las expresiones regulares quedan en código.

## Qué haría en este orden (hay tiempo: entrega el 16/11)
1. Agregar `etimo_marcado` a la hoja `verificacion_cid.xlsx` para los ~90 lemas con étimo latino, con las cantidades verificadas en Corominas/DLE.
2. Correr `python3 tabla.py` sobre esa tabla: las filas `sin_explicar` son las que hay que mirar primero (error de la tabla, error del motor o fenómeno que falta).
3. Para cada `sin_explicar`, decidir con la bibliografía: ¿regla nueva?, ¿excepción léxica?, ¿analogía? Anotarlo en `marca` y `cambios`.
4. Conectar el motor a `build_evolucion.py` (opción A).
5. Para el PDF de 2 páginas: la tabla de reglas (`REGLAS.md`), un ejemplo con traza completa (*nŏctem > noche* o *fīlium > hijo*) y la medición final.

## Integración con la página (precálculo)

`scripts/build_evolucion.py` importa `motor/precalculo.py`. Para cada lema pendiente con étimo latino de una sola palabra,
deriva con el motor y **sólo si la forma actual coincide con el lema** escribe en `web/data/evolucion.js` la cadena
(latín > latín vulgar > romance temprano > medieval > actual), los cambios y la fuente de cada regla. Siempre queda
`estado: "pendiente"` y con nota; los lemas verificados en la hoja nunca se pisan. Columna H opcional de la hoja
(«Étimo marcado», con cantidades ĕ, ŏ, ā…) para pasarle al motor el étimo con cantidad.
Regenerar: `python scripts/build_evolucion.py`. Resultado actual: 597 de 1638 lemas con étimo tienen cadena calculada.
