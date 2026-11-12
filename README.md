# AIDA

AIDA (Asistente Inteligente de Interpretación y Síntesis de Resultados) ayuda a leer los resultados de **DaFu**, la aplicación web del laboratorio ReAVi (UTN FRM) para el análisis de datos imprecisos con lógica difusa. Lee la descripción de asociaciones que exporta la aplicación 03 de DaFu y produce:

- una **interpretación** de cada asociación, con su justificación estadística;
- una **síntesis** de cuatro secciones (descripción general, resultados relevantes, interpretación conclusiva y limitaciones), redactada con un modelo de lenguaje.

La salida se adapta a tres lectores: **novato**, **intermedio** y **experto**. AIDA no calcula ni modifica nada de DaFu: interpreta lo que DaFu exporta, y el modelo de lenguaje sólo redacta sobre hallazgos ya validados. Todo texto del modelo se verifica contra los datos antes de mostrarse; si el modelo no está disponible, AIDA entrega igual las interpretaciones y una síntesis estructurada. Cómo se usa está en `GUIA_DE_USO.md`.

Esta guía explica cómo instalarlo y dejarlo funcionando en Windows (los pasos son equivalentes en Linux y macOS). AIDA tiene dos partes que se instalan por separado:

- **R**: lee las exportaciones de DaFu, interpreta cada asociación y arma la síntesis estructurada. Es lo mínimo para que funcione.
- **Python**: redacta la síntesis en lenguaje natural con un modelo de lenguaje (Gemini por la API de Google, u Ollama en la propia PC). Es opcional.

## 1. Requisitos

| Programa | Versión | Para qué | ¿Obligatorio? |
|---|---|---|---|
| R | 4.1 o posterior | Ejecutar AIDA | Sí |
| RStudio | cualquiera reciente | Usar R y la aplicación de DaFu | Recomendado |
| Python | 3.10 o posterior | Redactar la síntesis | Sólo para la síntesis redactada |
| Clave de API de Gemini | — | Modelo de lenguaje en la nube | Una de las dos opciones de modelo |
| Ollama + un modelo | — | Modelo de lenguaje local | La otra opción de modelo |
| Carpeta `DaFu` (repositorio, sin cambios) | — | Sólo para el modo integrado | Sólo para el modo integrado |

Se necesita Internet para instalar los paquetes y, si se usa Gemini, cada vez que se redacta una síntesis.

## 2. Dónde poner las carpetas

Dejá la carpeta `aida` al lado de la carpeta `DaFu`, dentro de una misma carpeta:

```
PPS/
├── DaFu/          (el repositorio de DaFu, sin modificar)
└── aida/          (esta carpeta)
```

Si no vas a usar el modo integrado, `DaFu` no hace falta.

## 3. Instalar R y los paquetes de R

1. Instalá R desde https://cloud.r-project.org y RStudio desde https://posit.co/download/rstudio-desktop. Instalá primero R.
2. Abrí RStudio y ejecutá en la consola:

```r
install.packages(c("jsonlite", "reticulate", "testthat"))
```

`jsonlite` es obligatorio. `reticulate` conecta R con Python y sólo se usa para la síntesis redactada. `testthat` sirve para las pruebas. En Windows no hace falta instalar Rtools.

## 4. Instalar Python y sus bibliotecas

1. Descargá Python desde https://www.python.org/downloads. **Al instalarlo, marcá «Add python.exe to PATH».**
2. Abrí una terminal (en Windows, «Símbolo del sistema» o PowerShell), andá a la carpeta `aida` y ejecutá:

```
cd C:\ruta\a\PPS\aida
python -m pip install -r requirements.txt
```

Escribir `python -m pip` (y no sólo `pip`) asegura que las bibliotecas queden en el mismo Python que se va a usar. Si `python` no responde en Windows, probá con `py -m pip install -r requirements.txt`.

`requirements.txt` instala `jinja2` (arma el prompt), `pytest` (pruebas) y `ollama` (sólo se usa con Ollama).

3. Si R no encuentra ese Python, indicáselo con la variable `AIDA_PYTHON` **al comenzar la sesión de R, antes de usar la síntesis redactada** (si R ya inició otro Python, reiniciá R con Session > Restart R):

```r
Sys.setenv(AIDA_PYTHON = "C:/Users/<tu usuario>/AppData/Local/Programs/Python/Python312/python.exe")
```

Para dejarlo fijo, escribí `AIDA_PYTHON=C:/ruta/a/python.exe` (sin `Sys.setenv(...)` ni comillas) en el archivo `.Renviron`, que se abre con `usethis::edit_r_environ()`. En una sesión también sirve `options(aida.python = "...")`, que tiene prioridad sobre `AIDA_PYTHON`. Si ninguna está definida, `reticulate` elige el Python con sus propias reglas (entre ellas `RETICULATE_PYTHON`). En R las rutas se escriben con barras `/` (o con `\\` doble); una sola `\` da error.

## 5. Configurar el modelo de lenguaje

Elegí una de las dos opciones. Podés cambiar de una a otra cuando quieras.

### Opción A. Gemini (recomendada: rápida, no exige una PC potente)

1. Generá una clave de API en Google AI Studio: https://aistudio.google.com/apikey.
2. En la carpeta `aida`, copiá el archivo `.env.example` con el nombre `.env`:

```
copy .env.example .env
```

3. Abrí `.env` con un editor de texto y completá la clave, sin comillas ni espacios:

```
AIDA_PROVEEDOR=gemini
GEMINI_API_KEY=la_clave_que_generaste
```

Variables opcionales del `.env`: `AIDA_MODELO` (el modelo que se usa; ya viene escrito en `.env.example` como `gemini-3.5-flash-lite`, y si falta, ese es el valor de respaldo; Google cambia los nombres de los modelos, por lo que conviene verificar el vigente en AI Studio), `AIDA_MODELO_RESPALDO` (otro modelo para cuando el principal está saturado) y `AIDA_ENV` (ruta de otro archivo `.env`).

**Seguridad.** El archivo `.env` está excluido de git. La clave no debe pegarse en chats, informes ni capturas: si se expone, hay que regenerarla. Si la carpeta `aida` está dentro de OneDrive u otra carpeta sincronizada, el `.env` también se sube a esa nube; para evitarlo, guardalo en otra carpeta e indicá su ruta con la variable de entorno `AIDA_ENV`.

**Qué datos salen de la PC.** Con Gemini se envían a Google los nombres de las clases y de los conjuntos, los valores de cada asociación (porcentajes y, según el perfil, valor test y p-valor) y los recuentos. No se envían los datos originales ni el nombre del archivo. En el nivel gratuito, Google puede usar lo enviado para mejorar sus productos, por lo que no conviene usarlo con datos sensibles o confidenciales (https://ai.google.dev/gemini-api/terms).

### Opción B. Ollama (local: los datos no salen de la PC)

1. Instalá Ollama desde https://ollama.com. Queda corriendo en segundo plano.
2. Descargá el modelo (ocupa unos 2 GB, necesita unos 4 GB de RAM; en equipos sin placa de video la respuesta es lenta):

```
ollama pull llama3.2:3b
```

3. En el `.env` escribí `AIDA_PROVEEDOR=ollama`.

**Cambiar el modelo local.** El modelo por defecto es `llama3.2:3b`, pero se puede usar cualquier modelo que ofrezca Ollama: descargalo con `ollama pull <nombre>` y escribí su nombre en el `.env`, sin tocar el código:

```
AIDA_MODELO=qwen2.5:7b
```

También se puede indicar desde R, para una sesión: `options(aida.modelo = "qwen2.5:7b")`. Un modelo más grande suele redactar mejor, pero es más lento en equipos sin placa de video; uno más chico es más rápido y falla más en los controles, de modo que más párrafos se informan con la versión armada por código. Conviene probar el modelo elegido con los casos de `ejemplos/` y mirar el estado de la síntesis (`redactada`, `parcialmente redactada` o `no redactada`). `AIDA_MODELO` vale para el proveedor elegido: con Gemini, es el nombre de un modelo de Gemini.

Si el servidor no responde, ejecutá `ollama serve` en una terminal y dejala abierta.

### Sin modelo

Si no configurás ninguno, AIDA igual funciona con `redactar = FALSE`: entrega las interpretaciones y la síntesis estructurada.

## 6. Comprobar la instalación

Las pruebas no usan la red, ni la clave de Gemini, ni Ollama.

En la terminal, dentro de `aida`:

```
python -m pytest tests/pytest -q
```

En RStudio, con la carpeta `aida` como directorio de trabajo (Session > Set Working Directory):

```r
source("cargar.R")
testthat::test_dir("tests/testthat")
```

Debe informar que todas las pruebas pasan (sin fallas ni errores). Después, un ejemplo completo, sin modelo, que sólo necesita R:

```r
r <- aida("ejemplos/entropy__Fuzzy_csv_DescGrp.txt", perfil = "intermedio", redactar = FALSE)
r
```

Y con el modelo, que prueba Python y la conexión:

```r
r <- aida("ejemplos/entropy__Fuzzy_csv_DescGrp.txt", perfil = "intermedio")
```

El resultado debe decir «Síntesis (redactada)». Si dice «no redactada», el aviso indica la causa (ver la sección 9).

## 7. Primer uso

Con la instalación comprobada, el modo independiente es: descargar la descripción desde DaFu (**Descargar Descripción … TXT** en la aplicación 03) y, en RStudio,

```r
source("C:/ruta/a/PPS/aida/cargar.R")
r <- aida("C:/ruta/al/archivo_DescFil.txt", perfil = "intermedio")
aida_guardar(r, "resultado.md")
```

Los parámetros, los perfiles y los controles del texto están en `GUIA_DE_USO.md`.

## 8. Modo integrado (pestaña dentro de la aplicación 03 de DaFu)

El repositorio de DaFu no se modifica: se trabaja sobre una copia.

1. Copiá la carpeta `DaFu/03_AsociacionesDifusas` como `DaFu/03_AsociacionesDifusas_AIDA`.
2. Reemplazá el `app.R` de la copia por `aida/integracion/app.R`.
3. Abrí la copia en RStudio y ejecutala con **Run App**, como la original. La primera vez la aplicación instala sola sus paquetes (`shinyWidgets`, `caret`, `tidyverse`, `FactoMineR`, entre otros): requiere Internet y puede tardar varios minutos.
4. Cargá el CSV y tocá **Describir** (con «¿Agregación por grupo de filas?» y las variables de agrupación, si querés agrupar). Después, en la pestaña **Interpretación AIDA**, elegí el perfil y tocá **Interpretar con AIDA**. **Descargar resultado** guarda el mismo informe Markdown que `aida_guardar()`.

La copia busca AIDA en `../../aida`, es decir, en la carpeta `aida` que está junto a `DaFu`. Si la guardaste en otro lugar, indicá la ruta antes de ejecutar la aplicación:

```r
Sys.setenv(AIDA_HOME = "C:/ruta/a/aida")
```

Si ejecutás la aplicación como trabajo en segundo plano de RStudio, fijá `AIDA_HOME` y `AIDA_PYTHON` en el archivo `.Renviron`.

Si DaFu cambia, la copia se regenera a partir del `app.R` original con:

```
python tools/integrar_app03.py ruta/al/app.R_original ruta/de/salida/app.R
```

## 9. Problemas frecuentes

| Mensaje o síntoma | Qué hacer |
|---|---|
| «Ejecute primero source("aida/cargar.R")» | Cargá AIDA con `source()` antes de usar `aida()`. |
| «Perfil no válido» | Escribí el perfil en minúsculas: `"novato"`, `"intermedio"` o `"experto"`. |
| «falta el módulo de Python…» | R está usando otro Python. Reiniciá R, indicá el Python correcto (sección 4) y repetí. |
| «…falta GEMINI_API_KEY» o «Gemini rechazó la clave» | Revisá que `.env` exista en la carpeta `aida` y que la clave esté completa y sin comillas. |
| «…se superó la cuota de Gemini» | Esperá un momento y repetí: el nivel gratuito tiene límites por minuto y por día. |
| «…el servicio de Gemini no está disponible (error 503)» | Es del servicio. AIDA reintenta y, si no responde, entrega la síntesis estructurada: probá de nuevo más tarde. |
| «…el modelo de Gemini no existe» | Definí `AIDA_MODELO` en `.env` con un nombre vigente de AI Studio. |
| «…no se pudo conectar con Ollama» | Abrí Ollama o ejecutá `ollama serve`. |
| «…el modelo llama3.2:3b no está descargado» | `ollama pull llama3.2:3b`. |
| «El archivo no tiene el formato de una descripción exportada por DaFu» | Usá el TXT de «Descargar Descripción», no el CSV ni el Excel. |
| Síntesis «parcialmente redactada» o «no redactada» por los controles | Es el comportamiento esperado: el texto del modelo no pasó la verificación contra los datos y se entrega la versión estructurada. Los textos rechazados quedan en `<archivo>_rechazos.json`. |

## 10. Qué hay en la carpeta

```
aida/
├── cargar.R              carga todo (source)
├── README.md             esta guía (qué es AIDA e instalación)
├── GUIA_DE_USO.md        modos de uso, parámetros y controles del texto
├── .env.example          plantilla de configuración del modelo (copiar como .env)
├── requirements.txt      bibliotecas de Python
├── DESCRIPTION           dependencias de R
├── R/                    lectura, interpretación (MI), síntesis (MS) y funciones públicas
├── python/               redacción de la síntesis (Jinja2 + Gemini u Ollama) y verificación
├── kb/                   base de conocimiento (JSON) y su script de Neo4j
├── integracion/          app.R de la aplicación 03 con la pestaña de AIDA, y el diff
├── tools/                exportador de la base de conocimiento e integrador de app.R
├── tests/                pruebas de R (testthat) y de Python (pytest)
└── ejemplos/             exportaciones de DaFu de los casos de referencia
```
