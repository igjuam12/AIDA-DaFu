# AIDA · Documentación técnica

Descripción de cómo está construido AIDA: arquitectura, flujo de datos, módulos, formatos de intercambio, base de conocimiento, controles del texto, integración con DaFu y pruebas. Para instalar, ver `README.md`; para usarlo, `GUIA_DE_USO.md`.

## 1. Visión general

AIDA lee la descripción de asociaciones que exporta la aplicación 03 de DaFu (TXT) y produce:

1. una **interpretación atómica** por cada par clase–categoría (módulo MI);
2. una **síntesis** de cuatro secciones (módulo MS): descripción general (S1), resultados relevantes (S2), interpretación conclusiva (S3) y limitaciones (S4).

Principios de diseño:

- **AIDA no calcula estadística.** Interpreta lo que DaFu ya calculó (valor test, p-valor, porcentajes).
- **Lo determinista está en R; sólo la redacción usa un modelo de lenguaje (LLM).** Reglas, rangos, selección y ordenamiento de hallazgos salen del código y de la base de conocimiento, nunca del modelo.
- **El modelo redacta sobre hallazgos ya validados y todo lo que escribe se verifica contra los datos.** Lo que no verifica se reemplaza por una versión armada por código (degradación, no error).
- **Las reglas viven en datos, no en código** (`kb/base_conocimiento.json`, RNF-3). El código sólo las aplica.
- **Funciona sin modelo.** Con `redactar = FALSE`, o si el modelo falla, se entrega la síntesis estructurada.

Los identificadores `RF-*`, `R-MI-*`, `R-MS-*`, `RNF-*` y `AD*` que aparecen en los comentarios del código remiten a los requisitos, reglas y advertencias del modelo lógico (A8) y de la base de conocimiento (A10).

## 2. Arquitectura y flujo de datos

```
 TXT de DaFu (o líneas en memoria)
        │
        ▼
 ┌────────────────┐   R/lectura.R      aida_leer()
 │   LECTURA      │   TXT → data.frame de pares (clase, categoría, 6 magnitudes)
 └───────┬────────┘
         ▼
 ┌────────────────┐   R/mi.R           aida_interpretar()
 │  MI            │   regla R-MI-1..7 por valor test → estado, plantilla, texto
 │  (determinista)│   + p-valor, peso bajo, transición, razón de proporciones
 └───────┬────────┘
         ▼
 ┌────────────────┐   R/ms.R           aida_hallazgos()
 │  MS · parte R  │   selecciona significativas, agrupa por conjunto, ordena,
 │  (determinista)│   clasifica (constante / singularidad) → hallazgos.json
 └───────┬────────┘
         │  reticulate (R → Python)         redactar = TRUE y hay hallazgos
         ▼
 ┌────────────────┐   python/redaccion.py  redactar_sintesis()
 │  MS · redacción│   prompt (Jinja2) → llm.py → JSON del modelo
 │  + verificación│   pulido → verificación → respaldo por código → sintesis.json
 └───────┬────────┘
         ▼
 ┌────────────────┐   R/ms.R           aida_sintetizar()
 │  Resultado     │   si Python falla: aida_sintesis_estructurada()
 └────────────────┘   → objeto «aida_resultado»
```

Los dos lenguajes se comunican **por archivos JSON en un directorio temporal** (`tempfile("aida_")`), no por objetos en memoria:

| Archivo | Lo escribe | Contenido |
|---|---|---|
| `hallazgos.json` | R (`aida_sintetizar`) | Hallazgos ordenados, perfil, secciones, limitaciones, contexto |
| `prompt.txt` | Python | Prompt enviado al modelo (útil para depurar) |
| `sintesis.json` | Python | Estado, aviso, modelo, proveedor, fecha, secciones, textos rechazados |

R invoca Python con `reticulate::import_from_path("redaccion", ...)` y llama a `redactar_sintesis(ruta_hallazgos, ruta_kb, modelo)`, que devuelve la ruta de `sintesis.json`.

## 3. Estructura del repositorio

```
aida/
├── cargar.R                 Fija options(aida.home), carga los 5 archivos de R y la KB
├── DESCRIPTION              Dependencias de R (no se instala como paquete)
├── requirements.txt         jinja2, pytest, ollama
├── .env.example             Plantilla de configuración del LLM
├── R/
│   ├── kb.R                 Carga de la KB, aida_home(), formato numérico, trapecio difuso
│   ├── lectura.R            aida_leer(): parser de la exportación de DaFu
│   ├── mi.R                 aida_interpretar(): reglas, plantillas, texto atómico
│   ├── ms.R                 aida_hallazgos(), síntesis estructurada, puente a Python
│   └── aida.R               API pública: aida(), aida_tabla(), aida_guardar(), aida_desde_dafu()
├── python/
│   ├── llm.py               Única llamada al LLM (Gemini / Ollama)
│   ├── redaccion.py         Prompt, pulido, verificación y respaldo del texto
│   └── plantillas/prompt_aida.j2   Plantilla Jinja2 del prompt
├── kb/
│   ├── base_conocimiento.json      Base de conocimiento que carga AIDA (A10-1.5)
│   └── AIDA_frames_A10.cypher      Misma KB como red de marcos para Neo4j
├── integracion/
│   ├── app.R                       app 03 de DaFu con la pestaña «Interpretación AIDA»
│   └── cambios_app03.diff          Diferencias respecto del app.R original
├── tools/
│   ├── exportar_kb.py              Neo4j → JSON de marcos (para revisar el modelo)
│   └── integrar_app03.py           Genera integracion/app.R desde el app.R de DaFu
└── tests/
    ├── testthat/test_aida.R        Pruebas de R
    └── pytest/                     Pruebas de Python (sin red ni LLM)
```

`cargar.R` debe ejecutarse con `source()` (no `sys.source()`): detecta su propia carpeta mirando `ofile` en los marcos de llamada y la guarda en `options(aida.home)`. Todo lo demás (`aida_kb()`, la ruta a `python/`) parte de `aida_home()`.

## 4. Módulos de R

### 4.1 `R/kb.R` · Base de conocimiento y utilidades

- `aida_kb(ruta, recargar)`: lee `kb/base_conocimiento.json` con `jsonlite` y lo guarda en `.aida_env` (caché por ruta). Valida que existan las claves de primer nivel: `metadatos`, `parametros`, `magnitudes`, `estados`, `rangos`, `etiquetas_difusas`, `advertencias`, `plantillas`, `secciones_sintesis`, `perfiles`, `reglas`, `marcos`.
- `.aida_param(kb, nombre)`: valor de un parámetro (falla si falta).
- `.aida_num(x, d)`: formato numérico en español (coma decimal, redondeo con `d` decimales). `NA` → «no calculable», `±Inf` → «infinito» / «menos infinito».
- `.aida_trapecio(x, abcd)`: pertenencia trapezoidal de las etiquetas difusas «algunas» y «muchas».
- `.aida_validar_perfil()`: acepta sólo los perfiles definidos en la KB.

### 4.2 `R/lectura.R` · `aida_leer(archivo, kb)`

Convierte la exportación de DaFu en un `data.frame` de pares. Acepta una ruta o un vector de líneas (modo integrado).

**Tipos de descripción.** Se identifican por la primera línea con texto, que sale de los marcos `DescripcionDeFilas`, `DescripcionDeColumnas` y `DescripcionDeGrupos` de la KB (slot `primera_linea`). El slot `bloque_es` decide qué es el bloque: en filas y grupos el bloque es la **clase** y cada línea una **categoría**; en columnas es al revés.

**Formato esperado.** Bloques separados por una línea de guiones (`-----`). Cada bloque trae su nombre (`class: X`, o una línea `Variable: valor` por variable de agrupación, que se unen con `_`), la cabecera `Test.Value p.Value Class.Cat Cat.Class Global Weight` y una fila por categoría con seis números.

**Casos que maneja el parser** (todos con prueba):

- Codificación UTF-8, Windows-1252 y latin1 (DaFu en R viejo sobre Windows); rechaza UTF-16 y binarios con un mensaje claro.
- Tabla **partida en dos o más trozos de columnas** cuando `print()` corta por ancho: reconstruye cada fila uniendo las partes y verifica que coincidan.
- `NULL` de `by()`, `<0 rows>`, `$t1`/`$filas`, falta de línea de guiones entre bloques.
- Valores `Inf`, `NaN` y `NA`. Los pares con valor test, p-valor, `Cat.Class` o `Global` no numéricos se **omiten con advertencia**; sin `Class.Cat` o `Weight` se informan como no calculables.
- Exportación sin pares (RF-LE-5): devuelve un `data.frame` vacío con las columnas correctas.
- Control de dominio de cada magnitud contra la KB (`minimo_valido`/`maximo_valido`).

**Salida.** Columnas `id_par` (`P001`…), `descripcion`, `bloque`, `linea`, `clase`, `categoria`, `valor_test`, `p_valor`, `class_cat`, `cat_class`, `global`, `weight`, con atributos `descripcion` y `archivo`. Cualquier violación de formato lanza `.aida_error_formato()` con un mensaje en español que indica qué exportar.

### 4.3 `R/mi.R` · `aida_interpretar(pares, perfil, kb, variables)`

Aplica las reglas de interpretación a cada par. Todo está vectorizado: los rangos se buscan una vez por valor distinto y las plantillas se completan por regla, no por par (con decenas de miles de pares era el cuello de botella).

| Paso | Regla | Qué hace |
|---|---|---|
| Rango del valor test | R-MI-1 a R-MI-7 | Asigna regla y estado (E1…E7) según los rangos de la KB; fija significación, dirección e intensidad |
| Significativa | R-MS-1 | `significacion != "no significativo"` (equivale a \|V\| ≥ 1,65) |
| p-valor | R-MI-9 | `p = 0,xxx` si p ≥ 0,01; si no, `p < 0,01` (el texto se calcula siempre; sólo el experto lo ve) |
| Valor no finito | R-MI-13 | `±Inf` o \|V\| ≥ 1e9 toma el rango extremo; se marca `extrema` |
| Peso bajo | R-MI-11 | `Global < 2 %` agrega la advertencia por peso |
| Advertencia general | R-MI-8 / AD1 | Se agrega a toda interpretación |
| Razón de proporciones | — | `Cat.Class / Global` (sólo la ve el experto) |
| Transición | R-MI-12 | Misma clase y misma variable con categorías de índice contiguo (distancia 1) entre las significativas |

**Interpretación con plantilla.** Para cada regla se elige la plantilla del perfil y, si no existe, la general (`perfil == "todos"`). Los campos `[clase]`, `[V]`, `[p]`, `[Cat.Class]`… se completan en una sola pasada (`.aida_completar_vec`), de modo que un nombre de clase como `[V]` no se confunde con un campo. A partir de la segunda aparición dentro del mismo texto, la clase se escribe en su forma breve.

**Nombres legibles.**

- Conjuntos difusos: `Are3_20.9a31.4_` → «Are3 (20,9 a 31,4)». También se reconoce la forma con puntos (`CO4.9.5a10.5.`), que llega de algunos CSV.
- Clases numéricas: `76` → «la clase 76» (para no confundirlas con cifras al verificar).
- Clases compuestas con `variables = c("Cepa", "Fecha")`: `E47_F3` → «E47_F3 (cepa E47, fecha F3)». Si la cantidad de variables no coincide con los componentes, se ignoran.

**Salida.** El mismo `data.frame` de pares más: `id` (`FIL-P001`…), `regla`, `estado`, `significacion`, `direccion`, `intensidad`, `es_significativa`, `extrema`, `p_texto`, `peso_bajo`, `advertencias`, `razon`, `es_transicion`, `contigua`, `plantilla`, `texto`, `perfil`.

### 4.4 `R/ms.R` · Síntesis (parte R)

**`aida_hallazgos()`** es la parte determinista de la síntesis:

1. Toma las interpretaciones significativas (R-MS-1) y las agrupa por conjunto (R-MS-2).
2. Dentro de cada conjunto ordena los pares por \|valor test\| descendente y luego por clase (R-MS-4). Ordena los conjuntos por **fuerza** (suma de \|V\|, R-MS-3). Se usa `method = "radix"` para que el orden no dependa del idioma del sistema (RNF-2).
3. Clasifica cada conjunto según la proporción de clases en que aparece, con las etiquetas difusas «algunas» y «muchas» (trapecios de la KB) y un corte de pertenencia de 0,5:
   - menos de 4 clases en total → `sin clasificar`;
   - pertenencia a «muchas» ≥ corte → `patrón constante`;
   - pertenencia a «algunas» ≥ corte → `singularidad`;
   - si no → `ni constante ni singularidad` (R-MS-5, R-MS-6).
4. Arma la estructura con lo que ve cada perfil (`visibles`: valor test, p-valor, `Class.Cat`, razón), las instrucciones de registro y estilo del perfil, las secciones y las limitaciones.
5. Calcula `texto_s2`, la versión estructurada de «Resultados relevantes», que sirve de respaldo.

**Limitaciones (S4)**, R-MS-10: siempre `AD3`, `AD6` y `AD7`, más `AD4` si la tabla se escaló o `AD5` si no. Las advertencias tienen una variante `texto_novato` que no nombra el valor test.

**`aida_sintesis_estructurada(h)`** produce las cuatro secciones sin modelo, con estado `no redactada`. Para el novato no muestra valor test, fuerza ni identificadores: usa el porcentaje y su comparación con el total. Con muchos datos, los listados se cortan en 10 elementos («… y N más»).

**`aida_sintetizar()`** orquesta: escribe `hallazgos.json` (versión compacta), llama a Python dentro de `tryCatch` y, si el estado no es `redactada` ni `parcialmente redactada`, reemplaza todo por la síntesis estructurada y conserva los textos rechazados. `NA`, `NaN` e `Inf` viajan como `null`.

**`.aida_h_compacto()`**: de cada conjunto sólo van completas las 40 asociaciones de mayor valor test; del resto viajan vectores con lo mínimo que necesita el control (`id`, `clase`, `valor_test`, `transicion`). Python los vuelve a expandir con `_expandir_resto()`.

**`.aida_redactar_python()`**: elige el intérprete (`options(aida.python)` o `AIDA_PYTHON`), avisa si R ya cargó otro, importa `redaccion` y traduce `No module named` a un mensaje con la orden `pip` exacta.

### 4.5 `R/aida.R` · API pública

| Función | Uso |
|---|---|
| `aida(archivo, perfil, escalado, redactar, modelo, kb, variables, contexto, datos, nombre, conjuntos)` | Lectura → MI → MS. Devuelve un objeto de clase `aida_resultado` |
| `aida_inferir_variables(clases, datos)` | Deduce los nombres de las variables de agrupación buscando en qué columna de la tabla original aparece cada trozo del nombre. Devuelve `NULL` si hay ambigüedad |
| `aida_tabla(x)` | Tabla de interpretaciones sólo con las columnas que el perfil puede ver |
| `aida_guardar(x, archivo, max_interpretaciones = 500)` | Informe Markdown; escribe aparte `<archivo>_rechazos.json` |
| `aida_desde_dafu(titulo, descripcion, ...)` | Modo integrado: imprime la descripción de DaFu a texto (`capture.output`, ancho 250) y la procesa |

`aida_inferir_variables` resuelve por eliminación: si una columna es candidata única de un trozo, se descarta como candidata de los demás. `.aida_variables_utiles()` descarta nombres que parecen generados por código (`df...sapply.df..is.factor..`).

El objeto `aida_resultado` contiene: `descripcion`, `archivo`, `perfil`, `escalado`, `kb_version`, `pares`, `interpretaciones` y `sintesis` (esta última con `estado`, `aviso`, `modelo`, `secciones`, `rechazados`, `hallazgos` y `ruta_hallazgos`).

## 5. Módulos de Python

### 5.1 `python/llm.py` · Acceso al modelo

Es el **único** archivo que habla con un LLM; cambiar de modelo o de proveedor sólo toca este archivo (RF-MS-7).

- **Configuración**: variables de entorno o `.env` (`cargar_env()` no pisa variables ya definidas). `AIDA_PROVEEDOR` (`gemini` | `ollama`; por defecto `gemini` si hay `GEMINI_API_KEY`, si no `ollama`), `GEMINI_API_KEY`, `AIDA_MODELO`, `AIDA_MODELO_RESPALDO`, `AIDA_ENV`.
- **Gemini**: `POST` a la API REST con `urllib` (sin SDK), `temperature = 0`, `seed = 42`, respuesta JSON, 8.192 tokens de salida. La clave va en la cabecera `x-goog-api-key` (nunca en la URL ni en los mensajes de error).
  - Errores 500/502/503/504 y 429 se reintentan con esperas de 3, 8, 20 y 40 s (respeta `Retry-After` hasta 30 s).
  - Si el servicio sigue saturado, se prueba `AIDA_MODELO_RESPALDO`.
  - Los 400/401/403/404 se traducen a mensajes accionables. Una respuesta cortada por `MAX_TOKENS` o por seguridad se descarta.
- **Ollama**: `ollama.Client` con respuesta en streaming, contexto de 8.192 tokens, `temperature = 0`. Si el modelo cae en un bucle de repetición, reintenta una vez con más variación.
- `generar_texto(prompt, modelo)` es el punto de entrada; un nombre de modelo de Ollama no se usa con Gemini.

### 5.2 `python/redaccion.py` · Redacción y verificación

Es el archivo más grande (≈1.800 líneas). Entrada: `redactar_sintesis(ruta_hallazgos, ruta_kb, modelo=None, generar=None)`; `generar` permite inyectar un modelo simulado en las pruebas.

**Secuencia de `_redactar()`:**

1. **Prompt.** `datos_prompt(h, ruta_kb)` prepara lo que ve el modelo (por perfil) y `armar_prompt()` lo renderiza con `plantillas/prompt_aida.j2`. Incluye reglas estrictas, la guía de redacción y un ejemplo de estilo del perfil, el contexto del estudio, las variables de agrupación, y por conjunto: asociaciones, transiciones y lecturas cruzadas calculadas por el sistema (`_comparacion`, `_comunes`, `_afines`). Se limita a `MAX_GRUPOS = 8` conjuntos detallados y `MAX_DETALLE = 40` pares por conjunto.
2. **Consulta.** Una sola; se reintenta una vez si la respuesta no es JSON o le faltan secciones. Se pide un objeto con S1, S2 y S3.
3. **Partición de S2** en un párrafo por conjunto (`_partir_por_grupo`) y **revisión de cada uno** (`_revisar_parrafo`).
4. **Segunda consulta**, sólo si algún párrafo de S2 no verifica: se le dice al modelo cuáles y por qué (`reintentar`). Si falla, se ignora.
5. **Respaldo.** El párrafo que sigue sin verificar se reemplaza por uno armado por código (`_parrafo_de_respaldo`).
6. **S1 y S3**: se podan, se pulen y se les quitan las oraciones que no verifican (`_sin_oraciones_que_no_verifican`); la sección sólo falla si ninguna oración pasa.
7. **Estado final** y escritura de `sintesis.json`. S4 (limitaciones) nunca la escribe el modelo: se copia de los hallazgos.

**Pulido** (`_pulir`, antes de verificar; no toca datos): pasa a cifras las cantidades en palabras, quita rangos sueltos del nombre del conjunto, elimina el cierre que repite la primera oración y comparativos falsos («menos marcada» entre asociaciones de igual intensidad), junta transiciones al mismo vecino, y agrega por código las explicaciones del porcentaje y del valor test y la aclaración de «transición» si el modelo no las escribió (según el perfil).

**Controles de verificación:**

| Función | Qué garantiza |
|---|---|
| `verificar` (R-MS-12) | Todo número del texto figura en los hallazgos; también cantidades en palabras y cálculos («la mitad», «el doble») |
| `verificar_atribuciones` | Cada cifra va con su clase y su conjunto; el modelo no cruza datos entre clases |
| `verificar_relaciones` | Las relaciones, conteos y comparaciones entre clases y conjuntos coinciden con el análisis |
| `verificar_afirmaciones` | El texto no afirma lo que el archivo no permite saber (causas, orden temporal, totales «N de N», jerga sin respaldo) |
| `verificar_intensidad` / `verificar_intensidad_por_asociacion` | La intensidad dicha (fuerte/moderada/débil) coincide con la del dato; en novato e intermedio cada asociación debe decirla |
| `_citas_ajenas_al_conjunto`, `_rangos_en_su_lugar` | Un párrafo no nombra otros conjuntos salvo sus transiciones ni usa rangos que no son suyos |

Los textos rechazados quedan registrados con sección, conjunto, texto y motivos.

**Estados de la síntesis:**

| Estado | Significado |
|---|---|
| `redactada` | Todo el texto es del modelo y pasó los controles |
| `parcialmente redactada` | Algún conjunto se informó con el párrafo armado por código |
| `no redactada` | No hubo modelo, o S1/S3 no verificaron: se entrega la versión estructurada completa (la arma R) |

Internamente Python también puede devolver `error` o `no verificada`; R trata cualquier estado que no sea `redactada` ni `parcialmente redactada` como fallo y cae a la versión estructurada, conservando `rechazados` y el aviso.

## 6. Base de conocimiento (`kb/`)

`base_conocimiento.json` (versión **A10-1.5**) concentra las reglas y los textos. Sus secciones:

| Clave | Contenido |
|---|---|
| `metadatos` | Versión, fecha, origen y `sin_limite` (1e9) |
| `parametros` | `umbral_p_exacto` 0,01 · `umbral_peso_bajo` 2 % · `distancia_contigua` 1 · `minimo_clases` 4 · `corte_pertenencia` 0,5 |
| `magnitudes` | Dominio válido de cada columna exportada |
| `estados` | E1…E7: significación, dirección e intensidad |
| `rangos` | R-MI-1…R-MI-7: límites del valor test (±1,65; ±1,96; ±2,58) |
| `etiquetas_difusas` | Trapecios de «algunas» y «muchas» |
| `advertencias` | AD1…AD7 y su disparador (`siempre`, `peso_bajo`, escalado…) |
| `plantillas` | Textos de la interpretación atómica por regla y perfil |
| `secciones_sintesis` | S1…S4: contenido y qué debe incluir (con variante para novato) |
| `perfiles` | `novato`, `intermedio`, `experto`: qué datos ve, `instruccion_registro`, `guia_redaccion`, `ejemplo_estilo`; el novato además `intensidad_llana` |
| `reglas`, `marcos` | La red de marcos (frames) del modelo lógico |

**Para cambiar cómo redacta AIDA para un nivel, se edita este JSON, no el código.** `AIDA_frames_A10.cypher` contiene el mismo modelo para Neo4j y una prueba verifica que ambos coincidan: cualquier cambio se hace en los dos. `tools/exportar_kb.py` sirve para el camino inverso (revisar la red desde Neo4j); su salida no tiene el formato de `base_conocimiento.json`.

## 7. Perfiles de lector

Los perfiles controlan qué se muestra y cómo se escribe (RF-PU-1 a RF-PU-3):

| | Novato | Intermedio | Experto |
|---|---|---|---|
| Valor test y regla | No (`solo_nivel`) | Sí (`valor_y_nivel`) | Sí (`valor_y_nivel`) |
| p-valor | No | No | Sí (anota «no significativa al 5 %» si p ≥ 0,05) |
| `Class.Cat` | No | No | Sí |
| Razón de proporciones | No | No | Sí |
| Tipo de patrón | En palabras comunes | En palabras comunes | «singularidad» / «patrón constante» |
| Explica porcentaje | Sí | Sí | No |

La visibilidad sale de `kb$perfiles[[perfil]]` (`valor_test`, `p_valor_visible`, `class_cat_visible`, `razon_proporciones_visible`). Las filas de tipo de patrón y de explicación del porcentaje salen del prompt y de la guía de cada perfil.

## 8. Integración con DaFu

`integracion/app.R` es la app 03 de DaFu con una pestaña **Interpretación AIDA**. **El repositorio de DaFu no se modifica** (RNF-4): se trabaja sobre una copia (`03_AsociacionesDifusas_AIDA`).

- `tools/integrar_app03.py <app.R original> <app.R salida>` inserta bloques marcados `AIDA (agregado)`: carga de AIDA (`AIDA_HOME`, por defecto `../../aida`), ítem de menú, `tabItem` de la pestaña, un `reactiveVal` y la llamada a `aida_server(...)`. Todos los cambios son agregados, salvo una coma al final de una línea del menú. Si un punto de inserción no se encuentra, el script se detiene e indica cuál (así se detecta que DaFu cambió).
- El servidor de la pestaña toma de DaFu el nombre del CSV (`nombre`), las variables de agrupación (`variables`, o `datos` para inferirlas) y los conjuntos de la tabla (`conjuntos = colnames()`), y llama a `aida_desde_dafu()` dentro de `withProgress`.
- **Descargar resultado** usa `aida_guardar()`: el mismo Markdown que en modo independiente.
- Los cambios exactos están en `integracion/cambios_app03.diff`.

## 9. Configuración y variables de entorno

| Variable / opción | Dónde | Efecto |
|---|---|---|
| `AIDA_PROVEEDOR` | `.env` | `gemini` u `ollama` |
| `GEMINI_API_KEY` | `.env` | Clave de la API de Gemini |
| `AIDA_MODELO` | `.env` / `options(aida.modelo)` | Modelo del proveedor elegido |
| `AIDA_MODELO_RESPALDO` | `.env` | Otro modelo de Gemini si el principal sigue saturado |
| `AIDA_ENV` | entorno | Ruta de otro `.env` (por ejemplo fuera de OneDrive) |
| `AIDA_PYTHON` / `options(aida.python)` | `.Renviron` / sesión | Intérprete de Python para `reticulate` |
| `AIDA_HOME` | entorno | Carpeta de AIDA para la app integrada |
| `options(aida.home)` | lo fija `cargar.R` | Carpeta raíz de AIDA |

`.env` está en `.gitignore`. **Qué sale de la PC con Gemini:** nombres de clases y conjuntos, valores de cada asociación y recuentos; no se envían los datos originales ni el nombre del archivo (se reemplaza por el marcador `ARCHIVO_ANALIZADO` y se restituye al volver). Con Ollama no sale nada.

## 10. Pruebas

| Suite | Comando | Alcance |
|---|---|---|
| R (`testthat`) | `source("cargar.R"); testthat::test_dir("tests/testthat")` | Lectura, MI, MS, informe, KB |
| Python (`pytest`) | `python -m pytest tests/pytest -q` | Redacción, pulido y los controles de verificación, clases numéricas, `llm.py`, coincidencia KB JSON ↔ Cypher |

Ninguna usa red, Gemini ni Ollama: `tests/pytest/conftest.py` limpia `GEMINI_API_KEY`, `AIDA_PROVEEDOR` y `AIDA_MODELO` y apunta `AIDA_ENV` a un archivo inexistente; el modelo se simula con el parámetro `generar` de `redactar_sintesis`.

## 11. Decisiones de diseño y límites

- **Reproducibilidad (RNF-2).** Temperatura 0 y semilla fija en el modelo; ordenamientos por `radix` en R; resultado de MI/MS idéntico entre corridas.
- **Rendimiento.** Se vectoriza todo lo posible y se resuelve una vez por valor distinto; sólo viajan completas 40 asociaciones por conjunto hacia Python; los listados estructurados se topean.
- **Honestidad del texto.** Sin orden temporal ni causas (la lectura es estadística), sin totales que el archivo no permite saber (sólo trae lo que supera el umbral de DaFu), y sin inventar nombres de variables.
- **Límites conocidos.** La redacción depende de la disponibilidad y la cuota del proveedor; los modelos locales chicos fallan más los controles y producen más párrafos de respaldo; los nombres de conjunto sólo se interpretan en las formas `Var3_a_b_` y `Var3.a.b.`; las clases compuestas se descomponen por `_`.
