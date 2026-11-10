"""Genera la versión de app.R de la aplicación 03 de DaFu con la pestaña de AIDA.

Uso:  python integrar_app03.py <app.R original> <app.R de salida>

No modifica el archivo original: escribe una copia con los agregados marcados
«AIDA (agregado)». Todos los cambios son agregados, salvo una coma que se suma al final de una línea del menú
(RNF-4). Si el app.R original cambia y algún punto de inserción no se encuentra,
el script se detiene e indica cuál.
"""
import os
import sys

CARGA = '''
# ── AIDA (agregado) ──────────────────────────────────────────────────────────
# Carpeta donde está AIDA. Por defecto, la carpeta "aida" al lado de la carpeta de DaFu;
# puede cambiarse con la variable de entorno AIDA_HOME.
AIDA_HOME <- Sys.getenv("AIDA_HOME", "../../aida")
source(file.path(AIDA_HOME, "cargar.R"), encoding = "UTF-8")
# ─────────────────────────────────────────────────────────────────────────────
'''

MENU = ''',
    menuItem("Interpretación AIDA",           tabName = "aida",      icon = icon("comment-dots"))  # AIDA (agregado)'''

PESTANA = ''',

    # ── Pestaña AIDA (agregado) ───────────────────────────────────────────────
    tabItem("aida",
            h3("Interpretación y síntesis con AIDA"),
            box(width = 12,
                radioButtons("aida_perfil", "Perfil del lector:",
                             choices = c(Novato = "novato", Intermedio = "intermedio", Experto = "experto"),
                             selected = "intermedio", inline = TRUE),
                conditionalPanel(
                  "input.tipo_desc == false",
                  radioButtons("aida_desc", "Descripción a interpretar:",
                               choices = c(Filas = "filas", Columnas = "columnas"), inline = TRUE)
                ),
                actionButton("aida_btn", "Interpretar con AIDA"),
                downloadButton("aida_descarga", "Descargar resultado (Markdown)")
            ),
            box(width = 12, title = "Síntesis",
                tags$style("#aida_sintesis { white-space: pre-wrap; word-wrap: break-word; }"),    # que el texto se lea corrido, sin desplazar
                verbatimTextOutput("aida_sintesis")),
            box(width = 12, title = "Interpretaciones", DTOutput("aida_tabla"))
    )'''

ESTADO = '''  aida_res   <- reactiveVal(NULL)   # AIDA (agregado)
'''

LLAMADA = '''
  aida_server(input, output, resultados, aida_res, factores, tc)   # AIDA (agregado)
'''

SERVER = '''# ── AIDA (agregado) ──────────────────────────────────────────────────────────
# Se llama dentro del server: arma en memoria el mismo texto que las descargas TXT
# (modo integrado) y lo procesa con AIDA. No modifica los resultados de DaFu.
# Todo lo que usa del server de DaFu llega por parámetro (esta función se define fuera de él y no ve sus variables):
# `factores` son las columnas de factores del CSV (para deducir los nombres de las variables) y `tc`, la tabla analizada.
aida_server <- function(input, output, resultados, aida_res, factores, tc) {
  detalle <- function() if (TRUE) "La redacción con el modelo de lenguaje puede tardar varios minutos." else NULL
  observeEvent(input$aida_btn, {
    res <- resultados()
    if (length(res) == 0) {
      showNotification("Primero ejecute «Describir».", type = "warning")
      return()
    }
    # Se decide por lo que DaFu calculó en el último «Describir», no por el estado actual del interruptor.
    vars <- NULL
    if (!is.null(res$grupo)) {
      titulo <- res$t0; desc <- res$grupo; esc <- TRUE      # con agregación DaFu siempre escala
      vars <- grp_dafu()                                    # variables de agrupación: la clase «E47_F3» pasa a decir «cepa E47, fecha F3»
    } else if (identical(input$aida_desc, "columnas") && !is.null(res$columnas)) {
      titulo <- res$t2; desc <- res$columnas; esc <- esc_dafu()
    } else if (!is.null(res$filas)) {
      titulo <- res$t1; desc <- res$filas; esc <- esc_dafu()
    } else {
      showNotification("Los resultados no corresponden al modo elegido; vuelva a ejecutar «Describir».", type = "warning")
      return()
    }
    withProgress(message = "AIDA está interpretando los resultados…", detail = detalle(), {
      r <- tryCatch(aida_desde_dafu(titulo, desc, perfil = input$aida_perfil, escalado = esc,
                                    redactar = TRUE, variables = vars, datos = factores(),
                                    nombre = input$file$name, conjuntos = colnames(tc())),
                    error = function(e) { showNotification(conditionMessage(e), type = "error", duration = 15); NULL })
    })
    if (!is.null(r)) aida_res(r)
  })
  esc_dafu <- reactiveVal(TRUE)                              # escalado vigente al pulsar «Describir»
  grp_dafu <- reactiveVal(NULL)                              # variables de agrupación vigentes al pulsar «Describir»
  observeEvent(resultados(), { aida_res(NULL); esc_dafu(isolate(input$escalar)); grp_dafu(isolate(input$grupo)) })                 # un nuevo «Describir» invalida la interpretación anterior
  output$aida_sintesis <- renderPrint({ req(aida_res()); print(aida_res()$sintesis, encabezado = FALSE) })
  output$aida_tabla <- renderDT({
    req(aida_res())
    # RF-PU-2: aida_tabla() deja sólo los datos que ve el perfil.
    datatable(aida_tabla(aida_res()), rownames = FALSE, options = list(scrollX = TRUE, pageLength = 10, language = list(
      search = "Buscar:", lengthMenu = "Mostrar _MENU_ filas", info = "Filas _START_ a _END_ de _TOTAL_",
      infoEmpty = "Sin filas", zeroRecords = "No hay coincidencias", infoFiltered = "(de _MAX_ en total)",
      paginate = list(previous = "Anterior", `next` = "Siguiente"))))
  })
  output$aida_descarga <- downloadHandler(
    filename = function() paste0(tools::file_path_sans_ext(if (is.null(aida_res())) "resultado" else aida_res()$archivo), "_AIDA_",
                                 if (is.null(aida_res())) input$aida_perfil else aida_res()$perfil, ".md"),   # el perfil con que se interpretó
    content  = function(f) { req(aida_res()); aida_guardar(aida_res(), f) }
  )
}
# ─────────────────────────────────────────────────────────────────────────────

'''

# (ancla, texto, posición): el texto se inserta antes o después del ancla.
PUNTOS = [
    ('source("dellNULMarg.R")\n', CARGA, 'despues'),
    ('menuItem("Caracterización Valor de Test", tabName = "texto",     icon = icon("list-alt"))', MENU, 'despues'),
    ('verbatimTextOutput("desc_results"))\n              )\n            )\n    )', PESTANA, 'despues'),
    ('  # para retener la tabla de frecuencias antes de exportar', ESTADO, 'antes'),
    ('        rowNames = FALSE\n      )\n    }\n  )\n', LLAMADA, 'despues'),
    ('shinyApp(ui, server)', SERVER, 'antes'),
]


def integrar(texto):
    if 'AIDA (agregado)' in texto:
        raise SystemExit("El app.R ya contiene los agregados de AIDA; partí del app.R original de DaFu.")
    for ancla, nuevo, pos in PUNTOS:
        n = texto.count(ancla)
        if n != 1:
            raise SystemExit(f"No se encontró (o se repite) el punto de inserción:\n{ancla}")
        texto = texto.replace(ancla, ancla + nuevo if pos == 'despues' else nuevo + ancla)
    return texto


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    if os.path.abspath(sys.argv[1]) == os.path.abspath(sys.argv[2]):
        raise SystemExit("El archivo de salida debe ser distinto del original: el app.R de DaFu no se modifica.")
    if not os.path.isfile(sys.argv[1]):
        raise SystemExit(f"No se encontró el archivo: {sys.argv[1]}")
    with open(sys.argv[1], 'rb') as f:
        crudo = f.read().decode('utf-8')
    crlf = '\r\n' in crudo
    salida = integrar(crudo.replace('\r\n', '\n'))
    if crlf:
        salida = salida.replace('\n', '\r\n')
    with open(sys.argv[2], 'wb') as f:
        f.write(salida.encode('utf-8'))
    print('Escrito', sys.argv[2])
