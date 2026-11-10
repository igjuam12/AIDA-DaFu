# Pruebas de la parte en R (criterios de aceptación de A5, sección 14, que corresponden a A10).
# Ejecutar desde la carpeta aida:  testthat::test_dir("tests/testthat")

if (is.null(getOption("aida.home"))) source(file.path("..", "..", "cargar.R"), encoding = "UTF-8")
ej <- function(f) file.path(getOption("aida.home"), "ejemplos", f)

test_that("RF-LE-1 a RF-LE-5: lee las exportaciones de referencia", {
  expect_equal(nrow(aida_leer(ej("Area__Fuzzy_csv_DescGrp.txt"))), 22)
  expect_equal(nrow(aida_leer(ej("entropy__Fuzzy_csv_DescGrp.txt"))), 7)
  fil <- aida_leer(ej("HorasDocencia_csv_DescFil.txt"))
  col <- aida_leer(ej("HorasDocencia_csv_DescCol.txt"))
  expect_equal(c(nrow(fil), nrow(col)), c(41, 41))
  expect_equal(attr(col, "descripcion"), "columnas")
  expect_type(fil$clase, "character")                       # RF-LE-4: 9001 es texto
  expect_true("9001" %in% fil$clase)
  # En la descripción de columnas la clase es la línea y la categoría el bloque.
  expect_equal(col$clase[1], "9006"); expect_equal(col$categoria[1], "CaFun")
  expect_equal(nrow(aida_leer(ej("HorasDocencia_csv_DescGrp.txt"))), 0)   # RF-LE-5
})

test_that("RF-LE-6: rechaza un archivo con otro formato", {
  expect_error(aida_leer(c("hola", "mundo")), "no tiene el formato")
  expect_error(aida_leer(c("Descripción filas en función columnas", "class: A", "basura sin formato")), "formato")
})

test_that("RF-LE-2: acepta bloques con varias variables de agrupación", {
  txt <- c('$t0', '[1] "Descripción grupos filas en función columnas"', '', '$grupo',
           'Temperatura: T40', 'Dia: jueves',
           '     Test.Value p.Value Class.Cat Cat.Class Global   Weight',
           'HCC2     20.640   0.000       2.4      14.1    5.2 22243.85')
  p <- aida_leer(txt)
  expect_equal(p$clase, "T40_jueves")
})

test_that("RF-MI-1: la regla asignada coincide con la esperada en los 70 pares distintos", {
  r <- c(aida_interpretar(aida_leer(ej("Area__Fuzzy_csv_DescGrp.txt")))$regla,
         aida_interpretar(aida_leer(ej("entropy__Fuzzy_csv_DescGrp.txt")))$regla,
         aida_interpretar(aida_leer(ej("HorasDocencia_csv_DescFil.txt")))$regla)
  expect_equal(as.vector(table(r)[c("R-MI-1", "R-MI-2", "R-MI-3")]), c(52, 11, 7))
})

test_that("RF-MI-8: reglas latentes con casos construidos para cada rango", {
  v <- c(-3, -2.58, -2, -1.96, -1.7, -1.65, 0.5, 1.65, 1.7, 1.96, 2, 2.58, 13.202)
  esperado <- c("R-MI-7", "R-MI-7", "R-MI-6", "R-MI-6", "R-MI-5", "R-MI-5", "R-MI-4",
                "R-MI-3", "R-MI-3", "R-MI-2", "R-MI-2", "R-MI-1", "R-MI-1")
  txt <- c("Descripción filas en función columnas", "class: K",
           "     Test.Value p.Value Class.Cat Cat.Class Global   Weight",
           sprintf("C%02d %s 0.010 10.0 10.0 10.0 100", seq_along(v), v))
  for (pf in c("novato", "intermedio", "experto")) {
    i <- aida_interpretar(aida_leer(txt), pf)
    expect_equal(i$regla, esperado)
    expect_true(all(nzchar(i$texto)))
  }
})

test_that("RF-MI-5, R-MI-11, R-MI-12 y R-MI-13", {
  i <- aida_interpretar(aida_leer(ej("HorasDocencia_csv_DescFil.txt")), "experto")
  expect_true(any(grepl("p < 0,01", i$texto)))
  expect_true(any(grepl("p = 0,015", i$texto)))
  expect_equal(sum(i$peso_bajo), 4)
  a <- aida_interpretar(aida_leer(ej("Area__Fuzzy_csv_DescGrp.txt")))
  expect_equal(sort(unique(a$clase[a$es_transicion])), c("E47_F1_D", "ECO_F2_D", "ECO_F3_D", "ECO_F3_F"))
  txt <- c("Descripción filas en función columnas", "class: K",
           "     Test.Value p.Value Class.Cat Cat.Class Global   Weight", "C1 Inf 0 10 10 10 100")
  x <- aida_interpretar(aida_leer(txt))
  expect_true(x$extrema); expect_equal(x$regla, "R-MI-1")
})

test_that("RF-MS-1 a RF-MS-5: grupos y orden del caso del área", {
  h <- aida_hallazgos(aida_interpretar(aida_leer(ej("Area__Fuzzy_csv_DescGrp.txt"))))
  f <- vapply(h$grupos, `[[`, 0, "fuerza")
  expect_equal(vapply(h$grupos, `[[`, "", "conjunto"),
               c("Are1_1.3a9.3_", "Are5_53a53_", "Are3_20.9a31.4_", "Are2_9.3a20.9_", "Are4_31.4a43.4_"))
  expect_equal(round(f, 3), c(70.068, 41.164, 38.234, 37.514, 37.372))
  expect_true(all(vapply(h$grupos, `[[`, "", "tipo") == "singularidad"))
  v <- vapply(h$grupos[[1]]$pares, `[[`, 0, "valor_test")
  expect_false(is.unsorted(rev(abs(v))))
})

test_that("RF-PU-4: mismos hallazgos para los tres perfiles", {
  it <- aida_interpretar(aida_leer(ej("Area__Fuzzy_csv_DescGrp.txt")))
  g <- lapply(c("novato", "intermedio", "experto"), function(pf) aida_hallazgos(it, pf)$grupos)
  expect_identical(g[[1]], g[[2]]); expect_identical(g[[2]], g[[3]])
  t <- vapply(c("novato", "intermedio", "experto"),
              function(pf) aida_interpretar(aida_leer(ej("Area__Fuzzy_csv_DescGrp.txt")), pf)$texto[1], "")
  expect_equal(length(unique(t)), 3)
  expect_false(grepl("9,003", t[["novato"]]))               # el novato no ve el valor test
  expect_true(grepl("p < 0,01", t[["experto"]]))
})

test_that("RF-MS-9: síntesis estructurada con las cuatro secciones", {
  r <- aida(ej("entropy__Fuzzy_csv_DescGrp.txt"), redactar = FALSE)
  expect_equal(r$sintesis$estado, "no redactada")
  expect_equal(vapply(r$sintesis$secciones, `[[`, "", "id"), c("S1", "S2", "S3", "S4"))
  expect_true(grepl("escalada", r$sintesis$secciones[[4]]$texto))
  expect_true(grepl("conjuntos difusos", r$sintesis$secciones[[4]]$texto))
})

test_that("RF-MS-11: intercambio con Python (modelo simulado)", {
  skip_if_not(reticulate::py_module_available("jinja2"))
  it <- aida_interpretar(aida_leer(ej("entropy__Fuzzy_csv_DescGrp.txt")))
  dir <- tempfile(); dir.create(dir)
  h <- aida_hallazgos(it); ruta <- file.path(dir, "hallazgos.json")
  jsonlite::write_json(h, ruta, auto_unbox = TRUE, digits = NA)
  red <- reticulate::import_from_path("redaccion", path = file.path(getOption("aida.home"), "python"))
  falso <- function(prompt) jsonlite::toJSON(list(S1 = "Se analizaron 3 clases.",
    S2 = "El conjunto ent1_4.6a4.9_ encabeza los resultados.",
    S3 = "Sólo las asociaciones listadas son relevantes."), auto_unbox = TRUE)
  s <- jsonlite::fromJSON(red$redactar_sintesis(ruta, .aida_env$kb_ruta, "simulado", falso), simplifyVector = FALSE)
  expect_equal(s$estado, "parcialmente redactada")          # S2 se pide con la clave «texto», que esta respuesta no trae
  falso2 <- function(prompt) jsonlite::toJSON(list(S1 = "Se analizaron 37 clases.", S2 = "x", S3 = "y"), auto_unbox = TRUE)
  s2 <- jsonlite::fromJSON(red$redactar_sintesis(ruta, .aida_env$kb_ruta, "simulado", falso2), simplifyVector = FALSE)
  expect_equal(s2$estado, "no verificada")                  # R-MS-12
})

# ─── Correcciones de la revisión del 26/10/2026 ──────────────────────────────

tabla <- function(clase, cat, v, p = 0.001, cc = 10, ctc = 30, g = 20, w = 99)
  c(paste0("class: ", clase),
    "Test.Value p.Value Class.Cat Cat.Class Global Weight",
    sprintf("%s %s %s %s %s %s %s", cat, v, p, cc, ctc, g, w), strrep("-", 40))
titulo <- "Descripción filas en función columnas "

test_that("RF-LE-2: lee la tabla que print() parte en dos y los bloques NULL", {
  l <- c(titulo, "class: 9001",
         "                    Test.Value p.Value Class.Cat",
         "Variable_larga_1.3a9.3_   3.100   0.001      10.0",
         "Otra_2_                  -2.000   0.040       5.0", "",
         "                    Cat.Class Global Weight",
         "Variable_larga_1.3a9.3_  30.0 20.0 99.0",
         "Otra_2_                   4.0  9.0 99.0", strrep("-", 40),
         "class: 9002", "NULL", strrep("-", 40))
  x <- aida_leer(l)
  expect_equal(nrow(x), 2)
  expect_equal(x$global, c(20, 9)); expect_equal(x$valor_test, c(3.1, -2))
})

test_that("RF-LE-3: los pares con NaN se omiten con aviso y no rompen la interpretación", {
  l <- c(titulo, tabla("A", "Are1_1_", "NaN"), tabla("B", "Are1_1_", "3.2"))
  expect_warning(x <- aida_leer(l), "Se omiten 1 pares")
  expect_equal(nrow(x), 1)
  expect_silent(aida_interpretar(x))
  expect_error(aida_interpretar(transform(x, valor_test = NaN)), "no es un número")
})

test_that("RF-LE-1: lee un TXT en Windows-1252 y avisa si no es texto", {
  f <- tempfile(fileext = ".txt")
  con <- file(f, "wb"); writeBin(iconv(c(titulo, tabla("A", "Are1_1_", "3.2")), "UTF-8", "latin1"), con); close(con)
  writeBin(iconv(paste0(c(titulo, tabla("A", "Are1_1_", "3.2")), collapse = "\n"), "UTF-8", "latin1", toRaw = TRUE)[[1]], f)
  expect_equal(attr(aida_leer(f), "descripcion"), "filas")
  expect_error(aida_leer(tempdir()), "carpeta")
  expect_equal(nrow(aida_leer(titulo)), 0)                    # un título solo es una exportación sin pares
})

test_that("RF-MI: un nombre de clase igual a un campo de plantilla no se reemplaza", {
  x <- aida_interpretar(aida_leer(c(titulo, tabla("[V]", "Are1_1_", "3.2"), tabla("[p]", "Are2_2_", "2.0"))), "novato")
  expect_true(all(grepl("\\[V\\]|\\[p\\]", x$texto)))
  expect_false(any(grepl("3,200|p < 0,01", x$texto)))
})

test_that("R-MI-9 y R-MI-12: texto del p-valor y frase de transición", {
  l <- c(titulo, tabla("C", "Are1_1_", "3.2"), tabla("C", "Are2_2_", "3.0"), tabla("C", "Are3_3_", "2.9"))
  x <- aida_interpretar(aida_leer(l), "intermedio")
  expect_true(all(x$es_transicion))
  expect_match(x$texto[2], "Are1_1_ y Are3_3_")                       # lista con «y», no con coma
  e <- aida_interpretar(aida_leer(c(titulo, tabla("C", "Are1_1_", "Inf", p = 0))), "experto")
  expect_match(e$texto, "p = 0")                                       # R-MI-13 tiene prioridad sobre R-MI-9
})

test_that("RF-MI-4: todas las reglas R-MI-1 a R-MI-7 tienen texto por perfil, sin campos sin completar", {
  v <- c(3, 2.2, 1.8, 0.5, -1.7, -2.0, -3)
  l <- c(titulo, unlist(lapply(seq_along(v), function(k) tabla(paste0("K", k), "Cat_x", v[k]))))
  for (pf in c("novato", "intermedio", "experto")) {
    x <- aida_interpretar(aida_leer(l), pf)
    expect_equal(x$regla, paste0("R-MI-", 1:7))
    expect_false(any(grepl("\\[|NA|NaN|Inf", x$texto)), info = pf)
  }
  nov <- aida_interpretar(aida_leer(l), "novato")$texto
  expect_equal(length(unique(nov[5:7])), 3)                            # el novato distingue los tres niveles negativos
  expect_false(any(grepl("valor test|p = ", nov)))                     # y no ve el valor test ni el p-valor
})

test_that("RNF-2: dos ejecuciones dan la misma salida y el orden de empates no depende del idioma", {
  l <- c(titulo, tabla("b", "Are1_1_", "3"), tabla("B", "Are1_1_", "3"), tabla("a", "Are1_1_", "3"))
  a <- aida(l, redactar = FALSE); b <- aida(l, redactar = FALSE)
  expect_identical(a$interpretaciones, b$interpretaciones)
  expect_identical(a$sintesis$secciones, b$sintesis$secciones)
  clases <- vapply(a$sintesis$hallazgos$grupos[[1]]$pares, `[[`, "", "clase")
  expect_equal(clases, c("B", "a", "b"))                               # orden por punto de código, como en Python
})

test_that("RNF-3: el texto del p-valor sigue al parámetro de la base de conocimiento", {
  kb <- aida_kb(); kb$parametros$umbral_p_exacto$valor <- 0.05
  x <- aida_interpretar(aida_leer(c(titulo, tabla("A", "Are1_1_", "2.1", p = 0.037)), kb), "experto", kb)
  expect_match(x$texto, "p < 0,05")
  y <- aida_interpretar(aida_leer(c(titulo, tabla("A", "Are1_1_", "2.1", p = 0.06)), kb), "experto", kb)
  expect_match(y$texto, "p = 0,060")
})

test_that("RF-MS-9: la síntesis estructurada informa el peso bajo y el caso sin asociaciones", {
  x <- aida(c(titulo, tabla("A", "Are1_1_", "3", g = 1.5)), redactar = FALSE)
  expect_match(x$sintesis$secciones[[3]]$texto, "peso bajo")
  v <- suppressMessages(aida(titulo, redactar = FALSE))
  expect_match(v$sintesis$secciones[[3]]$texto, "No hay asociaciones")
  f <- tempfile(fileext = ".md"); aida_guardar(v, f); expect_true(any(grepl("Sin interpretaciones", readLines(f))))
})

test_that("RF-MS-11: NA, NaN e Inf viajan al JSON como null", {
  x <- aida(c(titulo, tabla("A", "Are1_1_", "3", g = 0)), redactar = FALSE)
  j <- paste(readLines(x$sintesis$ruta_hallazgos), collapse = "")
  expect_match(j, "\"razon\":\\s*null")
})

test_that("RNF: rendimiento, 1.500 pares se procesan en pocos segundos", {
  l <- c(titulo, "class: C", "Test.Value p.Value Class.Cat Cat.Class Global Weight",
         sprintf("Var%d_%d_ 3.0 0.001 10 30 20 99", rep(1:30, each = 50), rep(1:50, times = 30)))
  expect_lt(system.time(aida_interpretar(aida_leer(l)))[["elapsed"]], 10)
})

test_that("aida() valida sus argumentos con mensajes en español", {
  expect_error(aida(titulo, escalado = "si"), "escalado")
  expect_error(aida(titulo, perfil = NULL), "Perfil no válido")
  expect_error(aida(titulo, perfil = "Experto"), "Perfil no válido")
})


# ── Pruebas agregadas en la segunda revisión ──
# Pruebas propuestas (segunda auditoría). Usan los ayudantes tabla() y titulo de test_aida.R.
if (!exists("tabla")) {
  tabla <- function(clase, cat, v, p = 0.001, cc = 10, ctc = 30, g = 20, w = 99)
    c(paste0("class: ", clase), "Test.Value p.Value Class.Cat Cat.Class Global Weight",
      sprintf("%s %s %s %s %s %s %s", cat, v, p, cc, ctc, g, w), strrep("-", 40))
  titulo <- "Descripción filas en función columnas "
}
tipos_de <- function(k, n, cat = "Are1_1_") {      # la categoría aparece en k de n clases
  l <- c(titulo, unlist(lapply(seq_len(n), function(i)
    if (i <= k) tabla(paste0("K", i), cat, "3") else tabla(paste0("K", i), "Otra1_1_", "0.5"))))
  aida_hallazgos(aida_interpretar(aida_leer(l)))$grupos[[1]]$tipo
}

test_that("R-MS-5/6: tipo de patrón en los bordes de las etiquetas difusas y del mínimo de clases", {
  expect_equal(tipos_de(3, 3), "sin clasificar")               # n < minimo_clases
  expect_equal(tipos_de(1, 4), "singularidad")                 # n == minimo_clases ya se clasifica
  expect_equal(tipos_de(3, 8), "singularidad")                 # 0,375: pertenencia a «algunas» = corte exacto
  expect_equal(tipos_de(5, 12), "ni constante ni singularidad")
  expect_equal(tipos_de(9, 20), "patrón constante")            # 0,45: pertenencia a «muchas» = corte exacto
  expect_equal(tipos_de(4, 4), "patrón constante")             # proporción 1 (extremo del trapecio)
})

test_that("RF-MS-4: empate de fuerza entre conjuntos se ordena por punto de código", {
  l <- c(titulo, tabla("C", "a1_1_", "3"), tabla("C", "B1_1_", "3"), tabla("C", "b1_1_", "3"))
  g <- aida_hallazgos(aida_interpretar(aida_leer(l)))$grupos
  expect_equal(vapply(g, `[[`, "", "conjunto"), c("B1_1_", "a1_1_", "b1_1_"))
})

test_that("RF-LE-2/3: tabla partida con filas desalineadas y valores no numéricos", {
  p <- function(segunda) c(titulo, "class: K", "Test.Value p.Value Class.Cat", "A_1_ 3.1 0.001 10", "B_2_ 2.0 0.04 5",
                           "", "Cat.Class Global Weight", segunda, strrep("-", 20))
  expect_error(aida_leer(p(c("B_2_ 4 9 99", "A_1_ 30 20 99"))), "no coinciden")
  expect_error(aida_leer(p("A_1_ 30 20 99")), "no coinciden|falta")
  expect_error(aida_leer(c(titulo, tabla("K", "A_1_", "abc"))), "no numéricos")
  for (col in c("p", "ctc", "g")) {                                   # NaN en p-valor, Cat.Class o Global
    a <- list(v = "3", p = 0.001, ctc = 30, g = 20); a[[col]] <- "NaN"
    expect_warning(x <- aida_leer(c(titulo, tabla("K", "A_1_", a$v, p = a$p, ctc = a$ctc, g = a$g))), "Se omiten", info = col)
    expect_equal(nrow(x), 0, info = col)
  }
  expect_warning(aida_leer(c(titulo, tabla("K", "A_1_", "3", p = 1.5))), "fuera de su dominio")
})

test_that("RF-LE-1: BOM UTF-8 y fin de línea de Windows en un archivo", {
  f <- tempfile(fileext = ".txt")
  writeBin(c(as.raw(c(0xEF, 0xBB, 0xBF)), charToRaw(enc2utf8(paste0(paste(c(titulo, tabla("A", "Are1_1_", "3.2")), collapse = "\r\n"), "\r\n")))), f)
  x <- aida_leer(f); expect_equal(nrow(x), 1); expect_equal(attr(x, "descripcion"), "filas")
  y <- aida_leer(c(paste0("\ufeff", titulo), tabla("A", "Are1_1_", "3.2"))); expect_equal(nrow(y), 1)
})

test_that("R-MI-8/9/11: bordes exactos de los umbrales y de los rangos", {
  g <- function(v) aida_interpretar(aida_leer(c(titulo, tabla("A", "Are1_1_", "3", g = v))))
  expect_false(g(2.0)$peso_bajo); expect_true(g(1.99)$peso_bajo)         # Global = umbral no es peso bajo
  expect_match(g(1.99)$texto, "pocos datos")                              # y se añade AD2
  pp <- function(p) aida_interpretar(aida_leer(c(titulo, tabla("A", "Are1_1_", "3", p = p))))$p_texto
  expect_equal(pp(0.01), "p = 0,010"); expect_equal(pp(0.0099), "p < 0,01")
  r <- function(v) aida_interpretar(aida_leer(c(titulo, tabla("A", "Are1_1_", v))))$regla
  expect_equal(c(r("1000000000"), r("-1000000000")), c("R-MI-1", "R-MI-7"))   # 1,0E9 exacto cae en el extremo
  x <- g(0); expect_true(is.na(x$razon))                                   # Global = 0: razón no calculable
})

test_that("R-MS-1/3: lo no significativo no forma conjuntos y la fuerza suma valores absolutos", {
  h <- aida_hallazgos(aida_interpretar(aida_leer(c(titulo, tabla("A", "Are1_1_", "0.5")))))
  expect_equal(c(h$n_significativas, length(h$grupos)), c(0, 0))
  h2 <- aida_hallazgos(aida_interpretar(aida_leer(c(titulo, tabla("A", "Are1_1_", "3"), tabla("B", "Are1_1_", "-2.1")))))
  expect_equal(h2$grupos[[1]]$fuerza, 5.1)
})

test_that("R-MI-12: dos categorías no contiguas, o de otra clase, no son transición", {
  x <- aida_interpretar(aida_leer(c(titulo, tabla("C", "Are1_1_", "3"), tabla("C", "Are3_3_", "3"), tabla("D", "Are2_2_", "3"))))
  expect_false(any(x$es_transicion))
})

test_that("R-MS-10, RF-MI-3, RF-MI-9: limitaciones por escalado, prefijo de id y plantilla general", {
  l <- c(titulo, tabla("A", "Are1_1_", "3"))
  expect_match(aida(l, escalado = TRUE, redactar = FALSE)$sintesis$secciones[[4]]$texto, "fue escalada antes")
  expect_match(aida(l, escalado = FALSE, redactar = FALSE)$sintesis$secciones[[4]]$texto, "no fue escalada")
  expect_match(aida(l, redactar = FALSE)$interpretaciones$id, "^FIL-P001$")
  expect_match(aida(c("Descripción grupos filas en función columnas", l[-1]), redactar = FALSE)$interpretaciones$id[1], "^GRU-P")
  kb <- aida_kb(); kb$plantillas <- Filter(function(p) p$perfil == "todos", kb$plantillas)
  x <- aida_interpretar(aida_leer(l, kb), "novato", kb)
  expect_match(x$texto, "El valor test indica la significación")      # AD1 se agrega a la plantilla general
})


test_that("lectura: tablas partidas con cualquier corte de columnas", {
  for (nch in c(5, 25, 32, 40, 60, 75)) {
    nom <- c(strrep("a", nch), strrep("b", nch))
    d <- data.frame(Test.Value = c(3.1, 2.5), p.Value = c(0.001, 0.04), Class.Cat = c(10, 5),
                    Cat.Class = c(30, 20), Global = c(20, 15), Weight = c(99, 80), row.names = nom)
    salida <- utils::capture.output(print(d))
    x <- aida_leer(c(titulo, "class: K", salida))
    expect_equal(nrow(x), 2, info = nch)
  }
})

test_that("lectura: separadores \\r, NA y UTF-8 inválido en el vector de líneas", {
  l <- paste(c(titulo, tabla("K", "A_1_", "3")), collapse = "\r")
  expect_equal(nrow(aida_leer(l)), 1)
  expect_error(aida_leer(c(titulo, NA)), "NA")
})

test_that(".aida_num no escribe «-0,00»", {
  expect_equal(.aida_num(-0.001, 2), "0,00")
})

test_that("síntesis estructurada del novato no muestra valor test ni fuerza", {
  l <- c(titulo, tabla("K", "A_1_", "13.011"))
  s <- aida(l, perfil = "novato", redactar = FALSE)$sintesis
  txt <- paste(vapply(s$secciones, `[[`, "", "texto"), collapse = "\n")
  expect_false(grepl("V = |fuerza|13,011", txt))
})

test_that("aida() rechaza una base de conocimiento inválida", {
  expect_error(aida(c(titulo, tabla("K", "A_1_", "3")), kb = NULL), "base de conocimiento")
})

# ─── Correcciones de la revisión del 04/11/2026 ──────────────────────────────

test_that("RF-PU-2: el Markdown y la tabla del novato no muestran regla, valor test ni p-valor", {
  r <- aida(ej("HorasDocencia_csv_DescFil.txt"), perfil = "novato", redactar = FALSE)
  f <- tempfile(fileext = ".md"); aida_guardar(r, f)
  md <- paste(readLines(f, encoding = "UTF-8"), collapse = "\n")
  expect_false(grepl("R-MI-|valor test|p-valor|p < |fuerza|FIL-P018,|Interpretaciones: ", md))
  expect_true(grepl("FIL-P001", md))                                    # RF-MI-7: el identificador se conserva
  expect_equal(names(aida_tabla(r)), c("id", "clase", "categoria", "texto"))
})

test_that("RF-PU-2: los otros perfiles sí ven la regla y lo que les corresponde", {
  for (pf in c("intermedio", "experto")) {
    r <- aida(ej("HorasDocencia_csv_DescFil.txt"), perfil = pf, redactar = FALSE)
    f <- tempfile(fileext = ".md"); aida_guardar(r, f)
    md <- paste(readLines(f, encoding = "UTF-8"), collapse = "\n")
    expect_true(grepl("(R-MI-1)", md, fixed = TRUE), info = pf)
    expect_true(grepl("valor test", md), info = pf)
    expect_true(grepl("Base de conocimiento: A10-1.5", md, fixed = TRUE), info = pf)
  }
  e <- aida_tabla(aida(ej("Area__Fuzzy_csv_DescGrp.txt"), perfil = "experto", redactar = FALSE))
  expect_true(all(c("valor_test", "regla", "p_valor", "class_cat", "razon") %in% names(e)))
  i <- aida_tabla(aida(ej("Area__Fuzzy_csv_DescGrp.txt"), perfil = "intermedio", redactar = FALSE))
  expect_true(all(c("valor_test", "regla") %in% names(i))); expect_false(any(c("p_valor", "class_cat", "razon") %in% names(i)))
})

test_that("RF-PU-2 y R-MS-10: las limitaciones del novato no nombran el valor test, pero cubren escalado y conjuntos", {
  for (esc in c(TRUE, FALSE)) {
    t4 <- aida(ej("entropy__Fuzzy_csv_DescGrp.txt"), perfil = "novato", escalado = esc, redactar = FALSE)$sintesis$secciones[[4]]$texto
    expect_false(grepl("valor test", t4)); expect_match(t4, "conjuntos difusos"); expect_match(t4, "reescalaron")
  }
  t4i <- aida(ej("entropy__Fuzzy_csv_DescGrp.txt"), perfil = "intermedio", redactar = FALSE)$sintesis$secciones[[4]]$texto
  expect_match(t4i, "valor test")
})

test_that("RF-PU-2: el novato recibe la transición en lenguaje llano y los pocos datos por su nombre", {
  x <- aida(ej("Area__Fuzzy_csv_DescGrp.txt"), perfil = "novato", redactar = FALSE)
  t <- x$interpretaciones$texto[x$interpretaciones$es_transicion]
  expect_true(all(grepl("al lado de", t))); expect_false(any(grepl("transición", t)))
  b <- aida(ej("HorasDocencia_csv_DescFil.txt"), perfil = "novato", redactar = FALSE)$sintesis$secciones[[3]]$texto
  expect_match(b, "pocos datos: "); expect_false(grepl("FIL-P", b))
})

test_that("descripción de columnas: la característica del par es la categoría, no la clase", {
  h <- aida_hallazgos(aida_interpretar(aida_leer(ej("HorasDocencia_csv_DescCol.txt"))))
  for (g in h$grupos) for (p in g$pares) {
    expect_equal(p$caracteristica, g$conjunto); expect_false(identical(p$clase, p$caracteristica))
  }
})

test_that("R-MS-9: la cantidad de no significativas se informa sin listarlas", {
  l <- c(titulo, tabla("A", "Are1_1_", "3"), tabla("B", "Are2_2_", "0.5"), tabla("C", "Are3_3_", "1"))
  t1 <- aida(l, redactar = FALSE)$sintesis$secciones[[1]]$texto
  expect_match(t1, "no significativas: 2")
  expect_false(grepl("no significativas", aida(c(titulo, tabla("A", "Are1_1_", "3")), redactar = FALSE)$sintesis$secciones[[1]]$texto))
})

test_that("nombres legibles: un intervalo con los dos límites iguales muestra un solo valor", {
  expect_equal(.aida_legible("Are5_53a53_"), "Are5 (53)")
  expect_equal(.aida_legible("Are4_31.4a43.4_"), "Are4 (31,4 a 43,4)")
})

test_that("RF-LE: una fila que empieza con $ no se pierde y falta de guiones entre bloques", {
  x <- aida_leer(c(titulo, "class: A", "Test.Value p.Value Class.Cat Cat.Class Global Weight", "$ret 2 0.1 1 2 3 4"))
  expect_equal(x$linea, "$ret")
  y <- aida_leer(c(titulo, "class: A", "Test.Value p.Value Class.Cat Cat.Class Global Weight", "X_1_ 2 0.1 1 2 3 4",
                   "class: B", "Test.Value p.Value Class.Cat Cat.Class Global Weight", "X_1_ 3 0.1 1 2 3 4"))
  expect_equal(y$clase, c("A", "B"))
})

test_that("RF-LE-3: NA se trata como NaN; Inf sólo vale en el valor test", {
  expect_warning(x <- aida_leer(c(titulo, tabla("K", "A_1_", "NA"))), "Se omiten")
  expect_equal(nrow(x), 0)
  expect_warning(y <- aida_leer(c(titulo, tabla("K", "A_1_", "3", g = "Inf"))), "Se omiten")
  expect_equal(nrow(y), 0)
  expect_warning(z <- aida_leer(c(titulo, tabla("K", "A_1_", "3", cc = "NaN"))), "Sin Class.Cat")
  expect_equal(nrow(z), 1)
  expect_equal(nrow(aida_leer(c(titulo, tabla("K", "A_1_", "Inf")))), 1)
})

test_that("mensajes en español: perfil no texto, ruta vacía y destino inválido", {
  l <- c(titulo, tabla("K", "A_1_", "3"))
  expect_error(aida(l, perfil = list("novato"), redactar = FALSE), "Perfil no válido")
  expect_error(aida(l, perfil = NA, redactar = FALSE), "Perfil no válido")
  expect_error(aida("no_existe.txt", perfil = "x"), "Perfil no válido")     # el perfil se valida antes de leer
  expect_error(aida(""), "ruta")
  r <- aida(l, redactar = FALSE)
  expect_error(aida_guardar(r, file.path(tempdir(), "no", "existe", "o.md")), "No existe la carpeta")
  expect_error(aida_guardar(r, tempdir()), "carpeta")
  expect_error(aida_guardar(r, NULL), "ruta")
})

test_that("RNF-3: las advertencias salen de la base de conocimiento y la base se valida", {
  kb <- aida_kb(); kb$advertencias$AD2$disparador <- "otro"
  x <- aida_interpretar(aida_leer(c(titulo, tabla("A", "Are1_1_", "3", g = 1)), kb), "intermedio", kb)
  expect_equal(x$advertencias, "AD1"); expect_false(grepl("pocos datos", x$texto))
  f <- tempfile(fileext = ".json"); jsonlite::write_json(list(metadatos = list()), f)
  expect_error(aida_kb(f), "incompleta")
  invisible(aida_kb(recargar = TRUE))
  sin <- aida_kb(); sin$parametros$umbral_p_exacto <- NULL
  expect_error(aida_interpretar(aida_leer(c(titulo, tabla("A", "Are1_1_", "3")), sin), "experto", sin), "umbral_p_exacto")
})

test_that("aida_guardar informa la versión de la base usada en el análisis", {
  kb <- aida_kb(); kb$metadatos$version <- "PRUEBA"
  r <- aida(c(titulo, tabla("A", "Are1_1_", "3")), redactar = FALSE, kb = kb)
  f <- tempfile(fileext = ".md"); aida_guardar(r, f)
  expect_true(any(grepl("Base de conocimiento: PRUEBA", readLines(f, encoding = "UTF-8"), fixed = TRUE)))
})

test_that("modo integrado: una tabla con nombres largos no depende del ancho de la consola", {
  d <- data.frame(Test.Value = 3.1, p.Value = 0.001, Class.Cat = 10, Cat.Class = 30, Global = 20, Weight = 99,
                  row.names = paste0(strrep("n", 90), "_1_"))
  ancho <- options(width = 40); on.exit(options(ancho))
  res <- suppressMessages(aida_desde_dafu("Descripción filas en función columnas", by(d, list(class = "A"), identity), redactar = FALSE))
  expect_equal(getOption("width"), 40)
  expect_equal(nrow(res$pares), 1)
})

test_that("redactar = TRUE sin proveedor disponible entrega el respaldo estructurado", {
  skip_if_not(requireNamespace("reticulate", quietly = TRUE) && reticulate::py_module_available("jinja2"))
  viejo <- Sys.getenv(c("AIDA_PROVEEDOR", "OLLAMA_HOST", "AIDA_ENV"))
  nuevo <- list(AIDA_PROVEEDOR = "ollama", OLLAMA_HOST = "http://127.0.0.1:9", AIDA_ENV = file.path(tempdir(), "no_existe.env"))
  do.call(Sys.setenv, nuevo)
  # Un Python ya iniciado no ve Sys.setenv: sin esto, la prueba usaría el .env real y llamaría al proveedor configurado.
  os <- reticulate::import("os")
  viejo_py <- lapply(nuevo, function(v) NULL)
  for (k in names(nuevo)) { viejo_py[k] <- list(os$environ$get(k)); reticulate::py_set_item(os$environ, k, nuevo[[k]]) }
  on.exit({
    do.call(Sys.setenv, as.list(viejo))
    for (k in names(nuevo)) if (is.null(viejo_py[[k]])) os$environ$pop(k, NULL) else reticulate::py_set_item(os$environ, k, viejo_py[[k]])
  })
  r <- suppressWarnings(aida(c(titulo, tabla("A", "Are1_1_", "3")), redactar = TRUE))
  expect_equal(r$sintesis$estado, "no redactada")
  expect_match(r$sintesis$aviso, "No se pudo redactar")
  expect_equal(length(r$sintesis$secciones), 4)
})

test_that("nombres legibles de categorías difusas", {
  expect_equal(.aida_legible(c("Are2_9.3a20.9_", "Are1_1_", "E47_F1_D", NA)), c("Are2 (9,3 a 20,9)", "Are1_1_", "E47_F1_D", NA))
  x <- aida(ej("Area__Fuzzy_csv_DescGrp.txt"), perfil = "novato", redactar = FALSE)
  expect_match(x$interpretaciones$texto[1], "Are1 \\(1,3 a 9,3\\)")
  expect_match(x$sintesis$hallazgos$texto_s2, "1\\. Are1 \\(1,3 a 9,3\\): 6 asociaciones")
})

# ─── Correcciones de la revisión del 06/11/2026 ──────────────────────────────

cabecera <- "Test.Value p.Value Class.Cat Cat.Class Global Weight"
col_num <- c("Descripción columnas en función filas ", "class: Are1_1.3a9.3_", cabecera,
             "76 14.213 0.000 94.3 1.5 0.5 106.09", "E47 3.100 0.002 40.0 30.0 20.0 99", strrep("-", 40),
             "class: Are2_9.3a20.9_", cabecera, "76 2.100 0.036 5.0 0.7 0.5 106.09")

test_that("una clase que es sólo un número se escribe «la clase N», en todos los perfiles", {
  expect_equal(.aida_clase_txt(c("76", "1.5", "E47", "76a", NA)), c("la clase 76", "la clase 1.5", "E47", "76a", NA))
  expect_equal(.aida_clase_txt("76", articulo = FALSE), "clase 76")
  n <- aida(col_num, perfil = "novato", redactar = FALSE)
  i <- aida(col_num, perfil = "intermedio", redactar = FALSE)
  e <- aida(col_num, perfil = "experto", redactar = FALSE)
  expect_match(n$interpretaciones$texto[1], "corresponde a la clase 76,", fixed = TRUE)
  expect_match(i$interpretaciones$texto[1], "^La clase 76 caracteriza a Are1")
  expect_match(e$interpretaciones$texto[1], "^La clase 76 en Are1")
  expect_match(i$interpretaciones$texto[2], "^E47 caracteriza a Are1")           # un nombre no numérico queda igual
  expect_match(i$interpretaciones$texto[1], "En la clase 76, Are1", fixed = TRUE) # la transición también
  expect_match(i$sintesis$hallazgos$texto_s2, "clase 76 (V = 14,213; peso bajo)", fixed = TRUE)
  expect_match(n$sintesis$secciones[[3]]$texto, "la clase 76 en Are1", fixed = TRUE)
  expect_equal(i$interpretaciones$clase[1], "76")                                # el dato sigue siendo el nombre original
})

test_that("en la descripción de filas, la clase numérica es el bloque y también se nombra", {
  x <- aida(c("Descripción filas en función columnas ", "class: 76", cabecera, "Are1_1.3a9.3_ 14.213 0.000 94.3 1.5 0.5 106.09"),
            perfil = "intermedio", redactar = FALSE)
  expect_match(x$interpretaciones$texto[1], "caracteriza a la clase 76: ", fixed = TRUE)
})

simular_redaccion <- function(estado) {
  original <- get(".aida_redactar_python", envir = globalenv())
  assign(".aida_redactar_python", function(ruta_h, ruta_kb, modelo) list(
    estado = estado, aviso = "aviso de prueba", modelo = "m", proveedor = "simulado", fecha = "2026-11-06 10:00",
    secciones = list(list(id = "S1", nombre = "Descripción general", texto = "Redactado.", interpretaciones = list())),
    rechazados = list(list(seccion = "S2", conjunto = "Are1", texto = "Texto rechazado.", motivos = list("motivo de prueba")))), envir = globalenv())
  function() assign(".aida_redactar_python", original, envir = globalenv())
}

test_that("el estado parcial conserva lo redactado y lo que no verifica pasa al respaldo sin perder los rechazos", {
  restaurar <- simular_redaccion("parcialmente redactada"); on.exit(restaurar())
  r <- aida(col_num, redactar = TRUE)
  expect_equal(r$sintesis$estado, "parcialmente redactada")
  expect_equal(r$sintesis$secciones[[1]]$texto, "Redactado.")
  restaurar()
  restaurar <- simular_redaccion("no verificada")
  r <- aida(col_num, redactar = TRUE)
  expect_equal(r$sintesis$estado, "no redactada")
  expect_match(r$sintesis$aviso, "aviso de prueba")
  expect_equal(r$sintesis$rechazados[[1]]$texto, "Texto rechazado.")
})

test_that("aida_guardar deja los textos rechazados aparte y no conserva los de una corrida anterior", {
  restaurar <- simular_redaccion("parcialmente redactada"); on.exit(restaurar())
  r <- aida(col_num, redactar = TRUE)
  md <- tempfile(fileext = ".md"); aparte <- paste0(tools::file_path_sans_ext(md), "_rechazos.json")
  aida_guardar(r, md)
  expect_true(file.exists(aparte))
  expect_equal(jsonlite::fromJSON(aparte, simplifyVector = FALSE)[[1]]$motivos[[1]], "motivo de prueba")
  expect_false(any(grepl("Texto rechazado", readLines(md, encoding = "UTF-8"))))
  aida_guardar(aida(col_num, redactar = FALSE), md)
  expect_false(file.exists(aparte))
})

test_that("aida_guardar no lista decenas de miles de interpretaciones y lo aclara", {
  r <- aida(col_num, redactar = FALSE)
  md <- tempfile(fileext = ".md")
  aida_guardar(r, md, max_interpretaciones = 1)
  l <- readLines(md, encoding = "UTF-8")
  expect_equal(sum(grepl("^- \\*\\*COL-P", l)), 1)
  expect_true(any(grepl("Se muestran las primeras 1 de 3 interpretaciones", l, fixed = TRUE)))
  aida_guardar(r, md)
  expect_false(any(grepl("Se muestran las primeras", readLines(md, encoding = "UTF-8"), fixed = TRUE)))
})

test_that("los listados del texto estructurado tienen tope y cuentan el resto", {
  expect_equal(.aida_y_mas(c("a", "b")), "a, b")
  expect_equal(.aida_y_mas(as.character(1:12)), "1, 2, 3, 4, 5, 6, 7, 8, 9, 10 y 2 más")
  # un conjunto (Are1_1a2_) asociado con 15 clases, cada una en su bloque
  tab <- c(titulo, unlist(lapply(1:15, function(i) c(paste0("class: G", i), "Test.Value p.Value Class.Cat Cat.Class Global Weight",
           sprintf("Are1_1a2_ %.1f 0.001 10 30 20 99", 20 - i / 10), strrep("-", 40)))))
  x <- aida(tab, redactar = FALSE)
  s2 <- x$sintesis$hallazgos$texto_s2
  expect_match(s2, "15 asociaciones")
  expect_match(s2, " y 5 más\\.$")
  expect_equal(length(strsplit(s2, ", ")[[1]]), 10)
})

test_that("la clase compuesta se desglosa en las variables de agrupación, en MI y en los hallazgos", {
  expect_equal(.aida_desglose(c("E47_F3", "76", "ECO", "A_B_C", NA), c("Cepa", "Fecha")),
               c("E47_F3 (cepa E47, fecha F3)", "76", "ECO", "A_B_C", NA))
  expect_equal(.aida_desglose("E47_F3", NULL), "E47_F3")
  tab <- c("Descripción grupos filas en función columnas ", "class: E47_F3", "Test.Value p.Value Class.Cat Cat.Class Global Weight",
           "Are5_53a53_ 20.2 0 69 88.4 13.1 144.9", strrep("-", 40))
  con <- aida(tab, perfil = "novato", redactar = FALSE, variables = c("Cepa", "Fecha"))
  sin <- aida(tab, perfil = "novato", redactar = FALSE)
  expect_match(con$interpretaciones$texto[1], "En E47_F3 (cepa E47, fecha F3), el 88,4 %", fixed = TRUE)
  expect_match(sin$interpretaciones$texto[1], "En E47_F3, el 88,4 %", fixed = TRUE)
  expect_equal(con$sintesis$hallazgos$variables, c("Cepa", "Fecha"))
  expect_null(sin$sintesis$hallazgos$variables)
  ig <- aida(tab, redactar = FALSE, variables = c("Cepa"))                      # cantidad que no coincide: se ignora
  expect_match(ig$interpretaciones$texto[1], "E47_F3 caracteriza|caracteriza a E47_F3")
  expect_false(grepl("(cepa", ig$interpretaciones$texto[1], fixed = TRUE))
})


test_that("aida_inferir_variables deduce los nombres de las variables desde la tabla original y no adivina", {
  d <- data.frame(Cepa = factor(rep(c("E47", "ECO", "FLO"), each = 3)), Fecha = factor(rep(c("F1", "F2", "F3"), 3)),
                  Lado = factor(rep(c("L", "R", "L"), 3)), Area = 1:9)
  expect_equal(aida_inferir_variables(c("E47_F1", "ECO_F2", "FLO_F3"), d), c("Cepa", "Fecha"))
  expect_equal(aida_inferir_variables(c("L_F1", "R_F2"), d), c("Lado", "Fecha"))
  expect_equal(aida_inferir_variables("E47_F1_L", d), c("Cepa", "Fecha", "Lado"))
  expect_null(aida_inferir_variables("E47_X9", d))                       # un valor que no está en ninguna columna
  expect_null(aida_inferir_variables(c("1", "2"), d))                    # clases sin trozos
  dup <- cbind(d, Otra = d$Fecha)                                       # dos columnas con los mismos valores: ambiguo
  expect_null(aida_inferir_variables(c("E47_F1", "ECO_F2"), dup))
})


# ─── Auditoría del 09/11/2026 ────────────────────────────────────────────────

test_that("completar una plantilla para muchas asociaciones da lo mismo que de a una", {
  pl <- "[línea] en [bloque]: V = [V]; p = [p] ([regla]). [desconocido] queda igual."
  val <- list("línea" = c("Are1", "[V]"), "bloque" = c("A", "B"), "V" = c("1,000", "2,000"), "p" = c("p < 0,01", "p = 0,020"), "regla" = "R-MI-1")
  vec <- .aida_completar_vec(pl, val, 2L)
  uno <- vapply(1:2, function(i) .aida_completar(pl, lapply(val, function(x) x[min(i, length(x))])), "")
  expect_equal(vec, uno)
  expect_equal(vec[2], "[V] en B: V = 2,000; p = 0,020 (R-MI-1). [desconocido] queda igual.")   # lo insertado no se vuelve a completar
  expect_equal(.aida_completar_vec("Sin campos.", list(), 3L), rep("Sin campos.", 3))
})

test_that("R-MI-13: cada p-valor de una asociación extrema conserva su propio formato", {
  l <- c("Descripción filas en función columnas ",
         "class: A", "        Test.Value p.Value Class.Cat Cat.Class Global Weight", "Are1_1_        Inf   0.000      50.0      60.0   20.0  100",
         "------", "class: B", "        Test.Value p.Value Class.Cat Cat.Class Global Weight", "Are1_1_        Inf   0.00012      50.0      60.0   20.0  100")
  it <- aida_interpretar(aida_leer(l))
  expect_equal(it$p_texto, c("p = 0", "p = 0,00012"))
})

test_that("la síntesis estructurada no dice «N de N» cuando el archivo sólo trae lo que supera el umbral", {
  s <- aida(ej("Area__Fuzzy_csv_DescGrp.txt"), redactar = FALSE)$sintesis
  expect_match(s$secciones[[1]]$texto, "Asociaciones significativas: 22.", fixed = TRUE)
  expect_false(grepl("22 de 22", s$secciones[[1]]$texto, fixed = TRUE))
})

test_that("modo integrado: el nombre del archivo, los conjuntos de la tabla y la guía del perfil llegan a los hallazgos", {
  lineas <- readLines(ej("Area__Fuzzy_csv_DescGrp.txt"), warn = FALSE, encoding = "UTF-8")
  conj <- c("Are1_1.3a9.3_", "Are2_9.3a20.9_", "Are3_20.9a31.4_", "Are4_31.4a43.4_", "Are5_53a53_")
  r <- aida(lineas, perfil = "novato", redactar = FALSE, nombre = "Area _Fuzzy.csv", conjuntos = conj)
  expect_equal(r$archivo, "Area _Fuzzy.csv")
  expect_match(r$sintesis$secciones[[1]]$texto, "Archivo: Area _Fuzzy.csv", fixed = TRUE)
  h <- r$sintesis$hallazgos
  expect_equal(h$conjuntos_tabla, conj)
  expect_equal(h$guia_redaccion, aida_kb()$perfiles$novato$guia_redaccion)
  expect_equal(h$ejemplo_estilo, aida_kb()$perfiles$novato$ejemplo_estilo)
  # Leyendo un archivo, el nombre es el del archivo aunque se pase otro.
  expect_equal(aida(ej("Area__Fuzzy_csv_DescGrp.txt"), redactar = FALSE, nombre = "otro.csv")$archivo, "Area__Fuzzy_csv_DescGrp.txt")
})

test_that("aida_inferir_variables usa los niveles presentes y funciona con columnas de texto", {
  d <- data.frame(Cepa = c("E47", "ECO"), Fecha = factor(c("F1", "F2"), levels = c("F1", "F2", "F9")), stringsAsFactors = FALSE)
  expect_equal(aida_inferir_variables(c("E47_F1", "ECO_F2"), d), c("Cepa", "Fecha"))
  expect_null(aida_inferir_variables("E47_F9", d))            # F9 es un nivel declarado pero sin filas
})

test_that("A10-1.5: el desglose se da una sola vez por interpretación y no se usa con una sola variable", {
  tab <- c("Descripción grupos filas en función columnas ", "class: E47_F1", "Test.Value p.Value Class.Cat Cat.Class Global Weight",
           "Are1_1.3a9.3_ 10.9 0 30 50.9 28.8 144.9", "Are2_9.3a20.9_ 5.2 0 20 33.7 25.9 120", strrep("-", 40))
  x <- aida(tab, perfil = "novato", redactar = FALSE, variables = c("Cepa", "Fecha"))
  t <- x$interpretaciones$texto[1]
  expect_equal(lengths(regmatches(t, gregexpr("(cepa E47, fecha F1)", t, fixed = TRUE))), 1)     # antes: tres veces por oración
  expect_match(t, "distingue a E47_F1 de los demás", fixed = TRUE)
  expect_match(t, "E47_F1 se asocia además con Are2 (9,3 a 20,9), al lado de Are1 (1,3 a 9,3) en la escala de valores.", fixed = TRUE)
  una <- c("Descripción grupos filas en función columnas ", "class: E47BIS", "Test.Value p.Value Class.Cat Cat.Class Global Weight",
           "ent1_0a1_ 10.9 0 30 50.9 28.8 144.9", strrep("-", 40))
  y <- aida(una, perfil = "novato", redactar = FALSE, variables = "Tratamiento")
  expect_false(grepl("(tratamiento", y$interpretaciones$texto[1], fixed = TRUE))                # antes: «E47BIS (tratamiento E47BIS)»
  expect_equal(.aida_desglose("E47BIS", "Tratamiento"), "E47BIS")
})

test_that("A10-1.5: los conjuntos con puntos se leen como rangos y los nombres de variable basura no se usan", {
  expect_equal(.aida_legible(c("CO1.4.2a6.5.", "tem5.40a40.", "Are3_20.9a31.4_", "Hpre", "C5")),
               c("CO1 (4,2 a 6,5)", "tem5 (40)", "Are3 (20,9 a 31,4)", "Hpre", "C5"))
  expect_equal(.aida_categoria("CO4.9.5a10.5."), list(variable = "CO", indice = 4L))
  expect_true(is.na(.aida_categoria("V1.5")$indice))
  tab <- c("Descripción grupos filas en función columnas ", "class: ALTA", "Test.Value p.Value Class.Cat Cat.Class Global Weight",
           "CO4.9.5a10.5. 9.99 0 40 65.6 32.8 20", "CO5.11.8a11.8. 6.5 0 30 40 25 15", strrep("-", 40))
  x <- aida(tab, perfil = "intermedio", redactar = FALSE)
  expect_match(x$interpretaciones$texto[1], "CO4 (9,5 a 10,5)", fixed = TRUE)
  expect_true(x$interpretaciones$es_transicion[1] && x$interpretaciones$es_transicion[2])     # CO4 y CO5 son contiguos
  expect_equal(.aida_variables_utiles(c("Cepa", "Fecha")), c("Cepa", "Fecha"))
  expect_null(.aida_variables_utiles("df...sapply.df..is.factor.."))
  expect_null(.aida_variables_utiles(c("Cepa", "X.1")))
  expect_null(.aida_variables_utiles(NULL))
})
