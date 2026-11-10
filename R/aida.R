# ─── AIDA · Funciones públicas ───────────────────────────────────────────────

#' Ejecuta lectura, interpretación y síntesis sobre una descripción de DaFu.
#' @param archivo ruta del TXT exportado por DaFu, o sus líneas (modo integrado).
#' @param perfil "novato", "intermedio" (por defecto) o "experto" (RF-PU-1).
#' @param escalado TRUE si la tabla se escaló en DaFu (por defecto, como en DaFu).
#' @param redactar FALSE para no usar el modelo de lenguaje (síntesis estructurada).
#' @param variables nombres de las variables de agrupación, en el orden en que forman el nombre de la clase
#'   (por ejemplo c("Cepa", "Fecha") para clases «E47_F3»). Sólo se usan en la descripción de grupos: los textos dicen
#'   «cepa E47, fecha F3» en lugar de «E47_F3». Si no coinciden con la cantidad de componentes del nombre, se ignoran.
#' @param conjuntos nombres de todos los conjuntos (categorías) de la tabla analizada, por ejemplo colnames() de la tabla de
#'   DaFu. El archivo sólo trae los que tienen alguna asociación: con esta lista AIDA sabe cuál es de verdad el de valores
#'   más altos. Sin ella lo dice sólo «entre los conjuntos que figuran en el archivo».
#' @param nombre nombre que se muestra como archivo analizado cuando `archivo` son líneas en memoria (modo integrado):
#'   por ejemplo, el del CSV cargado en DaFu. Si se lee un archivo, se usa el nombre de ese archivo.
#' @param datos tabla de datos original (data.frame) de la que salieron las clases, o sólo sus columnas de factores. Si no se indican
#'   `variables`, AIDA busca en qué columna aparece cada trozo del nombre de la clase («E47» está en «Cepa», «F1» en «Fecha»)
#'   y los deduce sola; si algún trozo cae en más de una columna o en ninguna, no deduce nada y no inventa.
#' @param contexto texto libre, opcional, que describe el estudio (qué se midió, qué significan las variables y sus niveles).
#'   El modelo lo usa para explicar los hallazgos con palabras del tema; sin él, sólo habla de lo que dicen los datos.
aida <- function(archivo, perfil = "intermedio", escalado = TRUE, redactar = TRUE,
                 modelo = getOption("aida.modelo", ""), kb = aida_kb(), variables = NULL, contexto = NULL, datos = NULL, nombre = NULL,
                 conjuntos = NULL) {
  if (!(is.logical(escalado) && length(escalado) == 1 && !is.na(escalado)))
    stop("«escalado» debe ser TRUE o FALSE.", call. = FALSE)
  if (!is.logical(redactar) || length(redactar) != 1 || is.na(redactar))
    stop("«redactar» debe ser TRUE o FALSE.", call. = FALSE)
  if (!is.list(kb) || is.null(kb$rangos)) stop("«kb» debe ser una base de conocimiento (aida_kb()).", call. = FALSE)
  .aida_validar_perfil(perfil, kb)
  pares <- aida_leer(archivo, kb)
  if (length(nombre) == 1 && !is.na(nombre) && nzchar(nombre) && identical(attr(pares, "archivo"), "(texto en memoria)"))
    attr(pares, "archivo") <- as.character(nombre)
  if (!length(variables) && is.data.frame(datos)) variables <- aida_inferir_variables(pares$clase, datos)
  variables <- .aida_variables_utiles(variables)
  interp <- aida_interpretar(pares, perfil, kb, variables)
  if (nrow(pares) == 0) message("La exportación no contiene asociaciones para interpretar.")   # RF-LE-5
  sint <- aida_sintetizar(interp, perfil, escalado, kb, redactar = redactar, modelo = modelo, variables = variables,
                         contexto = contexto, conjuntos = conjuntos)
  structure(list(descripcion = attr(pares, "descripcion"), archivo = attr(pares, "archivo"),
                 perfil = perfil, escalado = escalado, kb_version = kb$metadatos$version, pares = pares,
                 interpretaciones = interp, sintesis = sint), class = "aida_resultado")
}

# Un nombre de columna que quedó de un código («df...sapply.df..is.factor..») no sirve para nombrar a las clases en un texto:
# si algún nombre de variable parece generado así (puntos seguidos, «sapply», «X.» al comienzo o demasiado largo), no se usan nombres.
.aida_variables_utiles <- function(variables) {
  if (!length(variables)) return(NULL)
  variables <- as.character(variables)
  if (any(is.na(variables) | !nzchar(variables) | nchar(variables) > 30 | grepl("[.]{2}|sapply|^X[.]", variables))) return(NULL)
  variables
}

#' Deduce los nombres de las variables de agrupación a partir de la tabla original.
#' Para clases como «E47_F1» busca, para cada trozo, la única columna de `datos` que contiene todos sus valores.
#' Devuelve NULL si las clases no tienen todas la misma cantidad de trozos o si algún trozo no se puede asignar con certeza.
aida_inferir_variables <- function(clases, datos) {
  clases <- unique(as.character(clases))
  if (!length(clases) || !is.data.frame(datos) || !ncol(datos)) return(NULL)
  partes <- strsplit(clases, "_", fixed = TRUE)
  n <- unique(lengths(partes))
  if (length(n) != 1 || n < 2) return(NULL)
  valores <- lapply(seq_len(n), function(i) unique(vapply(partes, `[`, "", i)))
  cols <- Filter(function(c) is.factor(datos[[c]]) || is.character(datos[[c]]), names(datos))
  # Los valores distintos de cada columna se calculan una vez (con millones de filas, convertir la columna por cada trozo era lento).
  niveles <- lapply(stats::setNames(cols, cols), function(c) if (is.factor(datos[[c]])) levels(droplevels(datos[[c]])) else unique(datos[[c]]))
  cand <- lapply(valores, function(v) cols[vapply(cols, function(c) all(v %in% niveles[[c]]), NA)])
  repeat {                                              # una columna ya asignada con certeza a un trozo no puede ser de otro
    unicas <- unlist(cand[lengths(cand) == 1])
    nuevo <- lapply(cand, function(x) if (length(x) > 1) setdiff(x, unicas) else x)
    if (identical(nuevo, cand)) break
    cand <- nuevo
  }
  if (any(lengths(cand) != 1)) return(NULL)
  res <- unlist(cand)
  if (anyDuplicated(res)) NULL else unname(res)
}

print.aida_resultado <- function(x, n = 5, ...) {
  cat("AIDA · ", .aida_desc_txt[[x$descripcion]], " · ", x$archivo, " · perfil ", x$perfil, "\n", sep = "")
  cat(nrow(x$interpretaciones), " interpretaciones (", sum(x$interpretaciones$es_significativa), " significativas)\n", sep = "")
  if (nrow(x$interpretaciones)) {
    cat("\nPrimeras interpretaciones:\n")
    k <- head(seq_len(nrow(x$interpretaciones)), n)
    for (i in k) cat("- [", x$interpretaciones$id[i], "] ", x$interpretaciones$texto[i], "\n", sep = "")
    if (nrow(x$interpretaciones) > n) cat("  … (use aida_tabla(resultado) para ver todas)\n")
  }
  cat("\n"); print(x$sintesis)
  invisible(x)
}

#' Tabla de interpretaciones con los datos que el perfil puede ver (RF-PU-2).
#' `resultado$interpretaciones` conserva todos los campos, para la trazabilidad y las pruebas.
aida_tabla <- function(x) {
  it <- x$interpretaciones
  vis <- x$sintesis$hallazgos$visibles
  tabla <- data.frame(id = it$id, clase = it$clase, categoria = .aida_legible(it$categoria), stringsAsFactors = FALSE)
  if (isTRUE(vis$valor_test)) { tabla$valor_test <- .aida_num(it$valor_test, 3); tabla$regla <- it$regla }
  if (isTRUE(vis$p_valor)) tabla$p_valor <- it$p_texto
  if (isTRUE(vis$class_cat)) tabla$class_cat <- .aida_num(it$class_cat, 1)
  if (isTRUE(vis$razon)) tabla$razon <- .aida_num(it$razon, 2)
  tabla$texto <- it$texto
  tabla
}

#' Guarda el resultado en un archivo Markdown legible (interpretaciones y síntesis).
aida_guardar <- function(x, archivo, max_interpretaciones = 500) {
  if (!is.character(archivo) || length(archivo) != 1 || is.na(archivo) || !nzchar(archivo))
    stop("Indique la ruta del archivo donde guardar el resultado.", call. = FALSE)
  if (dir.exists(archivo)) stop("Se indicó una carpeta; indique la ruta de un archivo.", call. = FALSE)
  if (!dir.exists(dirname(archivo))) stop("No existe la carpeta de destino: ", dirname(archivo), call. = FALSE)
  it <- x$interpretaciones
  ve_regla <- isTRUE(x$sintesis$hallazgos$visibles$valor_test)     # RF-PU-2: el novato no ve la regla
  modelo <- if (isTRUE(!is.na(x$sintesis$modelo)))
    paste0(" (", if (length(x$sintesis$proveedor)) paste0(x$sintesis$proveedor, ", "), "modelo ", x$sintesis$modelo,
           if (length(x$sintesis$fecha)) paste0(", ", x$sintesis$fecha), ")")
  l <- c(paste0("# AIDA · ", .aida_desc_txt[[x$descripcion]]), "",
         paste0("Archivo: ", x$archivo, "  "), paste0("Perfil: ", x$perfil, "  "),
         paste0("Tabla escalada: ", if (isTRUE(x$escalado)) "sí" else "no", "  "),
         paste0("Base de conocimiento: ", x$kb_version), "",
         "## Síntesis", "",
         paste0("Estado: ", x$sintesis$estado, modelo),
         if (isTRUE(nzchar(x$sintesis$aviso))) c("", paste0("> ", gsub("\\s*\n\\s*", " ", x$sintesis$aviso))), "")
  for (s in x$sintesis$secciones)
    l <- c(l, paste0("### ", s$nombre), "", gsub("\n", "  \n", s$texto), "",
           if (ve_regla && length(s$interpretaciones)) c(paste0("*Interpretaciones: ", .aida_y_mas(unlist(s$interpretaciones), 20), "*"), ""))
  l <- c(l, "## Interpretaciones", "")
  if (nrow(it) == 0) l <- c(l, "_Sin interpretaciones._")
  # Con muchas asociaciones el informe no las lista todas (serían decenas de miles de líneas): se escriben las primeras, que son las
  # de mayor valor test dentro de cada conjunto leído, y todas quedan en resultado$interpretaciones (y en aida_tabla()).
  mostrar <- seq_len(min(nrow(it), max_interpretaciones))
  if (length(mostrar))
    l <- c(l, paste0("- **", it$id[mostrar], "** ", if (ve_regla) paste0("(", it$regla[mostrar], ") "), it$texto[mostrar]))
  if (nrow(it) > length(mostrar))
    l <- c(l, "", paste0("_Se muestran las primeras ", length(mostrar), " de ", nrow(it), " interpretaciones; todas están en el resultado de AIDA (resultado$interpretaciones, aida_tabla())._"))
  tryCatch(suppressWarnings(writeLines(enc2utf8(l), archivo, useBytes = TRUE)),
           error = function(e) stop("No se pudo escribir el archivo ", archivo, " (¿falta permiso o está abierto en otro programa?).", call. = FALSE))
  # Los textos del modelo que no pasaron los controles van aparte: el informe no debe mostrarlos como resultado.
  ruta_r <- paste0(tools::file_path_sans_ext(archivo), "_rechazos.json")
  if (file.exists(ruta_r)) unlink(ruta_r)                                        # no dejar los de una corrida anterior
  if (length(x$sintesis$rechazados))
    jsonlite::write_json(x$sintesis$rechazados, ruta_r, auto_unbox = TRUE, pretty = TRUE)
  invisible(archivo)
}

#' Modo integrado: genera en memoria el mismo texto que DaFu escribe en la descarga
#' y lo procesa con AIDA. `titulo` y `descripcion` son res$t1 y res$filas, etc.
aida_desde_dafu <- function(titulo, descripcion, ...) {
  ancho <- options(width = 250); on.exit(options(ancho))   # sin esto, print() parte la tabla si los nombres son largos
  lineas <- utils::capture.output({ cat(titulo, "\n"); print(descripcion) })
  aida(lineas, ...)
}
