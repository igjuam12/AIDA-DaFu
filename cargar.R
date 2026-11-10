# ─── AIDA · Carga del asistente ──────────────────────────────────────────────
# Uso:  source("ruta/a/aida/cargar.R")
# Carga las funciones de R y fija la carpeta de AIDA para encontrar la base de
# conocimiento y la parte en Python.

local({
  aqui <- NULL                         # carpeta de este archivo (la llamada a source más interna)
  for (i in rev(seq_len(sys.nframe()))) {
    f <- sys.frame(i)$ofile
    if (!is.null(f)) { aqui <- dirname(normalizePath(f)); break }
  }
  if (is.null(aqui) || !file.exists(file.path(aqui, "kb", "base_conocimiento.json"))) {
    aqui <- if (file.exists(file.path(getwd(), "kb", "base_conocimiento.json"))) getwd()
            else file.path(getwd(), "aida")
  }
  if (!file.exists(file.path(aqui, "kb", "base_conocimiento.json")))
    stop("No se encontró la carpeta de AIDA. Cárguelo con source(\"ruta/a/aida/cargar.R\").", call. = FALSE)
  options(aida.home = normalizePath(aqui))
})

for (pkg in c("jsonlite")) {
  if (!requireNamespace(pkg, quietly = TRUE))
    stop("Falta el paquete ", pkg, ". Instálelo con install.packages(\"", pkg, "\").", call. = FALSE)
}
for (f in c("kb.R", "lectura.R", "mi.R", "ms.R", "aida.R"))
  source(file.path(getOption("aida.home"), "R", f), encoding = "UTF-8")
invisible(aida_kb(recargar = TRUE))
message("AIDA cargado desde ", getOption("aida.home"),
        " (base de conocimiento ", aida_kb()$metadatos$version, ").")
