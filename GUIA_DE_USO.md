# AIDA · Guía de uso

Cómo usar AIDA una vez instalado (la instalación está en `README.md`): modos de uso, parámetros, controles del texto, estados de la síntesis y problemas frecuentes.

## 1. Modo independiente

1. En DaFu (app 03) cargá el CSV, tocá **Describir** y descargá la descripción con **Descargar Descripción … TXT**.
2. En RStudio:

```r
source("C:/Users/<tu usuario>/OneDrive/Escritorio/aida/cargar.R")   # en R se escriben barras «/» (o «\\» doble); una sola «\» da error

r <- aida("C:/ruta/al/archivo_DescFil.txt", perfil = "intermedio")
r                                   # muestra las primeras interpretaciones y la síntesis
aida_tabla(r)                       # todas las interpretaciones, con los datos que ve el perfil
aida_guardar(r, "resultado.md")     # guarda todo en un archivo legible, en el directorio de trabajo (getwd())
```

Parámetros de `aida()`:

- `perfil`: `"novato"`, `"intermedio"` (por defecto) o `"experto"` (en minúsculas).
- `escalado`: `TRUE` si en DaFu dejaste activado «¿Desea escalar la Tabla?» (por defecto, `TRUE`).
- `redactar`: `FALSE` para no usar el modelo de lenguaje.
- `variables`: nombres de las variables con que agrupaste las filas en DaFu, en el mismo orden (por ejemplo, `c("Cepa", "Fecha")` para clases como `E47_F3`). Con eso los textos dicen «la cepa E47 en la fecha F3» en lugar de «E47_F3», explican qué comparten las clases de cada conjunto y comparan las cepas fecha por fecha. Dentro de la aplicación 03 se toman solos del «Describir» con agrupación. Si no se indican, AIDA los deduce sola buscando en qué columna de la tabla original aparece cada trozo del nombre de la clase («E47» está en «Cepa», «F1» en «Fecha»): la aplicación le pasa la tabla cargada en DaFu y desde R se hace con `datos = tabla` (`aida_inferir_variables()`). Si un trozo cae en más de una columna o en ninguna, no deduce nada. Sin ellos AIDA solo puede decir «las clases que terminan en F1», porque el archivo de DaFu no trae los nombres de las variables.
- `contexto`: texto libre y opcional que cuenta qué se estudió (por ejemplo, «Área de colonias de tres cepas medida en tres fechas»). El modelo lo usa para nombrar lo que se midió y explicar los hallazgos con palabras del tema, sin agregar nada que el texto no diga. La aplicación no lo pide (la pestaña es directa); se usa desde R. Sin contexto, la redacción se limita a lo que dicen los datos.
- `nombre` y `conjuntos`: los usa la aplicación integrada, que no lee un archivo sino el resultado de «Describir». `nombre` es el nombre que se muestra como archivo analizado (el del CSV) y `conjuntos`, la lista de todos los conjuntos de la tabla (`colnames()`). El archivo de DaFu sólo trae los conjuntos con alguna asociación: con esa lista AIDA sabe cuál es de verdad «el de valores más altos»; sin ella lo dice «entre los conjuntos que figuran en el archivo».

Para probar sin DaFu, usá los archivos de `aida/ejemplos`:

```r
r <- aida(file.path(getOption("aida.home"), "ejemplos", "Area__Fuzzy_csv_DescGrp.txt"), perfil = "novato")
```

Hay que cargar AIDA con `source()` (no con `sys.source()`). Si el archivo TXT se exportó con una versión vieja de R en Windows, AIDA lo lee igual (Windows-1252 o UTF-8). Si el TXT tiene valores no numéricos (`NaN`), AIDA omite esos pares y avisa.

**Si R no encuentra tu Python,** indicale cuál usar. Esto debe hacerse al comenzar la sesión, antes de usar la síntesis redactada: si R ya inició Python, hay que reiniciar R (Session > Restart R) y repetirlo:

```r
Sys.setenv(AIDA_PYTHON = "C:/Users/<tu usuario>/AppData/Local/Programs/Python/Python312/python.exe")
```

Para dejarlo fijo, escribí `AIDA_PYTHON=C:/ruta/a/python.exe` en el archivo `.Renviron`. En una sesión, `options(aida.python = "...")` hace lo mismo y tiene prioridad (ver README, sección 4).

Si querés usar otro modelo, definí `AIDA_MODELO` en el `.env` o indicalo con `options(aida.modelo = "qwen2.5:7b")`.

## 2. Modo integrado (pestaña en DaFu)

El repositorio de DaFu no se modifica. Se trabaja sobre una copia de la app 03:

1. Copiá la carpeta `DaFu/03_AsociacionesDifusas` como `DaFu/03_AsociacionesDifusas_AIDA`.
2. Reemplazá el `app.R` de la copia por `aida/integracion/app.R`.
3. Abrí la copia en RStudio y ejecutala con **Run App**, como la original.
4. Cargá el CSV y tocá **Describir** (con «¿Agregación por grupo de filas?» y las variables de agrupación, si querés agrupar). Después, en la pestaña **Interpretación AIDA**, elegí el perfil (y en filas y columnas, cuál de las dos descripciones), y tocá **Interpretar con AIDA**. No hay que subir ni escribir nada más: AIDA toma de DaFu el nombre del CSV, las variables de agrupación y la lista de conjuntos de la tabla. Con **Descargar resultado** obtenés el mismo archivo Markdown que genera `aida_guardar()`.

La primera vez, la app 03 instala sola los paquetes que necesita (`shinyWidgets`, `caret`, `tidyverse`, `FactoMineR`, entre otros): requiere Internet y puede tardar varios minutos. En Windows no hace falta Rtools; si RStudio pregunta por una biblioteca personal, aceptá.

La copia busca AIDA en `../../aida`. Si la guardaste en otro lugar, indicá la ruta con `Sys.setenv(AIDA_HOME = "C:/ruta/a/aida")` antes de ejecutar la app. Si ejecutás la app como trabajo en segundo plano de RStudio, es más seguro fijar la ruta (y `AIDA_PYTHON` con la ruta de `python.exe`) en el archivo `.Renviron`, que se abre con `usethis::edit_r_environ()`.

Los cambios respecto del `app.R` original están en `integracion/cambios_app03.diff`. Todos son agregados marcados «AIDA (agregado)», más una coma en el menú. Si DaFu cambia, la copia se regenera con:

```
python tools/integrar_app03.py ruta/al/app.R_original ruta/de/salida/app.R
```

### La base de conocimiento

Controles y arreglos por código sobre el texto del modelo (no cambian ningún dato): el novato debe decir la intensidad de cada asociación (cuenta «algo parecido pasa con…» como igual a la anterior, o una oración general sobre «las clases» que siguen) y nombrar el conjunto vecino (lo que falta y los hallazgos ya traen se completa por código: «…: aparece mucho más de lo esperable» y «La misma clase también se asocia con el conjunto vecino X»; si no se puede completar, se reintenta el párrafo y, si sigue mal, se arma por código); «Por un lado,» sin «por otro lado» se quita, y «la cepa FLO y fecha F1» vuelve a «la clase cepa FLO, fecha F1»; las oraciones seguidas con el mismo vecino se juntan; «Le sigue…» se reescribe; la explicación del valor test pegada a otra oración pasa a oración propia; y el primer párrafo del novato y del intermedio lleva en oraciones propias la explicación del porcentaje (y, en el intermedio, la del valor test), que se agregan si el modelo no las escribió. En el intermedio, cada asociación debe decir su intensidad y, la primera vez que aparece una transición, se aclara qué es (se agrega si falta). Las líneas de «comparación entre grupos» que calcula el sistema hablan del conjunto con el que más se asocia cada clase («se asocia sobre todo con…», «tiene su asociación principal en…»), porque una clase puede tener además asociaciones secundarias. La intensidad por asociación también se controla y se completa en clases de nombre numérico («clase 4»). En «Descripción general» y en la conclusión, una oración que no pasa los controles se quita y se conserva el resto (la sección sólo falla si ninguna oración pasa); una oración que dice «conjuntos distintos» de clases que tienen los mismos conjuntos también se quita, y la lectura cruzada que recibe el modelo aclara cuándo unas clases son las únicas con más de un conjunto. El tipo de patrón se le dice al modelo en palabras comunes salvo al experto («se asocia con pocas clases», no «singularidad»), y los límites del nombre de un conjunto no cuentan como cifras de una clase.

Las reglas, los umbrales, las plantillas y cómo se le escribe a cada perfil están en `kb/base_conocimiento.json` (versión A10-1.5), no en el código. Cada perfil tiene ahí su `instruccion_registro`, su `guia_redaccion` (las indicaciones que recibe el modelo para ese lector) y su `ejemplo_estilo` (el párrafo que imita); el novato tiene además `intensidad_llana`, que dice cada intensidad en palabras comunes («fuerte» es «mucho más de lo esperable»): para cambiar cómo redacta AIDA para un nivel se edita ese archivo. El mismo contenido está en `kb/AIDA_frames_A10.cypher`, y una prueba controla que coincidan. Después de que el modelo redacta, el código pule el texto sin tocar ningún dato (pasa a cifras las cantidades escritas con palabras, quita un rango que no va junto a su conjunto, el cierre que repite la primera oración y un «menos marcada» entre asociaciones de igual intensidad) y recién entonces lo verifica. Si el párrafo de algún conjunto no pasa los controles, AIDA se lo pide al modelo una vez más (una segunda consulta, sólo en ese caso) y, si tampoco verifica, lo reemplaza por un párrafo armado por código con los datos que ve el perfil. Al perfil experto se le anota «no significativa al 5 %» junto a todo p-valor de 0,05 o más. Los conjuntos se reconocen con el nombre de DaFu (`Are3_20.9a31.4_`) y también con puntos en lugar de guiones bajos (`CO4.9.5a10.5.`), que es como llegan de algunos CSV: en los dos casos AIDA sabe el rango, el orden y los vecinos. Un nombre de variable que quedó de un código (`df...sapply.df..is.factor..`) no se usa para nombrar a las clases. Cuando las clases son los valores de una sola variable, la conclusión se apoya en una lectura cruzada calculada por el sistema: qué clases se asocian con los mismos conjuntos.

El tipo de patrón (constante o singularidad) se nombra en la síntesis redactada sólo cuando distingue a unos conjuntos de otros; si todos tienen el mismo, no aporta nada y no se menciona. La síntesis estructurada lo informa siempre.

## 3. Estados de la síntesis y comprobación

En RStudio, con la carpeta `aida` como directorio de trabajo:

```r
testthat::test_dir("tests/testthat")
```

En la terminal, dentro de `aida`:

```
python -m pytest tests/pytest
```

Ninguna de las dos pruebas necesita Ollama ni la clave de Gemini: no leen tu `.env` ni usan la red. Para probar el modelo de lenguaje, ejecutá un caso con `redactar = TRUE` y fijate que la síntesis diga «Síntesis (redactada)».

El estado de la síntesis puede ser:

- **redactada:** todo el texto es del modelo y pasó los controles.
- **parcialmente redactada:** algún conjunto no pasó los controles y se informa con la versión estructurada; el aviso dice cuál y por qué.
- **no redactada:** el modelo no estuvo disponible o la descripción general o la conclusión no pasaron los controles; se entrega la versión estructurada.

Los textos del modelo que no pasaron los controles quedan en `resultado$sintesis$rechazados`, y `aida_guardar()` los escribe aparte, en `<archivo>_rechazos.json`. Nunca aparecen en el informe.

Si las clases tienen nombres que son sólo números, AIDA las escribe como «la clase 76»: así no se confunden con cifras, conteos ni intervalos al verificar el texto.

## 4. Problemas frecuentes

| Mensaje | Qué hacer |
|---|---|
| «Ejecute primero source(\"aida/cargar.R\")» | Cargá AIDA con `source()` antes de usarlo. |
| «Perfil no válido» | Escribí el perfil en minúsculas: `"novato"`, `"intermedio"` o `"experto"`. |
| «No se pudo redactar la síntesis… no se pudo conectar con Ollama» | Abrí Ollama, o ejecutá `ollama serve` en una terminal. |
| «…Gemini rechazó la clave» o «falta GEMINI_API_KEY» | Revisá el archivo `.env` (copia de `.env.example`) y que la clave esté completa. |
| «…se superó la cuota de Gemini» | Esperá un momento y repetí; el nivel gratuito tiene límites por minuto y por día. |
| «…el modelo de Gemini no existe» | Definí `AIDA_MODELO` en `.env` con un nombre vigente de AI Studio. |
| «…el modelo llama3.2:3b no está descargado» | Descargá el modelo con `ollama pull llama3.2:3b`. |
| «…el modelo tardó demasiado en responder» | Con Ollama, la primera respuesta carga el modelo en memoria; probá de nuevo. |
| «…Gemini cortó la respuesta (SAFETY…)» o «…se cortó por el límite de tokens» | La respuesta quedó incompleta y no se usa: se entrega la versión estructurada. Probá de nuevo u otro modelo. |
| «…AIDA_PROVEEDOR debe ser…» | Corregí el `.env`: los valores válidos son `gemini` y `ollama`. |
| «…falta la biblioteca de Python…» | R está usando otro Python: reiniciá R, configurá `AIDA_PYTHON` y volvé a ejecutar. |
| «…contiene valores que no figuran en los hallazgos» | El modelo inventó un número, o escribió una cantidad con palabras o un cálculo como «la mitad», y la síntesis no pasó el control. Se entrega la versión estructurada, que es la esperada en ese caso. |
| «…atribuye relaciones que no figuran en los hallazgos» | El modelo vinculó una clase con un conjunto, o dio un conteo, que no coincide con el análisis. Se entrega la versión estructurada. |
| «El archivo no tiene el formato de una descripción exportada por DaFu» | Usá el TXT de la descripción, no el CSV ni el Excel. |

## 5. Contenido de la carpeta

```
aida/
├── cargar.R              carga todo (source)
├── R/                    lectura, MI, MS y funciones públicas
├── python/               redacción de la síntesis (Jinja2 + Gemini u Ollama)
├── kb/                   base de conocimiento (JSON) y su script de Neo4j
├── integracion/          app.R de la app 03 con la pestaña AIDA y el diff
├── tools/                exportador de los marcos desde Neo4j (para revisar el modelo) e integrador de app.R
├── tests/                pruebas de R (testthat) y de Python (pytest)
└── ejemplos/             exportaciones de DaFu de los casos de referencia
```
