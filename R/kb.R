# ─── AIDA · Base de conocimiento y utilidades comunes ────────────────────────
# Las reglas, umbrales, plantillas e instrucciones por perfil están en
# kb/base_conocimiento.json (RNF-3). El código sólo las aplica.

.aida_env <- new.env(parent = emptyenv())

#' Carga la base de conocimiento (se guarda en memoria después de la primera vez).
aida_kb <- function(ruta = file.path(aida_home(), "kb", "base_conocimiento.json"), recargar = FALSE) {
  if (!recargar && !is.null(.aida_env$kb) && identical(.aida_env$kb_ruta, ruta)) return(.aida_env$kb)
  if (!file.exists(ruta)) stop("No se encontró la base de conocimiento: ", ruta, call. = FALSE)
  kb <- jsonlite::fromJSON(ruta, simplifyVector = FALSE)
  faltan <- setdiff(c("metadatos", "parametros", "magnitudes", "estados", "rangos", "etiquetas_difusas", "advertencias",
                      "plantillas", "secciones_sintesis", "perfiles", "reglas", "marcos"), names(kb))
  if (length(faltan)) stop("La base de conocimiento está incompleta; faltan: ", paste(faltan, collapse = ", "), ".", call. = FALSE)
  .aida_env$kb <- kb; .aida_env$kb_ruta <- ruta
  kb
}

#' Carpeta raíz de AIDA (la fija cargar.R).
aida_home <- function() {
  h <- getOption("aida.home", NULL)
  if (is.null(h)) stop("Ejecute primero source(\"aida/cargar.R\").", call. = FALSE)
  h
}

# Valor de un parámetro de la base de conocimiento (frame Parametro).
.aida_param <- function(kb, nombre) {
  v <- kb$parametros[[nombre]]$valor
  if (is.null(v)) stop("Falta el parámetro «", nombre, "» en la base de conocimiento.", call. = FALSE)
  v
}

# Formato numérico en español: coma decimal y cantidad fija de decimales.
.aida_num <- function(x, d) {
  ifelse(is.na(x), "no calculable",
         ifelse(is.infinite(x), ifelse(x > 0, "infinito", "menos infinito"),
                formatC({r <- round(x + sign(x) * 1e-9, d); r[r == 0] <- 0; r}, format = "f", digits = d, decimal.mark = ",")))
}

# Función de pertenencia trapezoidal (a, b, c, d) de una etiqueta difusa.
.aida_trapecio <- function(x, abcd) {
  a <- abcd[[1]]; b <- abcd[[2]]; c <- abcd[[3]]; d <- abcd[[4]]
  if (x < a || x > d) return(0)
  if (x >= b && x <= c) return(1)
  if (x < b) return((x - a) / (b - a))
  (d - x) / (d - c)
}

# Perfiles válidos (RF-PU-1).
.aida_validar_perfil <- function(perfil, kb) {
  validos <- names(kb$perfiles)
  if (!is.character(perfil) || length(perfil) != 1 || is.na(perfil) || !(perfil %in% validos))
    stop("Perfil no válido: «", paste(format(perfil), collapse = ", "), "». Use uno de: ", paste(validos, collapse = ", "), ".", call. = FALSE)
  invisible(perfil)
}
