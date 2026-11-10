# ─── AIDA · Lectura de la exportación de DaFu (RF-LE-1 a RF-LE-6) ────────────
# Convierte la descripción que exporta la aplicación 03 en una tabla de pares.
# En la descripción de filas y de grupos el bloque es la clase y cada línea es
# una categoría; en la de columnas es al revés (modelo lógico A8, sección 5.1).

.AIDA_CAMPOS <- c("Test.Value", "p.Value", "Class.Cat", "Cat.Class", "Global", "Weight")

# Tipos de descripción según la base de conocimiento (frames especializados).
.aida_tipos <- function(kb) {
  m <- kb$marcos
  data.frame(
    tipo = c("filas", "columnas", "grupos"),
    marco = c("DescripcionDeFilas", "DescripcionDeColumnas", "DescripcionDeGrupos"),
    primera_linea = c(m$DescripcionDeFilas$slots$primera_linea$default,
                      m$DescripcionDeColumnas$slots$primera_linea$default,
                      m$DescripcionDeGrupos$slots$primera_linea$default),
    bloque_es = c(m$DescripcionDeFilas$slots$bloque_es$default,
                  m$DescripcionDeColumnas$slots$bloque_es$default,
                  m$DescripcionDeGrupos$slots$bloque_es$default),
    stringsAsFactors = FALSE
  )
}

# Error de lectura con mensaje explicativo (RF-LE-6).
.aida_error_formato <- function(motivo) {
  stop(paste0("El archivo no tiene el formato de una descripción exportada por DaFu: ", motivo,
              ". Se espera el TXT que genera la aplicación 03 con los botones «Descargar Descripción ... TXT»."),
       call. = FALSE)
}

#' Lee una descripción exportada por DaFu.
#' @param archivo ruta del TXT, o vector de líneas con el mismo contenido (modo integrado).
#' @param kb base de conocimiento cargada con aida_kb().
#' @return data.frame con un par por fila; atributos `descripcion` y `archivo`.
aida_leer <- function(archivo, kb = aida_kb()) {
  if (!is.character(archivo) || length(archivo) == 0) stop("Se espera la ruta de un archivo o un vector de líneas.", call. = FALSE)
  if (anyNA(archivo)) stop("El vector de líneas contiene valores faltantes (NA).", call. = FALSE)
  if (!all(validUTF8(archivo) | Encoding(archivo) == "latin1")) stop("El texto recibido no es UTF-8 válido.", call. = FALSE)
  if (length(archivo) == 1 && !grepl("[\r\n]", archivo)) {
    if (!file.exists(archivo)) {
      if (trimws(gsub('^\\[1\\]\\s*"|"\\s*$', "", archivo)) %in% .aida_tipos(kb)$primera_linea)
        return(aida_leer(c(archivo, ""), kb))                    # sólo el título: exportación sin contenido
      if (!nzchar(trimws(archivo))) stop("Se espera la ruta de un archivo: la ruta está vacía.", call. = FALSE)
      stop("No se encontró el archivo: ", archivo, call. = FALSE)
    }
    if (dir.exists(archivo)) stop("Se indicó una carpeta; se espera la ruta de un archivo TXT.", call. = FALSE)
    ini <- readBin(archivo, "raw", 2)
    if (length(ini) == 0) .aida_error_formato("el archivo está vacío")
    if (identical(ini, as.raw(c(0xff, 0xfe))) || identical(ini, as.raw(c(0xfe, 0xff))))
      .aida_error_formato("el archivo está en UTF-16; guárdelo como UTF-8")
    lineas <- readLines(archivo, warn = FALSE)
    # DaFu con versiones viejas de R en Windows escribe en la codificación local (Windows-1252).
    if (any(is.na(iconv(lineas, "UTF-8", "UTF-8")))) {
      crudo <- lineas
      lineas <- iconv(crudo, "CP1252", "UTF-8")
      if (anyNA(lineas)) lineas <- iconv(crudo, "latin1", "UTF-8")   # bytes sin definir en CP1252
      if (anyNA(lineas)) .aida_error_formato("el archivo no está en UTF-8 ni en Windows-1252 (¿es un archivo binario o un Excel?)")
    } else Encoding(lineas) <- "UTF-8"
    nombre <- basename(archivo)
  } else {                                   # modo integrado: texto en memoria
    lineas <- unlist(strsplit(archivo, "\r\n|\r|\n"))
    nombre <- "(texto en memoria)"
  }
  lineas <- enc2utf8(sub("\r$", "", lineas))
  lineas <- sub("^\ufeff", "", lineas)

  # RF-LE-1: el tipo de descripción se identifica por la primera línea con texto.
  tipos <- .aida_tipos(kb)
  limpia <- trimws(gsub('^\\[1\\]\\s*"|"\\s*$', "", lineas))
  i_tit <- which(limpia %in% tipos$primera_linea)
  if (length(i_tit) == 0) .aida_error_formato("no se reconoce la primera línea")
  i_tit <- i_tit[1]
  tipo <- tipos[tipos$primera_linea == limpia[i_tit], ]
  cuerpo <- lineas[seq_len(length(lineas) - i_tit) + i_tit]

  # RF-LE-2: bloques separados por una línea de guiones. Cada bloque empieza con
  # su nombre ("class: X", o una línea "Variable: valor" por cada variable de
  # agrupación, que se unen con "_" como en DaFu) y sigue con la cabecera y las filas.
  pares <- list(); bloque <- NULL; partes <- character(0); en_tabla <- FALSE
  modo <- "completa"; mitad <- list()      # print() parte la tabla en dos cuando los nombres de fila son largos
  agregar <- function(linea, v) {
    # RF-LE-3: as.numeric acepta 0, 0.000, decimales variables, Inf y NaN.
    pares[[length(pares) + 1]] <<- list(bloque = bloque, linea = linea, v = v)
  }
  numeros <- function(campos, t) {
    v <- suppressWarnings(as.numeric(campos))
    v[campos == "NA"] <- NaN                                     # un NA impreso por R se trata igual que NaN
    if (any(is.na(v) & !is.nan(v))) .aida_error_formato(paste0("valores no numéricos en «", t, "»"))
    v
  }
  cerrar_mitad <- function() {
    if (length(mitad) > 0) .aida_error_formato("la tabla está partida y falta su segunda parte")
  }
  A <- .AIDA_CAMPOS[1:3]; B <- .AIDA_CAMPOS[4:6]
  # Lo que se puede decidir línea por línea se calcula para todas a la vez (recortar y buscar patrones de a una línea era lo
  # que más tardaba con archivos grandes); el recorrido de abajo sólo lleva el estado (bloque, tabla, mitades).
  recortadas <- trimws(cuerpo)
  se_salta <- recortadas == "" | grepl("^\\$\\S*$", recortadas)   # $t1, $filas: nombres de la lista impresa por R
  es_separador <- grepl("^-{5,}$", recortadas)
  es_null <- recortadas == "NULL"                                 # by() imprime NULL en las celdas vacías
  sin_filas <- grepl("^<0 rows>", recortadas) | grepl("^\\[1\\] Test.Value", recortadas)
  es_class <- grepl("^class:", recortadas)
  todos_los_campos <- strsplit(recortadas, "\\s+")
  for (i_ln in seq_along(cuerpo)) {
    if (se_salta[i_ln]) next
    t <- recortadas[i_ln]
    if (es_separador[i_ln]) { cerrar_mitad(); bloque <- NULL; partes <- character(0); en_tabla <- FALSE; modo <- "completa"; next }
    if (es_null[i_ln]) { en_tabla <- FALSE; next }
    if (sin_filas[i_ln]) { en_tabla <- FALSE; next }
    campos <- todos_los_campos[[i_ln]]
    if (en_tabla && modo == "completa" && es_class[i_ln] && length(campos) < 7) {   # falta la línea de guiones entre bloques
      partes <- character(0); en_tabla <- FALSE
    }
    if (identical(campos, .AIDA_CAMPOS)) {                      # cabecera de la tabla
      bloque <- if (length(partes)) paste(partes, collapse = "_") else NA_character_
      en_tabla <- TRUE; modo <- "completa"; next
    }
    kc <- length(campos)                                         # tabla partida en 2 o más trozos de columnas (cualquier corte)
    if (kc < 6 && identical(campos, .AIDA_CAMPOS[seq_len(kc)])) {
      cerrar_mitad()
      bloque <- if (length(partes)) paste(partes, collapse = "_") else NA_character_
      en_tabla <- TRUE; modo <- "primera"; mitad <- list(); hechas <- kc; ncol_t <- kc; next
    }
    if (modo %in% c("primera", "segunda") && length(mitad) > 0 && kc <= 6 - hechas && identical(campos, .AIDA_CAMPOS[hechas + seq_len(kc)])) {
      hechas <- hechas + kc; modo <- "segunda"; ncol_t <- kc; k <- 0; next
    }
    if (identical(campos, B) && modo == "completa")
      .aida_error_formato("segunda parte de una tabla sin su primera parte")
    if (!en_tabla) {
      m <- regmatches(t, regexec("^([^:]+):\\s*(.*)$", t))[[1]]
      if (length(m) == 3) {
        partes <- c(partes, trimws(m[3]))
        next
      }
      .aida_error_formato(paste0("línea no reconocida: «", t, "»"))
    }
    n <- length(campos)
    if (modo == "primera") {
      if (n < ncol_t + 1) .aida_error_formato(paste0("fila incompleta: «", t, "»"))
      mitad[[length(mitad) + 1]] <- list(linea = paste(campos[1:(n - ncol_t)], collapse = " "),
                                         v = numeros(campos[(n - ncol_t + 1):n], t))
      next
    }
    if (modo == "segunda") {
      if (n < ncol_t + 1) .aida_error_formato(paste0("fila incompleta: «", t, "»"))
      k <- k + 1
      linea <- paste(campos[1:(n - ncol_t)], collapse = " ")
      if (k > length(mitad) || mitad[[k]]$linea != linea) .aida_error_formato(paste0("las partes de la tabla no coinciden en «", t, "»"))
      mitad[[k]]$v <- c(mitad[[k]]$v, numeros(campos[(n - ncol_t + 1):n], t))
      if (k == length(mitad)) {
        if (hechas == 6) { for (m in mitad) agregar(m$linea, m$v); mitad <- list(); en_tabla <- FALSE; modo <- "completa" }
        else modo <- "primera"
      }
      next
    }
    # Fila de datos: nombre (puede tener espacios) y seis valores numéricos.
    if (n < 7) .aida_error_formato(paste0("fila incompleta: «", t, "»"))
    agregar(paste(campos[1:(n - 6)], collapse = " "), numeros(campos[(n - 5):n], t))   # RF-LE-4: la línea es siempre texto
  }
  cerrar_mitad()

  if (length(pares) == 0) {
    # RF-LE-5: exportación sin pares.
    df <- data.frame(bloque = character(0), linea = character(0), valor_test = numeric(0),
                     p_valor = numeric(0), class_cat = numeric(0), cat_class = numeric(0),
                     global = numeric(0), weight = numeric(0), stringsAsFactors = FALSE)
  } else {
    v <- function(k) vapply(pares, function(p) p$v[k], 0)
    df <- data.frame(bloque = vapply(pares, function(p) p$bloque, ""), linea = vapply(pares, function(p) p$linea, ""),
                     valor_test = v(1), p_valor = v(2), class_cat = v(3), cat_class = v(4), global = v(5), weight = v(6),
                     stringsAsFactors = FALSE)
  }
  if (any(is.na(df$bloque))) .aida_error_formato("hay filas de datos fuera de un bloque con nombre")
  # Un valor test, p-valor, contribución o proporción global que no es un número no se puede interpretar.
  # Un valor test infinito sí (R-MI-13); un porcentaje o una probabilidad infinitos, no.
  sin_numero <- is.na(df$valor_test) | !is.finite(df$p_valor) | !is.finite(df$cat_class) | !is.finite(df$global)
  if (any(sin_numero)) {
    warning("Se omiten ", sum(sin_numero), " pares con un valor no numérico (NaN): ",
            paste(unique(paste0(df$bloque[sin_numero], " / ", df$linea[sin_numero])), collapse = "; "), call. = FALSE)
    df <- df[!sin_numero, , drop = FALSE]
  }
  incompletos <- is.na(df$class_cat) | is.na(df$weight)
  if (any(incompletos))
    warning("Sin Class.Cat o Weight (se informan como no calculables) en: ",
            paste(unique(paste0(df$bloque[incompletos], " / ", df$linea[incompletos])), collapse = "; "), call. = FALSE)

  # Clase y categoría según el tipo de descripción (slot bloque_es del frame).
  if (tipo$bloque_es == "clase") { df$clase <- df$bloque; df$categoria <- df$linea }
  else                           { df$clase <- df$linea;  df$categoria <- df$bloque }
  df$descripcion <- rep(tipo$tipo, nrow(df))
  df$id_par <- if (nrow(df)) sprintf("P%03d", seq_len(nrow(df))) else character(0)
  df <- df[, c("id_par", "descripcion", "bloque", "linea", "clase", "categoria",
               "valor_test", "p_valor", "class_cat", "cat_class", "global", "weight")]
  rownames(df) <- NULL

  # Control de dominio de cada magnitud (frame Magnitud, facetas mínimo y máximo).
  for (mg in kb$magnitudes) {
    x <- df[[mg$campo_par]]
    fuera <- is.finite(x) & (x < mg$minimo_valido | x > mg$maximo_valido)
    if (any(fuera)) warning("Valores de ", mg$nombre, " fuera de su dominio en los pares ",
                            paste(df$id_par[fuera], collapse = ", "), call. = FALSE)
  }
  attr(df, "descripcion") <- tipo$tipo
  attr(df, "archivo") <- nombre
  df
}
