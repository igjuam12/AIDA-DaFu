# ─── AIDA · Módulo de Interpretación Automática (RF-MI-1 a RF-MI-8) ──────────
# Aplica las reglas R-MI-1 a R-MI-13 de la base de conocimiento a cada par y
# redacta la interpretación atómica con la plantilla de la regla y del perfil.

# R-MI-1 a R-MI-7: rango del valor test (límites y cierres del frame Rango).
.aida_rango <- function(v, rangos, sin_limite = 1e9) {
  if (is.na(v)) stop("El valor test no es un número (NA o NaN); aida_leer() omite esos pares.", call. = FALSE)
  for (r in rangos) {
    ok_i <- if (isTRUE(r$cierre_inferior)) v >= r$limite_inferior else v > r$limite_inferior
    ok_s <- if (isTRUE(r$cierre_superior)) v <= r$limite_superior else v < r$limite_superior
    if (ok_i && ok_s) return(r)
  }
  # Un valor infinito, o de magnitud igual o mayor que 1,0E9, queda fuera de los límites (R-MI-13): se toma el rango extremo.
  if (abs(v) >= sin_limite) return(if (v > 0) rangos[[1]] else rangos[[length(rangos)]])
  stop("El valor test ", v, " no cae en ningún rango.", call. = FALSE)
}

# Nombre de una categoría difusa: «Are3_20.9a31.4_» (la forma de DaFu) o «CO4.9.5a10.5.» (la misma, con puntos en lugar de guiones bajos,
# como llega de algunos CSV): variable, número de orden y, en la forma con puntos, sólo si el resto es un rango completo.
.aida_num_re <- "-?[0-9]+(?:\\.[0-9]+)?"
.aida_pat_cat <- paste0("^([A-Za-z]+)([0-9]+)(?:_|\\.", .aida_num_re, "a", .aida_num_re, "\\.$)")
.aida_pat_rango <- paste0("^([A-Za-z]+[0-9]+)[_.](", .aida_num_re, ")a(", .aida_num_re, ")[_.]$")

# Variable e índice de una categoría difusa (frame Categoria): "Are3_20.9a31.4_" -> Are, 3.
.aida_categoria <- function(nombre) {
  m <- regmatches(nombre, regexec(.aida_pat_cat, nombre, perl = TRUE))[[1]]
  if (length(m) == 3) list(variable = m[2], indice = as.integer(m[3]))
  else list(variable = nombre, indice = NA_integer_)
}

# Clase compuesta con los nombres de sus variables: "E47_F3" con c("Cepa", "Fecha") -> "E47_F3 (cepa E47, fecha F3)".
# Si no hay nombres, o su cantidad no coincide con la de componentes del nombre, queda igual.
.aida_desglose <- function(x, variables) {
  # Con una sola variable la clase ya es su valor: «E47BIS (tratamiento E47BIS)» no agrega nada.
  if (is.null(variables) || length(variables) < 2) return(x)
  if (length(x) > 50 && anyDuplicated(x)) { u <- unique(x); return(.aida_desglose(u, variables)[match(x, u)]) }
  partes <- strsplit(x, "_", fixed = TRUE)
  ok <- !is.na(x) & lengths(partes) == length(variables) & !grepl("^(la )?clase ", x)
  x[ok] <- vapply(which(ok), function(i) paste0(x[i], " (", paste(tolower(variables), partes[[i]], collapse = ", "), ")"), "")
  x
}

# Nombre de una clase en el texto: si es sólo un número, "76" -> "la clase 76". Otros nombres quedan igual.
.aida_clase_txt <- function(x, articulo = TRUE) {
  num <- !is.na(x) & grepl("^[0-9]+(\\.[0-9]+)?$", x)
  x[num] <- paste0(if (articulo) "la clase " else "clase ", x[num])
  x
}

# Nombre legible de una categoría difusa: "Are2_9.3a20.9_" -> "Are2 (9,3 a 20,9)". Otros nombres quedan igual.
.aida_legible <- function(x) {
  if (length(x) > 50 && anyDuplicated(x)) { u <- unique(x); return(.aida_legible(u)[match(x, u)]) }   # los nombres se repiten: uno por nombre distinto
  pat <- .aida_pat_rango
  ok <- !is.na(x) & grepl(pat, x, perl = TRUE)
  lim1 <- sub(pat, "\\2", x[ok], perl = TRUE); lim2 <- sub(pat, "\\3", x[ok], perl = TRUE)
  # Un intervalo con los dos límites iguales (Are5_53a53_) se muestra con un solo valor, como en el anexo de A6.
  x[ok] <- gsub("\\.", ",", paste0(sub(pat, "\\1", x[ok], perl = TRUE), " (", ifelse(lim1 == lim2, lim1, paste0(lim1, " a ", lim2)), ")"))
  x
}

# Plantilla de la regla y del perfil; si no hay variante para el perfil, la general.
.aida_plantilla <- function(regla, perfil, kb) {
  pl <- kb$plantillas
  cand <- Filter(function(p) regla %in% unlist(p$reglas), pl)
  esp <- Filter(function(p) p$perfil == perfil, cand)
  if (length(esp)) return(esp[[1]])
  gen <- Filter(function(p) p$perfil == "todos", cand)
  if (length(gen)) return(gen[[1]])
  stop("No hay plantilla para la regla ", regla, call. = FALSE)
}

# Completa los campos [campo] de una plantilla en una sola pasada: lo que se inserta no se vuelve a
# analizar, de modo que un nombre de clase como "[V]" no se confunde con un campo.
.aida_completar <- function(texto, valores) .aida_completar_vec(texto, valores, 1L)

# Lo mismo para n asociaciones a la vez: `valores` es una lista de vectores de largo n (o 1), uno por campo. La plantilla se
# parte una sola vez en sus trozos fijos y se pegan los vectores (con miles de asociaciones, completar de a una era lo más lento).
# `cortos` da, para algunos campos, la forma breve que se usa de la segunda aparición en adelante: la clase se presenta una
# vez con su desglose («E47_F1 (cepa E47, fecha F1)») y después sólo con su nombre.
.aida_completar_vec <- function(texto, valores, n, cortos = NULL) {
  texto <- gsub("p = [p]", "[p]", texto, fixed = TRUE)   # [p] es el texto del p-valor (R-MI-9)
  m <- gregexpr("\\[[^]]+\\]", texto)
  campos <- regmatches(texto, m)[[1]]
  if (length(campos) == 0) return(rep(texto, n))
  fijos <- regmatches(texto, m, invert = TRUE)[[1]]        # un trozo fijo antes, entre y después de los campos
  nombres <- substr(campos, 2, nchar(campos) - 1)
  out <- rep(fijos[1], n)
  for (k in seq_along(campos)) {
    repetido <- nombres[k] %in% nombres[seq_len(k - 1)]
    v <- if (repetido && nombres[k] %in% names(cortos)) as.character(cortos[[nombres[k]]])
         else if (nombres[k] %in% names(valores)) as.character(valores[[nombres[k]]]) else campos[k]
    out <- paste0(out, v, fijos[k + 1])
  }
  out
}

# Lista de categorías contiguas escrita en español: "A", "A y B", "A, B y C".
.aida_enumerar <- function(x) {
  x <- x[nzchar(x)]
  if (length(x) <= 1) return(paste(x, collapse = ""))
  paste0(paste(x[-length(x)], collapse = ", "), " y ", x[length(x)])
}

# Nombres legibles de las categorías contiguas de cada asociación («Are2_9.3a20.9_, Are4_31.4a43.4_»), unidos con `unir`.
# Las combinaciones distintas son pocas (a lo sumo, pares de conjuntos vecinos): se resuelven una vez cada una.
.aida_contiguas_legibles <- function(contigua, unir) {
  u <- unique(contigua)
  vapply(strsplit(u, ", ", fixed = TRUE), function(x) unir(.aida_legible(x)), "")[match(contigua, u)]
}

#' Interpreta los pares leídos (MI).
#' @param pares resultado de aida_leer().
#' @param perfil "novato", "intermedio" o "experto".
#' @return data.frame con una interpretación atómica por par (A5, 5.3).
aida_interpretar <- function(pares, perfil = "intermedio", kb = aida_kb(), variables = NULL) {
  .aida_validar_perfil(perfil, kb)
  n <- nrow(pares)
  desc <- attr(pares, "descripcion")
  out <- pares
  out$id <- if (n) paste0(toupper(substr(desc, 1, 3)), "-", pares$id_par) else character(0)  # RF-MI-7
  if (n == 0) {
    for (k in c("regla", "estado", "significacion", "direccion", "intensidad", "p_texto",
                "advertencias", "plantilla", "contigua", "texto")) out[[k]] <- character(0)
    out$peso_bajo <- logical(0); out$es_significativa <- logical(0); out$es_transicion <- logical(0)
    out$extrema <- logical(0); out$razon <- numeric(0); out$perfil <- character(0)
    attr(out, "descripcion") <- desc; attr(out, "archivo") <- attr(pares, "archivo")
    return(out)
  }
  p_exacto <- .aida_param(kb, "umbral_p_exacto")
  peso_min <- .aida_param(kb, "umbral_peso_bajo")
  dist <- .aida_param(kb, "distancia_contigua")

  # R-MI-1 a R-MI-7: regla y estado interpretado.
  # El rango se busca una vez por valor distinto (con muchos datos los valores test se repiten).
  v_unicos <- unique(pares$valor_test); cual <- match(pares$valor_test, v_unicos)
  rg <- lapply(v_unicos, .aida_rango, rangos = kb$rangos, sin_limite = kb$metadatos$sin_limite)
  out$regla <- vapply(rg, function(r) r$regla, "")[cual]
  out$estado <- vapply(rg, function(r) r$estado, "")[cual]
  de_estado <- function(campo) unname(vapply(kb$estados, function(e) e[[campo]], "")[out$estado])
  out$significacion <- de_estado("significacion")
  out$direccion <- de_estado("direccion")
  out$intensidad <- de_estado("intensidad")
  out$es_significativa <- out$significacion != "no significativo"            # R-MS-1

  # R-MI-9 y R-MI-13: texto del p-valor; valor test no finito.
  out$extrema <- !is.finite(pares$valor_test)
  out$p_texto <- ifelse(pares$p_valor >= p_exacto, paste0("p = ", .aida_num(pares$p_valor, 3)),
                        paste0("p < ", .aida_num(p_exacto, 2)))
  # Cada p-valor con su propio formato: format() sobre el vector les daría a todos los decimales del más largo.
  out$p_texto[out$extrema] <- paste0("p = ", vapply(pares$p_valor[out$extrema], format, "", decimal.mark = ",", scientific = FALSE))

  # R-MI-11: peso bajo de la línea (Global). R-MI-8: AD1 en toda interpretación.
  out$peso_bajo <- !is.na(pares$global) & pares$global < peso_min
  ad <- kb$advertencias
  ad_de <- function(disparador) names(Filter(function(a) identical(a$disparador, disparador), ad))
  siempre <- ad_de("siempre"); por_peso <- ad_de("peso_bajo")          # RNF-3: el disparador sale de la base de conocimiento
  out$advertencias <- ifelse(out$peso_bajo, paste(c(siempre, por_peso), collapse = ";"), paste(siempre, collapse = ";"))

  # Razón de proporciones (perfil experto, V2 de A5): Cat.Class / Global.
  out$razon <- ifelse(pares$global > 0, pares$cat_class / pares$global, NA_real_)

  # R-MI-12: transición entre categorías contiguas de la misma variable en una clase.
  # Se compara sólo dentro de cada grupo (clase, variable) para que el costo no crezca con el cuadrado de n.
  # La misma lectura que .aida_categoria(), para todas a la vez.
  difusa <- grepl(.aida_pat_cat, pares$categoria, perl = TRUE)
  variable <- ifelse(difusa, sub("^([A-Za-z]+)(\\d+).*$", "\\1", pares$categoria), pares$categoria)
  indice <- rep(NA_integer_, n); indice[difusa] <- as.integer(sub("^([A-Za-z]+)(\\d+).*$", "\\2", pares$categoria[difusa]))
  es_transicion <- logical(n); contigua <- character(n)       # vectores sueltos: asignar de a un elemento en la tabla la copia entera
  cand <- which(out$es_significativa & !is.na(indice))
  for (g in split(cand, paste(pares$clase[cand], variable[cand], sep = "\r"))) {
    if (length(g) < 2) next
    for (i in g) {
      j <- g[g != i & abs(indice[g] - indice[i]) == dist]
      if (length(j)) {
        es_transicion[i] <- TRUE
        contigua[i] <- paste(pares$categoria[j], collapse = ", ")
      }
    }
  }
  out$es_transicion <- es_transicion; out$contigua <- contigua

  # RF-MI-2, RF-MI-3, RF-PU-2: plantilla de la regla y del perfil, con los datos visibles del perfil.
  pt <- .aida_plantilla("R-MI-12", perfil, kb)
  por_regla <- list()
  for (r in unique(out$regla)) por_regla[[r]] <- .aida_plantilla(r, perfil, kb)
  leg <- lapply(list(bloque = pares$bloque, linea = pares$linea, clase = pares$clase, categoria = pares$categoria), .aida_legible)
  # Una clase que es sólo un número se escribe «la clase N», para no leerla como una cifra (ni confundirla al verificar el texto).
  # `breve` es el mismo nombre sin el desglose en variables: se usa cuando la clase ya se presentó en la misma interpretación.
  breve <- leg
  for (campo in c("bloque", "linea", "clase")) {
    es_clase <- which(pares[[campo]] == pares$clase)
    breve[[campo]][es_clase] <- .aida_clase_txt(leg[[campo]][es_clase])
    leg[[campo]][es_clase] <- .aida_desglose(breve[[campo]][es_clase], variables)
  }
  # Los números se escriben una sola vez, en bloque (formatC por asociación era lo que más tardaba con muchos datos).
  num_v <- .aida_num(pares$valor_test, 3); num_cc <- .aida_num(pares$cat_class, 1); num_cl <- .aida_num(pares$class_cat, 1)
  num_g <- .aida_num(pares$global, 1); num_r <- .aida_num(out$razon, 2)
  txt_siempre <- paste(vapply(ad[siempre], function(a) a$texto, ""), collapse = " ")
  txt_peso <- paste(vapply(ad[por_peso], function(a) a$texto, ""), collapse = " ")
  out$plantilla <- ""; out$texto <- ""
  for (r in names(por_regla)) {                           # una pasada por regla (son 7 a lo sumo), no por asociación
    pl <- por_regla[[r]]; w <- which(out$regla == r)
    val <- list(
      "bloque" = leg$bloque[w], "línea" = leg$linea[w],
      "clase" = leg$clase[w], "categoría" = leg$categoria[w],
      "V" = num_v[w], "p" = out$p_texto[w],
      "Cat.Class" = num_cc[w], "Class.Cat" = num_cl[w],
      "Global" = num_g[w], "razón" = num_r[w],
      "significación" = out$significacion[w], "regla" = out$regla[w])
    cortos <- list("bloque" = breve$bloque[w], "línea" = breve$linea[w], "clase" = breve$clase[w])
    txt <- sub("^la clase ", "La clase ", .aida_completar_vec(pl$texto, val, length(w), cortos))
    # Las variantes por perfil ya expresan AD1 con el registro del perfil; la plantilla general no.
    if (pl$perfil == "todos") txt <- paste(txt, txt_siempre)
    out$plantilla[w] <- pl$id
    out$texto[w] <- txt
  }
  w <- which(out$peso_bajo)                                                     # R-MI-11
  if (length(w)) out$texto[w] <- paste(out$texto[w], txt_peso)
  w <- which(out$es_transicion)                                                 # R-MI-12
  if (length(w)) {
    contiguas <- .aida_contiguas_legibles(out$contigua[w], .aida_enumerar)
    # La clase ya se presentó con su desglose en la oración anterior: aquí va sólo su nombre.
    out$texto[w] <- paste(out$texto[w], sub("^la clase ", "La clase ", .aida_completar_vec(pt$texto, list(
      "clase" = breve$clase[w], "categoría" = leg$categoria[w], "contigua" = contiguas, "variable" = variable[w]), length(w))))
  }
  out$perfil <- perfil
  attr(out, "descripcion") <- desc
  attr(out, "archivo") <- attr(pares, "archivo")
  out
}
