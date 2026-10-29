# Hispanicus

Lector de textos del español medieval (*Cantar de mio Cid*, *Auto de los Reyes Magos* y tres obras de Berceo) con el léxico del Diccionario del Español Medieval electrónico (DEMel).
Tocá una palabra: la glosa muestra su lema, sus formas documentadas y desde cuándo se registra.

## Cómo abrirlo
En línea: GitHub Pages (el enlace figura arriba, en la descripción del repositorio).
En tu computadora: abrí `index.html` (la portada, donde se elige la transcripción) en el navegador; no necesita servidor ni instalación. Cada texto se abre en `web/index.html?obra=cid` o `?obra=oria`.

## Estructura
- `index.html`: portada con un «códice» por obra (se arma sola desde `web/data/obras.js`).
- `web/`: el lector (`index.html`) y sus datos (`data/<obra>.js`, `data/obras.js`, `data/evolucion.js`).
- `datos/`: lemario completo del DEMel (`lemario.csv`, `formas_indice.csv`) y extractos del Cid y Santa Oria.
- `scripts/`: cómo se generaron los datos a partir de las publicaciones del DEMel.
  - `extract_demel.py`, `build_lemario.py`: leen el zip de datos sin descomprimirlo.
  - `build_obra.py [cid|oria|todas]`: genera `web/data/<obra>.json/.js` y `obras.js` desde el TEI del corpus (`build_cid.py` es un atajo para el Cid).
- `datos/manual/`: tablas de lemas que se corrigen a mano (abrir con Excel).
  - `comunes.csv`: formas ambiguas (de, al, se, es...). Valen para todas las obras.
  - `cid.csv`, `oria.csv`, `reyes.csv`, `millan.csv`, `domingo.csv`: formas sin lema de esa obra (nombres propios, formas raras). Cada obra tiene su archivo.
  - Columnas: forma; lema; estado (`propuesta`, `ok` o `descartar`); el resto es informativo.
  - Orden de prioridad: anotación del DEMel > tabla de la obra > tabla común > reglas automáticas.
  - `scripts/proponer_manuales.py` agrega formas nuevas sin tocar las filas existentes.
- `web/data/evolucion.js`: tabla de evolución que lee la página. Se genera con `scripts/build_evolucion.py` (no editar a mano).
  - `datos/evolucion_wiktionary.csv`: étimos propuestos por el Wikcionario en español para los lemas del DEMel (todos `pendiente`; las columnas que la fuente no da quedan vacías).
  - `datos/verificacion_cid.xlsx`: hoja de revisión de los lemas del Cid. Un étimo pasa a `verificado` solo con Estado = verificado y una Fuente verificada (obra y página, o entrada del DLE). La página marca como «propuesto, sin verificar» todo lo demás.
  - Después de corregir `datos/manual/cid.csv` o la hoja: `python3 scripts/build_obra.py todas` y `python3 scripts/build_evolucion.py`.

## Datos y licencias
- Texto: DEMel, corpus de textos t0103 (ADMYTE 0, transcripción de Steven Kirby), doi:10.18453/rosdok_id00005463, CC BY-SA 4.0.
- Léxico: DEMel, publicación de datos, doi:10.18453/rosdok_id00005462, CC BY-SA 4.0.
- Étimos propuestos: Wikcionario en español (es.wiktionary.org), CC BY-SA 4.0, extraídos con wiktextract (kaikki.org, `es-extract.jsonl`, que no se sube al repositorio por su tamaño). Son propuestas colaborativas, no una fuente bibliográfica.
- Los datos derivados de este repositorio se comparten bajo CC BY-SA 4.0.

## Regenerar los datos
La página ya trae sus datos (`web/data/<obra>.js`). Solo hace falta lo siguiente para reconstruirlos:
1. Descargar el corpus de textos (doi:10.18453/rosdok_id00005463) y la publicación de datos (doi:10.18453/rosdok_id00005462) del DEMel y dejarlos en la raíz del repositorio (`Mueller_Corpus_2026_data/` y `Mueller_Publicacion_2026_data.zip`; no se suben a GitHub).
2. `python3 scripts/extract_demel.py Mueller_Publicacion_2026_data.zip datos` y `python3 scripts/build_lemario.py Mueller_Publicacion_2026_data.zip datos` (leen el zip sin descomprimirlo).
3. `python3 scripts/build_obra.py todas`.

## Agregar una transcripción
1. En `scripts/build_obra.py`, sumar una entrada a `OBRAS` (código del TEI, archivo de documentaciones, recorte de folios y metadatos).
2. `python3 scripts/proponer_manuales.py <obra>` crea `datos/manual/<obra>.csv` con las formas sin lema; completarlo y correr `build_obra.py` de nuevo.
  Si el texto no tiene aún `datos/<tNNNN>_documentaciones.csv`, `python3 scripts/extract_documentaciones.py <zip del DEMel> datos <tNNNN>` lo crea (trae las anotaciones del DEMel de ese texto).
3. En `index.html` (portada), sumar su entrada en el objeto `P` (género, descripción y dibujo). Para usar una imagen propia en vez del dibujo: poner el archivo en `web/img/` y escribir su ruta en `foto`.
