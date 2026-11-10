# ─── AIDA · Módulo de Síntesis de Resultados, parte en R (RF-MS-1 a RF-MS-11) ─
# Selecciona, agrupa y ordena las interpretaciones (R-MS-1 a R-MS-6), escribe
# hallazgos.json, invoca la redacción en Python y, si no está disponible o la
# verificación falla, entrega la síntesis estructurada (RF-MS-9).

#' Hallazgos ordenados a partir de las interpretaciones (parte determinista de MS).
aida_hallazgos <- function(interp, perfil = "intermedio", escalado = TRUE, kb = aida_kb(), variables = NULL, contexto = NULL,
                           conjuntos = NULL) {
  .aida_validar_perfil(perfil, kb)
  desc <- attr(interp, "descripcion")
  n_clases <- length(unique(interp$clase))
  sig <- interp[which(interp$es_significativa), , drop = FALSE]                  # R-MS-1
  minimo <- .aida_param(kb, "minimo_clases"); corte <- .aida_param(kb, "corte_pertenencia")
  et <- kb$etiquetas_difusas

  grupos <- list()
  filas_de <- split(seq_len(nrow(sig)), factor(sig$categoria, levels = unique(sig$categoria)))   # una sola pasada, no una búsqueda por conjunto
  for (cat in names(filas_de)) {                                                 # R-MS-2
    g <- sig[filas_de[[cat]], , drop = FALSE]
    g <- g[order(-abs(g$valor_test), g$clase, method = "radix"), , drop = FALSE]                   # R-MS-4 (pares)
    clases <- length(unique(g$clase))
    prop <- if (n_clases > 0) clases / n_clases else 0
    mu_a <- .aida_trapecio(prop, et$algunas$parametros)
    mu_m <- .aida_trapecio(prop, et$muchas$parametros)
    tipo <- if (n_clases < minimo) "sin clasificar"                              # R-MS-5 y R-MS-6
            else if (mu_m >= corte) "patrón constante"
            else if (mu_a >= corte) "singularidad" else "ni constante ni singularidad"
    leg_cat <- .aida_legible(cat); vt_txt <- .aida_num(g$valor_test, 3)
    tr_leg <- character(nrow(g)); w <- which(g$es_transicion)
    if (length(w)) tr_leg[w] <- .aida_contiguas_legibles(g$contigua[w], function(x) paste(x, collapse = ", "))
    grupos[[length(grupos) + 1]] <- list(
      conjunto = cat, conjunto_legible = leg_cat,
      fuerza = sum(abs(g$valor_test)), fuerza_txt = .aida_num(sum(abs(g$valor_test)), 3),   # R-MS-3
      n_pares = nrow(g), n_clases = clases, proporcion_clases = prop,
      pertenencia_algunas = mu_a, pertenencia_muchas = mu_m, tipo = tipo,
      # Textos y números se calculan en bloque, una vez por conjunto; el texto de cada interpretación no viaja a Python (no se usa).
      pares = lapply(seq_len(nrow(g)), function(k) list(
        id = g$id[k], clase = g$clase[k], caracteristica = g$categoria[k], caracteristica_legible = leg_cat,
        valor_test = g$valor_test[k], valor_test_txt = vt_txt[k], p_valor = g$p_valor[k], p_texto = g$p_texto[k],
        class_cat = g$class_cat[k], cat_class = g$cat_class[k], global = g$global[k],
        razon = g$razon[k], regla = g$regla[k], significacion = g$significacion[k],
        direccion = g$direccion[k], intensidad = g$intensidad[k],
        peso_bajo = g$peso_bajo[k], transicion = if (g$es_transicion[k]) g$contigua[k] else "",
        transicion_legible = tr_leg[k])))
  }
  if (length(grupos)) {                                                          # R-MS-4 (grupos)
    o <- order(-vapply(grupos, `[[`, 0, "fuerza"), vapply(grupos, `[[`, "", "conjunto"), method = "radix")  # RNF-2: sin depender del idioma del sistema
    grupos <- grupos[o]
    for (k in seq_along(grupos)) grupos[[k]]$posicion <- k
  }

  lim <- c("AD3", if (isTRUE(escalado)) "AD4" else "AD5", "AD6", "AD7")          # R-MS-10
  ve_v <- kb$perfiles[[perfil]]$valor_test != "solo_nivel"
  # El perfil que no ve el valor test recibe la versión de la limitación que no lo nombra (RF-PU-2).
  texto_lim <- function(a) {
    ad <- kb$advertencias[[a]]
    if (!ve_v && !is.null(ad$texto_novato)) ad$texto_novato else ad$texto
  }
  h <- list(
    perfil = perfil,
    instruccion_registro = kb$perfiles[[perfil]]$instruccion_registro,          # RF-PU-3
    guia_redaccion = kb$perfiles[[perfil]]$guia_redaccion,                      # RF-PU-3: cómo se le escribe a este lector (RNF-3)
    ejemplo_estilo = kb$perfiles[[perfil]]$ejemplo_estilo,
    intensidad_llana = kb$perfiles[[perfil]]$intensidad_llana,                  # sólo el novato: «fuerte» → «mucho más de lo esperable»
    escalado = isTRUE(escalado),
    visibles = list(valor_test = ve_v,                                           # RF-PU-2 (RNF-3)
                    p_valor = isTRUE(kb$perfiles[[perfil]]$p_valor_visible),
                    class_cat = isTRUE(kb$perfiles[[perfil]]$class_cat_visible),
                    razon = isTRUE(kb$perfiles[[perfil]]$razon_proporciones_visible)),
    descripcion = desc,
    archivo = attr(interp, "archivo"),
    n_pares = nrow(interp),
    n_clases = n_clases,
    n_categorias = length(unique(interp$categoria)),
    n_significativas = nrow(sig),
    n_no_significativas = nrow(interp) - nrow(sig),                              # R-MS-9 (latente)
    n_transiciones = sum(sig$es_transicion),
    minimo_clases = minimo,
    secciones = lapply(kb$secciones_sintesis, function(s) list(id = s$id, nombre = s$nombre,
                                                                contenido = if (!ve_v && !is.null(s$contenido_novato)) s$contenido_novato else s$contenido,
                                                                debe_incluir = s$debe_incluir)),
    limitaciones = lapply(lim, function(a) list(id = a, texto = texto_lim(a))),
    tipo_novato = as.list(.aida_tipo_novato),
    grupos = grupos
  )
  if (length(contexto) && nzchar(trimws(paste(contexto, collapse = " "))))     # descripción del estudio escrita por el usuario
    h$contexto <- substr(trimws(paste(contexto, collapse = " ")), 1, 1500)
  if (length(conjuntos)) h$conjuntos_tabla <- as.character(conjuntos)   # todos los conjuntos de la tabla, tengan o no asociaciones
  if (length(variables)) h$variables <- as.character(variables)     # nombres de las variables de agrupación (descripción de grupos)
  h$texto_s2 <- .aida_texto_s2(h)           # versión estructurada de «Resultados relevantes»: respaldo si el modelo no redacta o no verifica
  h
}

# Para el novato, el tipo de patrón se dice en palabras comunes (R-MS-5 y R-MS-6: «algunas» o «muchas» clases).
.aida_tipo_novato <- c("singularidad" = "se asocia con pocas clases (singularidad)",
                       "patrón constante" = "se asocia con muchas clases (patrón constante)",
                       "ni constante ni singularidad" = "se asocia con una cantidad intermedia de clases",
                       "sin clasificar" = "sin clasificar (hay pocas clases para distinguir el patrón)")

# Texto estructurado de «Resultados relevantes»: una línea por conjunto, en el orden de R-MS-4, con los datos que ve el perfil.
# Si hay redacción, el modelo escribe un párrafo por conjunto y esta línea sólo reemplaza al párrafo que no verifica.
# Con muchos datos, los listados del texto estructurado tienen un tope: se muestran las de mayor valor test y se cuenta el resto.
.aida_max_listadas <- 10
.aida_y_mas <- function(x, max = .aida_max_listadas) {
  if (length(x) <= max) return(paste(x, collapse = ", "))
  paste0(paste(x[seq_len(max)], collapse = ", "), " y ", length(x) - max, " más")
}

.aida_texto_s2 <- function(h) {
  if (length(h$grupos) == 0) return("No hay asociaciones significativas.")
  ver_v <- isTRUE(h$visibles$valor_test)       # RF-PU-2: el novato no ve valor test ni fuerza
  lin <- vapply(h$grupos, function(g) {
    pares <- vapply(g$pares[seq_len(min(length(g$pares), .aida_max_listadas))], function(p) {
      # El novato no ve el valor test: se le da, en cambio, el porcentaje y su comparación con el total (Cat.Class y Global).
      det <- c(if (ver_v) paste0("V = ", .aida_num(p$valor_test, 3))
               else paste0(.aida_num(p$cat_class, 1), " % de sus valores, frente al ", .aida_num(p$global, 1), " % del total"),
               if (isTRUE(p$peso_bajo)) if (ver_v) "peso bajo" else "pocos datos")
      nombre <- .aida_clase_txt(p$clase, articulo = FALSE)
      if (length(det)) paste0(nombre, " (", paste(det, collapse = "; "), ")") else nombre
    }, "")
    paste0(g$posicion, ". ", g$conjunto_legible, ": ", if (ver_v) paste0("fuerza ", .aida_num(g$fuerza, 3), "; "),
           g$n_pares, if (g$n_pares == 1) " asociación; " else " asociaciones; ",
           if (ver_v) g$tipo else unname(.aida_tipo_novato[g$tipo]), ". ", paste(pares, collapse = ", "),
           if (length(g$pares) > .aida_max_listadas) paste0(" y ", length(g$pares) - .aida_max_listadas, " más"), ".")
  }, "")
  paste(lin, collapse = "\n")
}

# Etiquetas de cada tipo de descripción, para los textos.
.aida_desc_txt <- c(filas = "descripción de filas", columnas = "descripción de columnas", grupos = "descripción de grupos")

#' Síntesis estructurada, sin redacción narrativa (RF-MS-9). Se genera en R.
aida_sintesis_estructurada <- function(h, aviso = NULL) {
  ids_todos <- unlist(lapply(h$grupos, function(g) vapply(g$pares, `[[`, "", "id")))
  if (is.null(ids_todos)) ids_todos <- character(0)
  s <- h$secciones
  t1 <- paste0("Tipo: ", .aida_desc_txt[[h$descripcion]], ". Archivo: ", h$archivo, ". Clases: ", h$n_clases,
               ". Categorías: ", h$n_categorias, ". Asociaciones significativas: ", h$n_significativas,
               # «N de N» sólo si el archivo trae también las no significativas: si no, el total de combinaciones no se conoce.
               if (h$n_no_significativas > 0) paste0(" de ", h$n_pares), ".")
  if (h$n_no_significativas > 0) t1 <- paste0(t1, " Asociaciones no significativas: ", h$n_no_significativas, " (no se listan).")   # R-MS-9
  if (h$n_pares == 0) t1 <- paste0(t1, " La exportación no contiene asociaciones para interpretar.")
  ver_v <- isTRUE(h$visibles$valor_test)
  t2 <- h$texto_s2
  por_tipo <- function(tp) Filter(function(g) g$tipo == tp, h$grupos)
  const <- por_tipo("patrón constante"); sing <- por_tipo("singularidad"); otros <- por_tipo("ni constante ni singularidad")
  bajos <- unlist(lapply(h$grupos, function(g) Filter(function(i) !is.na(i), vapply(g$pares, function(p) if (isTRUE(p$peso_bajo)) p$id else NA_character_, ""))))
  # El novato no conoce los identificadores de las interpretaciones: se le nombra la clase y el conjunto.
  bajos_txt <- if (ver_v) bajos else unlist(lapply(h$grupos, function(g) Filter(function(i) !is.na(i), vapply(g$pares, function(p)
    if (isTRUE(p$peso_bajo)) paste0(.aida_clase_txt(p$clase), " en ", g$conjunto_legible) else NA_character_, ""))))
  lista <- function(gs) paste(vapply(gs, `[[`, "", "conjunto_legible"), collapse = ", ")
  t3 <- if (length(h$grupos) == 0) "No hay asociaciones significativas sobre las que concluir." else c(
    paste0("Conjunto de mayor ", if (ver_v) "fuerza" else "relevancia", ": ", h$grupos[[1]]$conjunto_legible,
           if (ver_v) paste0(" (", .aida_num(h$grupos[[1]]$fuerza, 3), ")"), "."),
    if (length(const)) paste0(if (ver_v) "Patrones constantes: " else "Se asocian con muchas clases (patrones constantes): ", lista(const), "."),
    if (length(sing)) paste0(if (ver_v) "Singularidades: " else "Se asocian con pocas clases (singularidades): ", lista(sing), "."),
    if (length(otros)) paste0("Ni patrón constante ni singularidad: ", lista(otros), "."),
    if (h$n_clases < h$minimo_clases)
      paste0("Con ", h$n_clases, " clases no se distinguen patrones constantes de singularidades."),
    if (h$n_transiciones > 0) paste0("Asociaciones en transición entre categorías contiguas: ", h$n_transiciones, "."),
    if (length(bajos)) paste0("Asociaciones que se apoyan en pocos datos", if (ver_v) " (peso bajo)", ": ", .aida_y_mas(bajos_txt), "."),
    "Sólo las asociaciones listadas son estadísticamente relevantes; las demás combinaciones no superaron el umbral de DaFu.")
  t4 <- paste(vapply(h$limitaciones, `[[`, "", "texto"), collapse = "\n")
  textos <- list(t1, t2, paste(t3, collapse = "\n"), t4)
  ids_de <- function(gs) unlist(lapply(gs, function(g) vapply(g$pares, `[[`, "", "id")))
  ids3 <- unique(c(ids_de(h$grupos[seq_len(min(1, length(h$grupos)))]), ids_de(const), ids_de(sing), ids_de(otros), bajos))
  usados <- list(character(0), ids_todos, if (length(ids3)) ids3 else character(0), character(0))   # RF-MS-10
  if (is.null(aviso)) aviso <- if (h$n_pares == 0) "No hay asociaciones para redactar: se entrega la versión estructurada."
                               else "Síntesis estructurada, sin redacción narrativa."
  list(
    estado = "no redactada",
    aviso = aviso,
    modelo = NA_character_,
    secciones = lapply(seq_along(s), function(k) list(id = s[[k]]$id, nombre = s[[k]]$nombre,
                                                      texto = textos[[k]], interpretaciones = usados[[k]]))
  )
}

# Invoca la parte en Python con reticulate (RF-MS-11). Devuelve la síntesis o un error.
.aida_redactar_python <- function(ruta_h, ruta_kb, modelo) {
  if (!requireNamespace("reticulate", quietly = TRUE)) stop("el paquete reticulate no está instalado")
  py <- getOption("aida.python", Sys.getenv("AIDA_PYTHON", ""))    # Python a usar (RNF-8)
  if (nzchar(py)) {
    if (!reticulate::py_available(initialize = FALSE)) reticulate::use_python(py, required = TRUE)
    ruta_py <- function(x) { r <- normalizePath(x, mustWork = FALSE); if (.Platform$OS.type == "windows") tolower(r) else r }
    if (ruta_py(py) != ruta_py(reticulate::py_config()$python))     # también pasa si RETICULATE_PYTHON indica otro Python
      warning("R está usando otro Python que el indicado en aida.python o AIDA_PYTHON. Reinicie R y revise RETICULATE_PYTHON.", call. = FALSE)
  }
  py_dir <- file.path(aida_home(), "python")
  red <- tryCatch(reticulate::import_from_path("redaccion", path = py_dir, delay_load = FALSE),
                  error = function(e) {
                    if (!grepl("No module named", conditionMessage(e))) stop(e)
                    m <- regmatches(conditionMessage(e), regexec("No module named '([^']+)'", conditionMessage(e)))[[1]][2]
                    exe <- tryCatch(reticulate::py_config()$python, error = function(e2) "python")
                    stop("falta el módulo de Python «", m, "» en ", exe, ". Instálelo con: \"", exe, "\" -m pip install ", m,
                         ", o siga README.md y reinicie RStudio", call. = FALSE)
                  })
  ruta_s <- red$redactar_sintesis(ruta_h, ruta_kb, modelo)
  jsonlite::fromJSON(ruta_s, simplifyVector = FALSE)
}

# Versión de los hallazgos que viaja a Python: de cada conjunto, las `completos` asociaciones de mayor valor test con todos sus
# campos y, del resto, sólo lo que el control del texto necesita (id, clase, valor test, transición) como vectores. Con
# decenas de miles de asociaciones, serializar una lista por asociación era lo que más tardaba. aida_hallazgos() no cambia.
.aida_h_compacto <- function(h, completos = 40) {
  for (i in seq_along(h$grupos)) {
    p <- h$grupos[[i]]$pares
    if (length(p) > completos) {
      resto <- p[(completos + 1):length(p)]
      h$grupos[[i]]$pares <- p[seq_len(completos)]
      h$grupos[[i]]$resto <- list(
        id = I(vapply(resto, `[[`, "", "id")), clase = I(vapply(resto, `[[`, "", "clase")),
        valor_test = I(vapply(resto, function(x) as.numeric(x$valor_test), 0)),
        transicion = I(vapply(resto, `[[`, "", "transicion")))
    }
  }
  h
}

#' Síntesis de una descripción (MS). Llama a Python y, si falla, entrega la versión estructurada.
#' @param redactar FALSE para pedir directamente la versión estructurada.
#' @param modelo modelo del proveedor (por defecto, el configurado en .env o AIDA_MODELO).
aida_sintetizar <- function(interp, perfil = "intermedio", escalado = TRUE, kb = aida_kb(),
                            redactar = TRUE, modelo = getOption("aida.modelo", ""),
                            dir_salida = tempfile("aida_"), variables = NULL, contexto = NULL, conjuntos = NULL) {
  h <- aida_hallazgos(interp, perfil, escalado, kb, variables, contexto, conjuntos)
  dir.create(dir_salida, showWarnings = FALSE, recursive = TRUE)
  ruta_h <- file.path(dir_salida, "hallazgos.json")
  jsonlite::write_json(.aida_h_compacto(h), ruta_h, auto_unbox = TRUE, pretty = FALSE, digits = NA, na = "null")   # NA, NaN e Inf viajan como null
  s <- NULL
  if (isTRUE(redactar) && length(h$grupos) > 0) {
    s <- tryCatch(.aida_redactar_python(ruta_h, .aida_env$kb_ruta, modelo),
                  error = function(e) list(estado = "error", aviso = strsplit(conditionMessage(e), "\n", fixed = TRUE)[[1]][1]))
    if (!(isTRUE(s$estado %in% c("redactada", "parcialmente redactada")))) {
      motivo <- if (length(s$aviso) && nzchar(s$aviso)) paste0(" (", s$aviso, ")") else ""
      rechazados <- s$rechazados                                                 # lo que el modelo escribió y no pasó los controles
      s <- aida_sintesis_estructurada(h, aviso = paste0(
        "No se pudo redactar la síntesis con el modelo de lenguaje", motivo,
        ". Se entrega la versión estructurada."))
      s$rechazados <- rechazados
    }
  } else {
    s <- aida_sintesis_estructurada(h)
  }
  s$hallazgos <- h
  s$ruta_hallazgos <- ruta_h
  class(s) <- "aida_sintesis"
  s
}

# `encabezado = FALSE` omite la línea «Síntesis (estado) · modelo …»: la aplicación no la muestra (el aviso, si lo hay, sí).
print.aida_sintesis <- function(x, encabezado = TRUE, ...) {
  if (isTRUE(encabezado))
    cat("Síntesis (", x$estado, ")", if (isTRUE(!is.na(x$modelo))) paste0(" · modelo ", x$modelo), "\n", sep = "")
  if (!is.null(x$aviso) && nzchar(x$aviso)) cat("Aviso: ", x$aviso, "\n", sep = "")
  for (s in x$secciones) cat("\n## ", s$nombre, "\n", s$texto, "\n", sep = "")
  invisible(x)
}
