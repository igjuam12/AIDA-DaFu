// ============================================================
// AIDA - Modelo lógico (A8) con las plantillas y advertencias de A10
// Red de frames con el metamodelo de la guía de la cátedra:
// FrameClass, FrameInst, Slot, HAS_VALUE, INSTANCE_OF
// Ambrogetti, Ignacio Julián - Legajo 48907 - PPS 2026
// ============================================================
// Cómo cargarlo: ejecutar primero el script del modelo conceptual (A7)
// y luego pegar este archivo completo en el editor de consultas.
// El script usa MERGE y restricciones de unicidad: puede ejecutarse
// más de una vez sin duplicar nodos ni relaciones. Los enlaces con
// los conceptos y las reglas de A7 (FORMALIZA) se crean sólo si esos
// nodos existen en la base.
// Convenciones: los slots que referencian a otro frame se guardan como
// relaciones con el nombre del slot en mayúsculas (ESTADO_ASOCIADO);
// los demás valores se guardan en la propiedad value de HAS_VALUE.

// ---------- 0. Restricciones de unicidad
CREATE CONSTRAINT IF NOT EXISTS FOR (c:FrameClass) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (i:FrameInst) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (s:Slot) REQUIRE s.name IS UNIQUE;

// ---------- 1. Frames (FrameClass) y herencia (IS_A)
UNWIND [
    {name: 'Exportacion', descripcion: 'Archivo de texto que DaFu genera con la descripción de un análisis.', grupo: 'Fuente de datos'},
    {name: 'DescripcionDeFilas', descripcion: 'Describe cada fila (clase) en función de las columnas.', grupo: 'Fuente de datos'},
    {name: 'DescripcionDeColumnas', descripcion: 'Describe cada columna (categoría) en función de las filas.', grupo: 'Fuente de datos'},
    {name: 'DescripcionDeGrupos', descripcion: 'Describe cada grupo de filas en función de las columnas.', grupo: 'Fuente de datos'},
    {name: 'Clase', descripcion: 'Fila de la tabla de contingencia, o grupo de filas, que se describe.', grupo: 'Datos'},
    {name: 'ConjuntoDifuso', descripcion: 'Conjunto en el que la pertenencia es un grado entre 0 y 1. Lo son las categorías de la tabla y las etiquetas que AIDA define sobre la proporción de clases.', grupo: 'Datos'},
    {name: 'Categoria', descripcion: 'Columna de la tabla. Su nombre codifica variable, número y rango, o una etiqueta lingüística.', grupo: 'Datos'},
    {name: 'ParDeAsociacion', descripcion: 'Combinación de una clase y una categoría evaluada con un valor test. Es el contexto que describe el estado interpretado.', grupo: 'Datos'},
    {name: 'Magnitud', descripcion: 'Campo numérico que la exportación informa para cada par de asociación.', grupo: 'Interpretación'},
    {name: 'ValorObservado', descripcion: 'Valor concreto de una magnitud en un par de asociación.', grupo: 'Interpretación'},
    {name: 'Rango', descripcion: 'Intervalo del valor test que determina un estado interpretado.', grupo: 'Interpretación'},
    {name: 'EstadoInterpretado', descripcion: 'Significado que se asigna al valor test de un par: significación, dirección e intensidad relativa.', grupo: 'Interpretación'},
    {name: 'Regla', descripcion: 'Enunciado del catálogo formalizado como regla de inferencia.', grupo: 'Explicación'},
    {name: 'Parametro', descripcion: 'Valor numérico que una regla consulta y que puede ajustarse sin modificar el código.', grupo: 'Explicación'},
    {name: 'AdvertenciaMetodologica', descripcion: 'Aclaración que acompaña a la interpretación para evitar una lectura errónea.', grupo: 'Explicación'},
    {name: 'Plantilla', descripcion: 'Texto con campos variables que se completa con los datos de un par para redactar la interpretación.', grupo: 'Explicación'},
    {name: 'InterpretacionAtomica', descripcion: 'Enunciado en lenguaje natural sobre un par de asociación, con su estado interpretado y su justificación estadística.', grupo: 'Explicación'},
    {name: 'PatronEmergente', descripcion: 'Conjunto de interpretaciones significativas que, agrupadas, caracterizan un conjunto difuso.', grupo: 'Síntesis'},
    {name: 'PatronConstante', descripcion: 'Categoría significativa en muchas clases.', grupo: 'Síntesis'},
    {name: 'Singularidad', descripcion: 'Categoría significativa sólo en algunas clases.', grupo: 'Síntesis'},
    {name: 'Sintesis', descripcion: 'Documento narrativo que reúne y jerarquiza las interpretaciones significativas de una descripción.', grupo: 'Síntesis'},
    {name: 'SeccionDeLaSintesis', descripcion: 'Parte fija del documento de síntesis.', grupo: 'Síntesis'},
    {name: 'Usuario', descripcion: 'Persona que ejecuta el análisis en DaFu y solicita la interpretación.', grupo: 'Perfil'},
    {name: 'PerfilDeUsuario', descripcion: 'Nivel de formación estadística del lector y forma en que se le presentan los resultados.', grupo: 'Perfil'},
    {name: 'PerfilNovato', descripcion: 'Lector sin formación estadística.', grupo: 'Perfil'},
    {name: 'PerfilIntermedio', descripcion: 'Lector con formación estadística básica.', grupo: 'Perfil'},
    {name: 'PerfilExperto', descripcion: 'Lector con formación estadística avanzada.', grupo: 'Perfil'}
  ]
AS f
MERGE (c:FrameClass {name: f.name})
SET c.descripcion = f.descripcion, c.grupo = f.grupo;

UNWIND [
    {hijo: 'DescripcionDeFilas', padre: 'Exportacion'},
    {hijo: 'DescripcionDeColumnas', padre: 'Exportacion'},
    {hijo: 'DescripcionDeGrupos', padre: 'Exportacion'},
    {hijo: 'Categoria', padre: 'ConjuntoDifuso'},
    {hijo: 'PatronConstante', padre: 'PatronEmergente'},
    {hijo: 'Singularidad', padre: 'PatronEmergente'},
    {hijo: 'PerfilNovato', padre: 'PerfilDeUsuario'},
    {hijo: 'PerfilIntermedio', padre: 'PerfilDeUsuario'},
    {hijo: 'PerfilExperto', padre: 'PerfilDeUsuario'}
  ]
AS h
MATCH (a:FrameClass {name: h.hijo}), (b:FrameClass {name: h.padre})
MERGE (a)-[:IS_A]->(b);

// ---------- 2. Slots (Slot) y facetas (HAS_SLOT)
// Las facetas son: tipo, requerido, valor_defecto, valores, minimo y maximo.
// El demonio se describe con demonio_tipo, demonio_accion y demonio_regla.
UNWIND ['advertencias', 'aplicabilidad', 'bloque', 'bloque_es', 'campos', 'categoria', 'cierre_inferior', 'cierre_superior', 'clase', 'class_cat_visible', 'columna', 'conclusion', 'condicion', 'conjunto_difuso', 'contenido', 'contribuciones_dimensiones', 'debe_incluir', 'decision', 'definicion', 'direccion', 'disparador', 'enunciado', 'es_significativa', 'es_transicion', 'escalado_lineal', 'estado', 'estado_asociado', 'estado_redaccion', 'excepcion', 'explicacion', 'explicacion_corta', 'exportacion', 'formalizacion', 'frecuencias', 'fuente', 'fuerza', 'funcion_pertenencia', 'fundamento', 'id', 'indice', 'instruccion_registro', 'guia_redaccion', 'ejemplo_estilo', 'intensidad_llana', 'intensidad', 'interpretaciones', 'limite_inferior', 'limite_superior', 'linea', 'magnitud', 'maximo_valido', 'minimo_valido', 'modulo', 'n_clases', 'n_no_significativas', 'n_pares', 'no_finito', 'nombre', 'orden', 'origen', 'p_texto', 'p_valor_visible', 'par', 'parametros', 'pares', 'patrones', 'perfil', 'pertenencia_algunas', 'pertenencia_muchas', 'peso_bajo', 'plantilla', 'posicion', 'primera_linea', 'proporcion_clases', 'rango_resultante', 'razon_proporciones', 'razon_proporciones_visible', 'regla', 'reglas', 'secciones', 'significacion', 'subprocesos', 'terminologia', 'texto', 'texto_novato', 'contenido_novato', 'tipo_conocimiento', 'unidad', 'valor', 'valor_crisp', 'valor_test', 'valores', 'variable', 'verificada'] AS n
MERGE (:Slot {name: n});

// Exportacion
UNWIND [
    {slot: 'primera_linea', tipo: 'string', requerido: true, nota: 'Primera línea del archivo; identifica el tipo de descripción.'},
    {slot: 'bloque_es', tipo: 'enum', requerido: true, valores: ['clase', 'categoria'], nota: 'Qué representa el nombre de cada bloque.'},
    {slot: 'escalado_lineal', tipo: 'boolean', requerido: true, valor_defecto: true, nota: 'Parámetro de invocación; la tabla se escala por defecto.'},
    {slot: 'pares', tipo: 'ref[]', requerido: true, valores: ['ParDeAsociacion'], nota: 'Pares de asociación que contiene el archivo.'},
    {slot: 'n_pares', tipo: 'integer', requerido: false, minimo: 0, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Cuenta los pares del archivo. Si es cero, el asistente informa que no hay asociaciones para interpretar y finaliza sin error.', demonio_regla: 'RF-LE-5'},
    {slot: 'n_clases', tipo: 'integer', requerido: false, minimo: 1, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Cuenta las clases distintas de los pares. Es el denominador de la proporción de clases de un patrón.', demonio_regla: 'R-MS-5, R-MS-6'}
  ]
AS s
MATCH (c:FrameClass {name: 'Exportacion'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// DescripcionDeFilas
UNWIND [
    {slot: 'primera_linea', tipo: 'string', requerido: true, valor_defecto: 'Descripción filas en función columnas'},
    {slot: 'bloque_es', tipo: 'enum', requerido: true, valor_defecto: 'clase', valores: ['clase', 'categoria']}
  ]
AS s
MATCH (c:FrameClass {name: 'DescripcionDeFilas'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// DescripcionDeColumnas
UNWIND [
    {slot: 'primera_linea', tipo: 'string', requerido: true, valor_defecto: 'Descripción columnas en función filas'},
    {slot: 'bloque_es', tipo: 'enum', requerido: true, valor_defecto: 'categoria', valores: ['clase', 'categoria'], nota: 'El bloque es la categoría y cada línea es una clase.'}
  ]
AS s
MATCH (c:FrameClass {name: 'DescripcionDeColumnas'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// DescripcionDeGrupos
UNWIND [
    {slot: 'primera_linea', tipo: 'string', requerido: true, valor_defecto: 'Descripción grupos filas en función columnas'},
    {slot: 'bloque_es', tipo: 'enum', requerido: true, valor_defecto: 'clase', valores: ['clase', 'categoria']}
  ]
AS s
MATCH (c:FrameClass {name: 'DescripcionDeGrupos'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// Clase
UNWIND [
    {slot: 'nombre', tipo: 'string', requerido: true},
    {slot: 'origen', tipo: 'enum', requerido: true, valor_defecto: 'fila', valores: ['fila', 'grupo'], nota: 'Es grupo cuando la descripción es de grupos.'}
  ]
AS s
MATCH (c:FrameClass {name: 'Clase'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// ConjuntoDifuso
UNWIND [
    {slot: 'nombre', tipo: 'string', requerido: true},
    {slot: 'variable', tipo: 'string', requerido: true},
    {slot: 'funcion_pertenencia', tipo: 'enum', requerido: true, valor_defecto: 'desconocida', valores: ['gaussiana', 'triangular', 'trapezoidal', 'desconocida'], nota: 'La exportación no informa la función de las categorías.'},
    {slot: 'parametros', tipo: 'number[]', requerido: false, nota: 'Cuatro valores a, b, c, d cuando la función es trapezoidal.'}
  ]
AS s
MATCH (c:FrameClass {name: 'ConjuntoDifuso'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// Categoria
UNWIND [
    {slot: 'variable', tipo: 'string', requerido: true, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Toma el prefijo alfabético del nombre previo al número (Are1_… → Are). Si el nombre no tiene número, la variable es el nombre completo.', demonio_regla: 'R-MI-12'},
    {slot: 'indice', tipo: 'integer', requerido: false, minimo: 1, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Extrae el número que sigue al prefijo (Are2_… → 2). Queda vacío en las categorías sin número.', demonio_regla: 'R-MI-12'},
    {slot: 'limite_inferior', tipo: 'number', requerido: false, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Extrae el primer límite del rango codificado en el nombre (Are2_9.3a20.9_ → 9,3).'},
    {slot: 'limite_superior', tipo: 'number', requerido: false, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Extrae el segundo límite del rango codificado en el nombre (Are2_9.3a20.9_ → 20,9).'}
  ]
AS s
MATCH (c:FrameClass {name: 'Categoria'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// ParDeAsociacion
UNWIND [
    {slot: 'exportacion', tipo: 'ref', requerido: true, valores: ['Exportacion']},
    {slot: 'bloque', tipo: 'string', requerido: true, nota: 'Nombre del bloque del archivo (RF-LE-2).'},
    {slot: 'linea', tipo: 'string', requerido: true, nota: 'Nombre de la línea del archivo, es decir, de la característica del par.'},
    {slot: 'clase', tipo: 'ref', requerido: false, valores: ['Clase'], demonio_tipo: 'IF-NEEDED', demonio_accion: 'En la descripción de filas y de grupos la clase es el bloque; en la de columnas es la línea.', demonio_regla: 'RF-LE-2'},
    {slot: 'categoria', tipo: 'ref', requerido: false, valores: ['Categoria'], demonio_tipo: 'IF-NEEDED', demonio_accion: 'En la descripción de filas y de grupos la categoría es la línea; en la de columnas es el bloque.', demonio_regla: 'RF-LE-2'},
    {slot: 'valores', tipo: 'ref[]', requerido: true, valores: ['ValorObservado'], nota: 'Los seis valores observados del par.'},
    {slot: 'estado', tipo: 'ref', requerido: false, valores: ['EstadoInterpretado'], demonio_tipo: 'IF-NEEDED', demonio_accion: 'Toma el estado asociado al rango en que cae su valor test.', demonio_regla: 'R-MI-1 a R-MI-7'},
    {slot: 'no_finito', tipo: 'boolean', requerido: false, valor_defecto: false, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Es verdadero si el valor test no es finito.', demonio_regla: 'R-MI-13'},
    {slot: 'peso_bajo', tipo: 'boolean', requerido: false, valor_defecto: false, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Es verdadero si el valor Global del par, que mide el peso de la línea, es menor que el umbral de peso bajo.', demonio_regla: 'R-MI-11'},
    {slot: 'razon_proporciones', tipo: 'number', requerido: false, minimo: 0, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Calcula Cat.Class dividido por Global. Queda vacío si Global es cero.', demonio_regla: 'R-PU-3'}
  ]
AS s
MATCH (c:FrameClass {name: 'ParDeAsociacion'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// Magnitud
UNWIND [
    {slot: 'nombre', tipo: 'string', requerido: true},
    {slot: 'columna', tipo: 'string', requerido: true, nota: 'Nombre de la columna en la exportación.'},
    {slot: 'unidad', tipo: 'enum', requerido: true, valores: ['desviaciones típicas', 'probabilidad', 'porcentaje', 'peso']},
    {slot: 'minimo_valido', tipo: 'number', requerido: true},
    {slot: 'maximo_valido', tipo: 'number', requerido: true},
    {slot: 'definicion', tipo: 'string', requerido: true}
  ]
AS s
MATCH (c:FrameClass {name: 'Magnitud'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// ValorObservado
UNWIND [
    {slot: 'par', tipo: 'ref', requerido: true, valores: ['ParDeAsociacion']},
    {slot: 'magnitud', tipo: 'ref', requerido: true, valores: ['Magnitud']},
    {slot: 'valor_crisp', tipo: 'number', requerido: true, demonio_tipo: 'IF-ADDED', demonio_accion: 'Controla que el valor esté dentro del intervalo válido de la magnitud. El valor test puede ser infinito: en ese caso marca el par como no finito.', demonio_regla: 'R-MI-13'},
    {slot: 'rango_resultante', tipo: 'ref', requerido: false, valores: ['Rango'], demonio_tipo: 'IF-NEEDED', demonio_accion: 'Para el valor test, busca el rango que contiene el valor. Para las demás magnitudes queda vacío.', demonio_regla: 'R-MI-1 a R-MI-7'}
  ]
AS s
MATCH (c:FrameClass {name: 'ValorObservado'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// Rango
UNWIND [
    {slot: 'nombre', tipo: 'string', requerido: true},
    {slot: 'magnitud', tipo: 'ref', requerido: true, valor_defecto: 'ValorTest', valores: ['Magnitud']},
    {slot: 'limite_inferior', tipo: 'number', requerido: true, nota: 'Sin límite se representa con −1,0E9.'},
    {slot: 'limite_superior', tipo: 'number', requerido: true, nota: 'Sin límite se representa con 1,0E9.'},
    {slot: 'cierre_inferior', tipo: 'boolean', requerido: true, nota: 'Verdadero si el límite inferior pertenece al rango.'},
    {slot: 'cierre_superior', tipo: 'boolean', requerido: true, nota: 'Verdadero si el límite superior pertenece al rango.'},
    {slot: 'estado_asociado', tipo: 'ref', requerido: true, valores: ['EstadoInterpretado']},
    {slot: 'regla', tipo: 'ref', requerido: true, valores: ['Regla']}
  ]
AS s
MATCH (c:FrameClass {name: 'Rango'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// EstadoInterpretado
UNWIND [
    {slot: 'significacion', tipo: 'enum', requerido: true, valores: ['altamente significativo', 'significativamente probable', 'sugerente', 'no significativo']},
    {slot: 'direccion', tipo: 'enum', requerido: true, valores: ['sobre-representación', 'sub-representación', 'neutra']},
    {slot: 'intensidad', tipo: 'enum', requerido: true, valores: ['fuerte', 'moderada', 'débil', 'nula']},
    {slot: 'explicacion_corta', tipo: 'string', requerido: true}
  ]
AS s
MATCH (c:FrameClass {name: 'EstadoInterpretado'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// Regla
UNWIND [
    {slot: 'enunciado', tipo: 'string', requerido: true},
    {slot: 'modulo', tipo: 'enum', requerido: true, valores: ['MI', 'MS', 'Perfil']},
    {slot: 'tipo_conocimiento', tipo: 'enum', requerido: true, valores: ['Determinística', 'Heurística', 'Contextual']},
    {slot: 'aplicabilidad', tipo: 'enum', requerido: true, valor_defecto: 'Activa', valores: ['Activa', 'Latente']},
    {slot: 'estado', tipo: 'enum', requerido: true, valor_defecto: 'Confirmada', valores: ['Confirmada']},
    {slot: 'fuente', tipo: 'string', requerido: true},
    {slot: 'subprocesos', tipo: 'string[]', requerido: true},
    {slot: 'condicion', tipo: 'json', requerido: true},
    {slot: 'conclusion', tipo: 'json', requerido: true},
    {slot: 'excepcion', tipo: 'string', requerido: false},
    {slot: 'explicacion', tipo: 'string', requerido: true},
    {slot: 'formalizacion', tipo: 'enum', requerido: true, valor_defecto: 'Directa', valores: ['Directa', 'Con decisión propuesta']},
    {slot: 'decision', tipo: 'string', requerido: false}
  ]
AS s
MATCH (c:FrameClass {name: 'Regla'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// Parametro
UNWIND [
    {slot: 'nombre', tipo: 'string', requerido: true},
    {slot: 'valor', tipo: 'number', requerido: true},
    {slot: 'unidad', tipo: 'string', requerido: true},
    {slot: 'regla', tipo: 'string', requerido: true},
    {slot: 'estado', tipo: 'enum', requerido: true, valores: ['Confirmado', 'Propuesto']},
    {slot: 'fundamento', tipo: 'string', requerido: true}
  ]
AS s
MATCH (c:FrameClass {name: 'Parametro'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// AdvertenciaMetodologica
UNWIND [
    {slot: 'texto', tipo: 'string', requerido: true},
    {slot: 'texto_novato', tipo: 'string', requerido: false},
    {slot: 'disparador', tipo: 'enum', requerido: true, valores: ['siempre', 'peso_bajo', 'sintesis', 'escalado', 'no_escalado']},
    {slot: 'regla', tipo: 'ref', requerido: true, valores: ['Regla']}
  ]
AS s
MATCH (c:FrameClass {name: 'AdvertenciaMetodologica'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// Plantilla
UNWIND [
    {slot: 'reglas', tipo: 'ref[]', requerido: true, valores: ['Regla']},
    {slot: 'perfil', tipo: 'enum', requerido: true, valor_defecto: 'todos', valores: ['todos', 'novato', 'intermedio', 'experto']},
    {slot: 'texto', tipo: 'string', requerido: true},
    {slot: 'campos', tipo: 'string[]', requerido: true}
  ]
AS s
MATCH (c:FrameClass {name: 'Plantilla'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// InterpretacionAtomica
UNWIND [
    {slot: 'id', tipo: 'string', requerido: true},
    {slot: 'par', tipo: 'ref', requerido: true, valores: ['ParDeAsociacion']},
    {slot: 'perfil', tipo: 'enum', requerido: true, valores: ['novato', 'intermedio', 'experto']},
    {slot: 'regla', tipo: 'ref', requerido: false, valores: ['Regla'], demonio_tipo: 'IF-NEEDED', demonio_accion: 'Toma la regla del rango en que cae el valor test del par.', demonio_regla: 'R-MI-1 a R-MI-7'},
    {slot: 'es_significativa', tipo: 'boolean', requerido: false, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Es verdadera si la significación del estado del par no es «no significativo».', demonio_regla: 'R-MS-1'},
    {slot: 'advertencias', tipo: 'ref[]', requerido: false, valores: ['AdvertenciaMetodologica'], demonio_tipo: 'IF-NEEDED', demonio_accion: 'Reúne la advertencia de toda interpretación y, si el par tiene peso bajo, la de peso bajo.', demonio_regla: 'R-MI-8, R-MI-11'},
    {slot: 'es_transicion', tipo: 'boolean', requerido: false, valor_defecto: false, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Es verdadera si la misma clase tiene otro par significativo con una categoría contigua de la misma variable.', demonio_regla: 'R-MI-12'},
    {slot: 'p_texto', tipo: 'string', requerido: false, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Da el formato al p-valor: exacto si es mayor o igual que el umbral, «p < 0,01» en caso contrario. Si el valor test no es finito, deja el p-valor sin transformar.', demonio_regla: 'R-MI-9, R-MI-13'},
    {slot: 'plantilla', tipo: 'ref', requerido: false, valores: ['Plantilla'], demonio_tipo: 'IF-NEEDED', demonio_accion: 'Elige la plantilla que corresponde a la regla y al perfil.', demonio_regla: 'R-PU-1 a R-PU-3'}
  ]
AS s
MATCH (c:FrameClass {name: 'InterpretacionAtomica'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// PatronEmergente
UNWIND [
    {slot: 'conjunto_difuso', tipo: 'ref', requerido: true, valores: ['Categoria']},
    {slot: 'interpretaciones', tipo: 'ref[]', requerido: true, valores: ['InterpretacionAtomica']},
    {slot: 'fuerza', tipo: 'number', requerido: false, minimo: 0, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Suma los valores test absolutos de sus interpretaciones. Si alguno no es finito, la fuerza es infinita.', demonio_regla: 'R-MS-3'},
    {slot: 'posicion', tipo: 'integer', requerido: false, minimo: 1, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Ordena los patrones por fuerza decreciente; el empate se resuelve por nombre.', demonio_regla: 'R-MS-4'},
    {slot: 'proporcion_clases', tipo: 'number', requerido: false, minimo: 0, maximo: 1, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Divide las clases en que la categoría es significativa por el total de clases de la exportación.', demonio_regla: 'R-MS-5, R-MS-6'},
    {slot: 'pertenencia_algunas', tipo: 'number', requerido: false, minimo: 0, maximo: 1, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Evalúa la proporción de clases en la función de pertenencia de «algunas».', demonio_regla: 'R-MS-6'},
    {slot: 'pertenencia_muchas', tipo: 'number', requerido: false, minimo: 0, maximo: 1, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Evalúa la proporción de clases en la función de pertenencia de «muchas».', demonio_regla: 'R-MS-5'}
  ]
AS s
MATCH (c:FrameClass {name: 'PatronEmergente'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// PatronConstante
UNWIND [
    {slot: 'pertenencia_muchas', tipo: 'number', requerido: true, minimo: 0.5, maximo: 1, nota: 'La faceta mínima es el corte de pertenencia.'}
  ]
AS s
MATCH (c:FrameClass {name: 'PatronConstante'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// Singularidad
UNWIND [
    {slot: 'pertenencia_algunas', tipo: 'number', requerido: true, minimo: 0.5, maximo: 1, nota: 'La faceta mínima es el corte de pertenencia.'}
  ]
AS s
MATCH (c:FrameClass {name: 'Singularidad'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// Sintesis
UNWIND [
    {slot: 'exportacion', tipo: 'ref', requerido: true, valores: ['Exportacion']},
    {slot: 'perfil', tipo: 'enum', requerido: true, valores: ['novato', 'intermedio', 'experto']},
    {slot: 'patrones', tipo: 'ref[]', requerido: false, valores: ['PatronEmergente']},
    {slot: 'n_no_significativas', tipo: 'integer', requerido: false, minimo: 0, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Cuenta los pares clasificados como no significativos, que se informan como cantidad.', demonio_regla: 'R-MS-9'},
    {slot: 'secciones', tipo: 'ref[]', requerido: true, valores: ['SeccionDeLaSintesis']},
    {slot: 'verificada', tipo: 'boolean', requerido: false, demonio_tipo: 'IF-NEEDED', demonio_accion: 'Compara cada valor numérico del texto con los valores de los hallazgos.', demonio_regla: 'R-MS-11, R-MS-12'},
    {slot: 'estado_redaccion', tipo: 'enum', requerido: true, valor_defecto: 'redactada', valores: ['redactada', 'estructurada'], demonio_tipo: 'IF-CHANGED', demonio_accion: 'Cuando verificada pasa a falso o el modelo de lenguaje no responde, fija el estado «estructurada» y agrega el aviso.', demonio_regla: 'R-MS-12'}
  ]
AS s
MATCH (c:FrameClass {name: 'Sintesis'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// SeccionDeLaSintesis
UNWIND [
    {slot: 'nombre', tipo: 'string', requerido: true},
    {slot: 'orden', tipo: 'integer', requerido: true, minimo: 1, maximo: 4},
    {slot: 'contenido', tipo: 'string', requerido: true},
    {slot: 'contenido_novato', tipo: 'string', requerido: false},
    {slot: 'debe_incluir', tipo: 'string[]', requerido: false}
  ]
AS s
MATCH (c:FrameClass {name: 'SeccionDeLaSintesis'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// Usuario
UNWIND [
    {slot: 'perfil', tipo: 'enum', requerido: true, valor_defecto: 'intermedio', valores: ['novato', 'intermedio', 'experto'], demonio_tipo: 'IF-CHANGED', demonio_accion: 'Invalida las interpretaciones y la síntesis ya redactadas con el perfil anterior, que deben generarse de nuevo.', demonio_regla: 'R-PU-4'},
    {slot: 'exportacion', tipo: 'ref', requerido: false, valores: ['Exportacion']}
  ]
AS s
MATCH (c:FrameClass {name: 'Usuario'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// PerfilDeUsuario
UNWIND [
    {slot: 'nombre', tipo: 'enum', requerido: true, valores: ['novato', 'intermedio', 'experto']},
    {slot: 'terminologia', tipo: 'enum', requerido: true, valores: ['llana', 'basica', 'tecnica']},
    {slot: 'valor_test', tipo: 'enum', requerido: true, valores: ['solo_nivel', 'valor_y_nivel']},
    {slot: 'frecuencias', tipo: 'enum', requerido: true, valores: ['llano', 'contribucion', 'tecnico']},
    {slot: 'p_valor_visible', tipo: 'boolean', requerido: true},
    {slot: 'class_cat_visible', tipo: 'boolean', requerido: true},
    {slot: 'razon_proporciones_visible', tipo: 'boolean', requerido: true},
    {slot: 'contribuciones_dimensiones', tipo: 'enum', requerido: true, valores: ['no', 'condicionado']},
    {slot: 'instruccion_registro', tipo: 'string', requerido: true},
    {slot: 'guia_redaccion', tipo: 'string[]', requerido: true},
    {slot: 'ejemplo_estilo', tipo: 'string', requerido: true},
    {slot: 'intensidad_llana', tipo: 'json', requerido: false}
  ]
AS s
MATCH (c:FrameClass {name: 'PerfilDeUsuario'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// PerfilNovato
UNWIND [
    {slot: 'nombre', tipo: 'enum', requerido: true, valor_defecto: 'novato', valores: ['novato', 'intermedio', 'experto']},
    {slot: 'terminologia', tipo: 'enum', requerido: true, valor_defecto: 'llana', valores: ['llana', 'basica', 'tecnica']},
    {slot: 'valor_test', tipo: 'enum', requerido: true, valor_defecto: 'solo_nivel', valores: ['solo_nivel', 'valor_y_nivel']},
    {slot: 'frecuencias', tipo: 'enum', requerido: true, valor_defecto: 'llano', valores: ['llano', 'contribucion', 'tecnico']},
    {slot: 'p_valor_visible', tipo: 'boolean', requerido: true, valor_defecto: false},
    {slot: 'class_cat_visible', tipo: 'boolean', requerido: true, valor_defecto: false},
    {slot: 'razon_proporciones_visible', tipo: 'boolean', requerido: true, valor_defecto: false},
    {slot: 'contribuciones_dimensiones', tipo: 'enum', requerido: true, valor_defecto: 'no', valores: ['no', 'condicionado']},
    {slot: 'instruccion_registro', tipo: 'string', requerido: true, valor_defecto: 'Explicaciones conceptuales, analogías simples sin cifras nuevas y frecuencias relativas, sin jerga técnica.'},
    {slot: 'guia_redaccion', tipo: 'string[]', requerido: true, valor_defecto: ['Escribe para alguien sin formación en estadística: frases cortas (una idea por frase) y palabras de uso diario.', 'Nada de jerga: no uses «sobre-representación», «significativo», siglas ni nombres de pruebas. La intensidad de cada asociación ya viene dicha en palabras comunes («mucho más de lo esperable», «algo más de lo esperable»): úsala tal cual para esa asociación y no le pongas la de otra.', 'Cada cifra va en la forma «el N % de los valores de la clase está en este conjunto, cuando en el total ese conjunto sólo reúne el M %».', 'Cierra cada hallazgo con una frase breve y sin cifras que no repita la primera; no agregues adjetivos ni conclusiones propias. No uses la palabra «transición»: di que la misma clase también se asocia con el conjunto vecino.']},
    {slot: 'ejemplo_estilo', tipo: 'string', requerido: true, valor_defecto: 'Hallazgos para el grupo de Ingresos Altos: Este grupo se asocia con dos medios de transporte. El que más lo distingue es el automóvil privado: el 62,4 % de los valores de esta clase está en ese medio, cuando en el total ese medio sólo reúne el 35,0 %; es decir, aparece mucho más de lo esperable. Algo parecido pasa, de forma menos marcada, con la motocicleta, que llega al 41,0 % frente al 22,0 % del total: algo más de lo esperable. En resumen, este grupo se concentra en el automóvil privado y, en menor medida, en la motocicleta.'},
    {slot: 'intensidad_llana', tipo: 'json', requerido: false, valor_defecto: '{"sobre-representación": {"fuerte": "mucho más de lo esperable", "moderada": "algo más de lo esperable", "débil": "apenas más de lo esperable"}, "sub-representación": {"fuerte": "mucho menos de lo esperable", "moderada": "algo menos de lo esperable", "débil": "apenas menos de lo esperable"}}'}
  ]
AS s
MATCH (c:FrameClass {name: 'PerfilNovato'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// PerfilIntermedio
UNWIND [
    {slot: 'nombre', tipo: 'enum', requerido: true, valor_defecto: 'intermedio', valores: ['novato', 'intermedio', 'experto']},
    {slot: 'terminologia', tipo: 'enum', requerido: true, valor_defecto: 'basica', valores: ['llana', 'basica', 'tecnica']},
    {slot: 'valor_test', tipo: 'enum', requerido: true, valor_defecto: 'valor_y_nivel', valores: ['solo_nivel', 'valor_y_nivel']},
    {slot: 'frecuencias', tipo: 'enum', requerido: true, valor_defecto: 'contribucion', valores: ['llano', 'contribucion', 'tecnico']},
    {slot: 'p_valor_visible', tipo: 'boolean', requerido: true, valor_defecto: false},
    {slot: 'class_cat_visible', tipo: 'boolean', requerido: true, valor_defecto: false},
    {slot: 'razon_proporciones_visible', tipo: 'boolean', requerido: true, valor_defecto: false},
    {slot: 'contribuciones_dimensiones', tipo: 'enum', requerido: true, valor_defecto: 'no', valores: ['no', 'condicionado']},
    {slot: 'instruccion_registro', tipo: 'string', requerido: true, valor_defecto: 'Terminología estadística básica, valor test y contribución.'},
    {slot: 'guia_redaccion', tipo: 'string[]', requerido: true, valor_defecto: ['Escribe para alguien con estadística básica: usa «valor test» junto a cada asociación y, en el primer párrafo, incluye una oración propia como esta: «El valor test mide cuán improbable es que la asociación sea casual; no mide cuán intenso es el fenómeno.»', 'Di siempre si la asociación es fuerte, moderada o débil (nunca «fuerza fuerte») y el porcentaje con su comparación («frente al N % del total»).', 'No uses p-valores, Class.Cat ni razones de proporciones. Una idea por frase, sin tecnicismos de más. La primera vez que nombres una transición, aclara que es la misma clase asociada con dos conjuntos vecinos. No enlaces con frases de relleno («Le sigue», «La tercera asociación es», «Cierra el grupo»): nombra la clase y da sus cifras.']},
    {slot: 'ejemplo_estilo', tipo: 'string', requerido: true, valor_defecto: 'Hallazgos para el grupo de Ingresos Altos: Este grupo se asocia con dos medios de transporte. El automóvil privado lo caracteriza fuertemente: con un valor test de 4,50 la asociación es estadísticamente sólida, y el 62,4 % de los valores de la clase está en ese medio frente al 35,0 % del total. La motocicleta también se asocia, de forma moderada (valor test de 2,10; 41,0 % frente al 22,0 % del total). En resumen, el grupo se concentra en el automóvil privado y, con menos fuerza, en la motocicleta.'}
  ]
AS s
MATCH (c:FrameClass {name: 'PerfilIntermedio'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// PerfilExperto
UNWIND [
    {slot: 'nombre', tipo: 'enum', requerido: true, valor_defecto: 'experto', valores: ['novato', 'intermedio', 'experto']},
    {slot: 'terminologia', tipo: 'enum', requerido: true, valor_defecto: 'tecnica', valores: ['llana', 'basica', 'tecnica']},
    {slot: 'valor_test', tipo: 'enum', requerido: true, valor_defecto: 'valor_y_nivel', valores: ['solo_nivel', 'valor_y_nivel']},
    {slot: 'frecuencias', tipo: 'enum', requerido: true, valor_defecto: 'tecnico', valores: ['llano', 'contribucion', 'tecnico']},
    {slot: 'p_valor_visible', tipo: 'boolean', requerido: true, valor_defecto: true},
    {slot: 'class_cat_visible', tipo: 'boolean', requerido: true, valor_defecto: true},
    {slot: 'razon_proporciones_visible', tipo: 'boolean', requerido: true, valor_defecto: true},
    {slot: 'contribuciones_dimensiones', tipo: 'enum', requerido: true, valor_defecto: 'condicionado', valores: ['no', 'condicionado']},
    {slot: 'instruccion_registro', tipo: 'string', requerido: true, valor_defecto: 'Formulación técnica completa: valores test, p-valores, contribuciones de la categoría a la clase y razones de proporciones.'},
    {slot: 'guia_redaccion', tipo: 'string[]', requerido: true, valor_defecto: ['Escribe para alguien con formación estadística: redacción técnica y compacta, sin analogías ni explicaciones de conceptos básicos.', 'De cada asociación da, en una sola cláusula o paréntesis y en este orden: valor test, p, porcentaje frente al total, Class.Cat y razón de proporciones. Si varias asociaciones seguidas tienen la misma intensidad, nómbrala una sola vez («sobre-representaciones fuertes de A (…), de B (…) y de C (…)»).', 'Usa los términos «sobre-representación», «valor test», «Class.Cat» y «razón de proporciones» sin definirlos; señala si cada asociación es fuerte, moderada o débil.']},
    {slot: 'ejemplo_estilo', tipo: 'string', requerido: true, valor_defecto: 'Hallazgos para el grupo de Ingresos Altos: Se observa una sobre-representación fuerte del automóvil privado (valor test 4,50; p < 0,01; 62,4 % frente al 35,0 % del total; Class.Cat 31,2 %; razón de proporciones 1,78) y otra moderada de la motocicleta (valor test 2,10; p = 0,036; 41,0 % frente al 22,0 % del total; Class.Cat 12,5 %; razón de proporciones 1,86). La clase se concentra en el automóvil privado y, en menor grado, en la motocicleta.'}
  ]
AS s
MATCH (c:FrameClass {name: 'PerfilExperto'}), (sl:Slot {name: s.slot})
MERGE (c)-[h:HAS_SLOT]->(sl)
SET h.tipo = s.tipo, h.requerido = s.requerido, h.valor_defecto = s.valor_defecto, h.valores = s.valores, h.minimo = s.minimo, h.maximo = s.maximo, h.demonio_tipo = s.demonio_tipo, h.demonio_accion = s.demonio_accion, h.demonio_regla = s.demonio_regla, h.nota = s.nota;

// ---------- 3. Instancias (FrameInst) y valores (HAS_VALUE)
// Magnitud
UNWIND [
    {id: 'ValorTest'},
    {id: 'PValor'},
    {id: 'CatClass'},
    {id: 'ClassCat'},
    {id: 'Global'},
    {id: 'Weight'}
  ] AS i
MATCH (c:FrameClass {name: 'Magnitud'})
MERGE (n:FrameInst {id: i.id})
MERGE (n)-[:INSTANCE_OF]->(c);
UNWIND [
    {id: 'ValorTest', slot: 'nombre', value: 'Valor test'},
    {id: 'ValorTest', slot: 'columna', value: 'Test.Value'},
    {id: 'ValorTest', slot: 'unidad', value: 'desviaciones típicas'},
    {id: 'ValorTest', slot: 'minimo_valido', value: -1.0E9},
    {id: 'ValorTest', slot: 'maximo_valido', value: 1.0E9},
    {id: 'ValorTest', slot: 'definicion', value: 'Desviación entre la medida observada en un grupo y la de la población, en desviaciones típicas de una ley normal.'},
    {id: 'PValor', slot: 'nombre', value: 'p-valor'},
    {id: 'PValor', slot: 'columna', value: 'p.Value'},
    {id: 'PValor', slot: 'unidad', value: 'probabilidad'},
    {id: 'PValor', slot: 'minimo_valido', value: 0.0},
    {id: 'PValor', slot: 'maximo_valido', value: 1.0},
    {id: 'PValor', slot: 'definicion', value: 'Probabilidad hipergeométrica asociada al valor test.'},
    {id: 'CatClass', slot: 'nombre', value: 'Cat.Class'},
    {id: 'CatClass', slot: 'columna', value: 'Cat.Class'},
    {id: 'CatClass', slot: 'unidad', value: 'porcentaje'},
    {id: 'CatClass', slot: 'minimo_valido', value: 0.0},
    {id: 'CatClass', slot: 'maximo_valido', value: 100.0},
    {id: 'CatClass', slot: 'definicion', value: 'Porcentaje de la línea dentro del bloque (en filas y grupos, de la categoría dentro de la clase; en columnas, de la clase dentro de la categoría).'},
    {id: 'ClassCat', slot: 'nombre', value: 'Class.Cat'},
    {id: 'ClassCat', slot: 'columna', value: 'Class.Cat'},
    {id: 'ClassCat', slot: 'unidad', value: 'porcentaje'},
    {id: 'ClassCat', slot: 'minimo_valido', value: 0.0},
    {id: 'ClassCat', slot: 'maximo_valido', value: 100.0},
    {id: 'ClassCat', slot: 'definicion', value: 'Porcentaje del bloque dentro de la línea (en filas y grupos, de la clase dentro de la categoría; en columnas, de la categoría dentro de la clase).'},
    {id: 'Global', slot: 'nombre', value: 'Global'},
    {id: 'Global', slot: 'columna', value: 'Global'},
    {id: 'Global', slot: 'unidad', value: 'porcentaje'},
    {id: 'Global', slot: 'minimo_valido', value: 0.0},
    {id: 'Global', slot: 'maximo_valido', value: 100.0},
    {id: 'Global', slot: 'definicion', value: 'Porcentaje de la línea en el total (en filas y grupos, de la categoría; en columnas, de la clase).'},
    {id: 'Weight', slot: 'nombre', value: 'Weight'},
    {id: 'Weight', slot: 'columna', value: 'Weight'},
    {id: 'Weight', slot: 'unidad', value: 'peso'},
    {id: 'Weight', slot: 'minimo_valido', value: 0.0},
    {id: 'Weight', slot: 'maximo_valido', value: 1.0E9},
    {id: 'Weight', slot: 'definicion', value: 'Marginal de la línea en la tabla analizada (en filas y grupos, de la categoría; en columnas, de la clase).'}
  ] AS v
MATCH (n:FrameInst {id: v.id}), (s:Slot {name: v.slot})
MERGE (n)-[h:HAS_VALUE]->(s)
SET h.value = v.value;

// EstadoInterpretado
UNWIND [
    {id: 'E1'},
    {id: 'E2'},
    {id: 'E3'},
    {id: 'E4'},
    {id: 'E5'},
    {id: 'E6'},
    {id: 'E7'}
  ] AS i
MATCH (c:FrameClass {name: 'EstadoInterpretado'})
MERGE (n:FrameInst {id: i.id})
MERGE (n)-[:INSTANCE_OF]->(c);
UNWIND [
    {id: 'E1', slot: 'significacion', value: 'altamente significativo'},
    {id: 'E1', slot: 'direccion', value: 'sobre-representación'},
    {id: 'E1', slot: 'intensidad', value: 'fuerte'},
    {id: 'E1', slot: 'explicacion_corta', value: 'V ≥ 2,58: altamente significativo, sobre-representación, fuerte.'},
    {id: 'E2', slot: 'significacion', value: 'significativamente probable'},
    {id: 'E2', slot: 'direccion', value: 'sobre-representación'},
    {id: 'E2', slot: 'intensidad', value: 'moderada'},
    {id: 'E2', slot: 'explicacion_corta', value: '1,96 ≤ V < 2,58: significativamente probable, sobre-representación, moderada.'},
    {id: 'E3', slot: 'significacion', value: 'sugerente'},
    {id: 'E3', slot: 'direccion', value: 'sobre-representación'},
    {id: 'E3', slot: 'intensidad', value: 'débil'},
    {id: 'E3', slot: 'explicacion_corta', value: '1,65 ≤ V < 1,96: sugerente, sobre-representación, débil.'},
    {id: 'E4', slot: 'significacion', value: 'no significativo'},
    {id: 'E4', slot: 'direccion', value: 'neutra'},
    {id: 'E4', slot: 'intensidad', value: 'nula'},
    {id: 'E4', slot: 'explicacion_corta', value: '−1,65 < V < 1,65: no significativo, neutra, nula.'},
    {id: 'E5', slot: 'significacion', value: 'sugerente'},
    {id: 'E5', slot: 'direccion', value: 'sub-representación'},
    {id: 'E5', slot: 'intensidad', value: 'débil'},
    {id: 'E5', slot: 'explicacion_corta', value: '−1,96 < V ≤ −1,65: sugerente, sub-representación, débil.'},
    {id: 'E6', slot: 'significacion', value: 'significativamente probable'},
    {id: 'E6', slot: 'direccion', value: 'sub-representación'},
    {id: 'E6', slot: 'intensidad', value: 'moderada'},
    {id: 'E6', slot: 'explicacion_corta', value: '−2,58 < V ≤ −1,96: significativamente probable, sub-representación, moderada.'},
    {id: 'E7', slot: 'significacion', value: 'altamente significativo'},
    {id: 'E7', slot: 'direccion', value: 'sub-representación'},
    {id: 'E7', slot: 'intensidad', value: 'fuerte'},
    {id: 'E7', slot: 'explicacion_corta', value: 'V ≤ −2,58: altamente significativo, sub-representación, fuerte.'}
  ] AS v
MATCH (n:FrameInst {id: v.id}), (s:Slot {name: v.slot})
MERGE (n)-[h:HAS_VALUE]->(s)
SET h.value = v.value;

// Rango
UNWIND [
    {id: 'RG1'},
    {id: 'RG2'},
    {id: 'RG3'},
    {id: 'RG4'},
    {id: 'RG5'},
    {id: 'RG6'},
    {id: 'RG7'}
  ] AS i
MATCH (c:FrameClass {name: 'Rango'})
MERGE (n:FrameInst {id: i.id})
MERGE (n)-[:INSTANCE_OF]->(c);
UNWIND [
    {id: 'RG1', slot: 'nombre', value: 'RG1'},
    {id: 'RG1', slot: 'limite_inferior', value: 2.58},
    {id: 'RG1', slot: 'limite_superior', value: 1.0E9},
    {id: 'RG1', slot: 'cierre_inferior', value: true},
    {id: 'RG1', slot: 'cierre_superior', value: false},
    {id: 'RG2', slot: 'nombre', value: 'RG2'},
    {id: 'RG2', slot: 'limite_inferior', value: 1.96},
    {id: 'RG2', slot: 'limite_superior', value: 2.58},
    {id: 'RG2', slot: 'cierre_inferior', value: true},
    {id: 'RG2', slot: 'cierre_superior', value: false},
    {id: 'RG3', slot: 'nombre', value: 'RG3'},
    {id: 'RG3', slot: 'limite_inferior', value: 1.65},
    {id: 'RG3', slot: 'limite_superior', value: 1.96},
    {id: 'RG3', slot: 'cierre_inferior', value: true},
    {id: 'RG3', slot: 'cierre_superior', value: false},
    {id: 'RG4', slot: 'nombre', value: 'RG4'},
    {id: 'RG4', slot: 'limite_inferior', value: -1.65},
    {id: 'RG4', slot: 'limite_superior', value: 1.65},
    {id: 'RG4', slot: 'cierre_inferior', value: false},
    {id: 'RG4', slot: 'cierre_superior', value: false},
    {id: 'RG5', slot: 'nombre', value: 'RG5'},
    {id: 'RG5', slot: 'limite_inferior', value: -1.96},
    {id: 'RG5', slot: 'limite_superior', value: -1.65},
    {id: 'RG5', slot: 'cierre_inferior', value: false},
    {id: 'RG5', slot: 'cierre_superior', value: true},
    {id: 'RG6', slot: 'nombre', value: 'RG6'},
    {id: 'RG6', slot: 'limite_inferior', value: -2.58},
    {id: 'RG6', slot: 'limite_superior', value: -1.96},
    {id: 'RG6', slot: 'cierre_inferior', value: false},
    {id: 'RG6', slot: 'cierre_superior', value: true},
    {id: 'RG7', slot: 'nombre', value: 'RG7'},
    {id: 'RG7', slot: 'limite_inferior', value: -1.0E9},
    {id: 'RG7', slot: 'limite_superior', value: -2.58},
    {id: 'RG7', slot: 'cierre_inferior', value: false},
    {id: 'RG7', slot: 'cierre_superior', value: true}
  ] AS v
MATCH (n:FrameInst {id: v.id}), (s:Slot {name: v.slot})
MERGE (n)-[h:HAS_VALUE]->(s)
SET h.value = v.value;

// Parametro
UNWIND [
    {id: 'PR1'},
    {id: 'PR2'},
    {id: 'PR3'},
    {id: 'PR4'},
    {id: 'PR5'}
  ] AS i
MATCH (c:FrameClass {name: 'Parametro'})
MERGE (n:FrameInst {id: i.id})
MERGE (n)-[:INSTANCE_OF]->(c);
UNWIND [
    {id: 'PR1', slot: 'nombre', value: 'umbral_p_exacto'},
    {id: 'PR1', slot: 'valor', value: 0.01},
    {id: 'PR1', slot: 'unidad', value: 'probabilidad'},
    {id: 'PR1', slot: 'regla', value: 'R-MI-9'},
    {id: 'PR1', slot: 'estado', value: 'Confirmado'},
    {id: 'PR1', slot: 'fundamento', value: 'Catálogo (A4, 4.2): el p-valor se informa exacto desde 0,01 y como «p < 0,01» por debajo.'},
    {id: 'PR2', slot: 'nombre', value: 'umbral_peso_bajo'},
    {id: 'PR2', slot: 'valor', value: 2.0},
    {id: 'PR2', slot: 'unidad', value: '% del total (Global)'},
    {id: 'PR2', slot: 'regla', value: 'R-MI-11'},
    {id: 'PR2', slot: 'estado', value: 'Confirmado'},
    {id: 'PR2', slot: 'fundamento', value: 'En las exportaciones de horas de docencia, cuatro de los 29 elementos de línea tienen un Global entre 1,0 % y 1,9 %, y el siguiente valor es 2,1 %; en las de área y entropía el mínimo es 11,9 %. El umbral de 2 % separa esos valores aislados del resto.'},
    {id: 'PR3', slot: 'nombre', value: 'distancia_contigua'},
    {id: 'PR3', slot: 'valor', value: 1},
    {id: 'PR3', slot: 'unidad', value: 'posiciones de índice'},
    {id: 'PR3', slot: 'regla', value: 'R-MI-12'},
    {id: 'PR3', slot: 'estado', value: 'Confirmado'},
    {id: 'PR3', slot: 'fundamento', value: 'Dos categorías son contiguas si sus números de orden dentro de la variable difieren en uno (por ejemplo, Are1 y Are2).'},
    {id: 'PR4', slot: 'nombre', value: 'minimo_clases'},
    {id: 'PR4', slot: 'valor', value: 4},
    {id: 'PR4', slot: 'unidad', value: 'clases'},
    {id: 'PR4', slot: 'regla', value: 'R-MS-5, R-MS-6'},
    {id: 'PR4', slot: 'estado', value: 'Confirmado'},
    {id: 'PR4', slot: 'fundamento', value: 'Con menos de cuatro clases la proporción no distingue «muchas» de «algunas»: con tres clases una sola equivale al 33 %.'},
    {id: 'PR5', slot: 'nombre', value: 'corte_pertenencia'},
    {id: 'PR5', slot: 'valor', value: 0.5},
    {id: 'PR5', slot: 'unidad', value: 'grado de pertenencia'},
    {id: 'PR5', slot: 'regla', value: 'R-MS-5, R-MS-6'},
    {id: 'PR5', slot: 'estado', value: 'Confirmado'},
    {id: 'PR5', slot: 'fundamento', value: 'Corte alfa de 0,5: la categoría pertenece al término si su grado alcanza o supera el de no pertenecer.'}
  ] AS v
MATCH (n:FrameInst {id: v.id}), (s:Slot {name: v.slot})
MERGE (n)-[h:HAS_VALUE]->(s)
SET h.value = v.value;

// ConjuntoDifuso
UNWIND [
    {id: 'CD_algunas'},
    {id: 'CD_muchas'}
  ] AS i
MATCH (c:FrameClass {name: 'ConjuntoDifuso'})
MERGE (n:FrameInst {id: i.id})
MERGE (n)-[:INSTANCE_OF]->(c);
UNWIND [
    {id: 'CD_algunas', slot: 'nombre', value: 'algunas'},
    {id: 'CD_algunas', slot: 'variable', value: 'proporcion_de_clases'},
    {id: 'CD_algunas', slot: 'funcion_pertenencia', value: 'trapezoidal'},
    {id: 'CD_algunas', slot: 'parametros', value: [0.0, 0.0, 0.25, 0.5]},
    {id: 'CD_muchas', slot: 'nombre', value: 'muchas'},
    {id: 'CD_muchas', slot: 'variable', value: 'proporcion_de_clases'},
    {id: 'CD_muchas', slot: 'funcion_pertenencia', value: 'trapezoidal'},
    {id: 'CD_muchas', slot: 'parametros', value: [0.3, 0.6, 1.0, 1.0]}
  ] AS v
MATCH (n:FrameInst {id: v.id}), (s:Slot {name: v.slot})
MERGE (n)-[h:HAS_VALUE]->(s)
SET h.value = v.value;

// AdvertenciaMetodologica
UNWIND [
    {id: 'AD1'},
    {id: 'AD2'},
    {id: 'AD3'},
    {id: 'AD4'},
    {id: 'AD5'},
    {id: 'AD6'},
    {id: 'AD7'}
  ] AS i
MATCH (c:FrameClass {name: 'AdvertenciaMetodologica'})
MERGE (n:FrameInst {id: i.id})
MERGE (n)-[:INSTANCE_OF]->(c);
UNWIND [
    {id: 'AD1', slot: 'texto', value: 'El valor test indica la significación de la asociación y no la magnitud del fenómeno.'},
    {id: 'AD1', slot: 'disparador', value: 'siempre'},
    {id: 'AD2', slot: 'texto', value: 'La asociación se apoya en pocos datos.'},
    {id: 'AD2', slot: 'disparador', value: 'peso_bajo'},
    {id: 'AD3', slot: 'texto', value: 'La exportación de DaFu contiene sólo asociaciones positivas con valor test mayor o igual que 1,65; las asociaciones negativas y las no significativas no se informan.'},
    {id: 'AD3', slot: 'texto_novato', value: 'AIDA sólo informa las asociaciones claras en las que un valor aparece más de lo esperado; las demás no figuran en el archivo de DaFu.'},
    {id: 'AD3', slot: 'disparador', value: 'sintesis'},
    {id: 'AD4', slot: 'texto', value: 'La tabla de contingencia fue escalada antes del análisis, por lo que los porcentajes son frecuencias relativas de la tabla escalada y no de los datos originales.'},
    {id: 'AD4', slot: 'texto_novato', value: 'Los datos se reescalaron antes del análisis: los porcentajes son proporciones de la tabla reescalada y no de los datos originales.'},
    {id: 'AD4', slot: 'disparador', value: 'escalado'},
    {id: 'AD5', slot: 'texto', value: 'La tabla de contingencia no fue escalada; los porcentajes son frecuencias relativas de los datos originales.'},
    {id: 'AD5', slot: 'texto_novato', value: 'Los datos no se reescalaron: los porcentajes son proporciones de los datos originales.'},
    {id: 'AD5', slot: 'disparador', value: 'no_escalado'},
    {id: 'AD6', slot: 'texto', value: 'Los resultados dependen de la elección de los conjuntos difusos: otra cantidad de conjuntos u otros límites pueden producir asociaciones distintas.'},
    {id: 'AD6', slot: 'texto_novato', value: 'Los resultados dependen de cómo se definieron los conjuntos difusos (los grupos de valores): con otra cantidad de conjuntos o con otros límites podrían aparecer asociaciones distintas.'},
    {id: 'AD6', slot: 'disparador', value: 'sintesis'},
    {id: 'AD7', slot: 'texto', value: 'El valor test mide la significación estadística de cada asociación y no la intensidad del fenómeno.'},
    {id: 'AD7', slot: 'texto_novato', value: 'Que una asociación sea clara no significa que el fenómeno sea más intenso.'},
    {id: 'AD7', slot: 'disparador', value: 'sintesis'}
  ] AS v
MATCH (n:FrameInst {id: v.id}), (s:Slot {name: v.slot})
MERGE (n)-[h:HAS_VALUE]->(s)
SET h.value = v.value;

// SeccionDeLaSintesis
UNWIND [
    {id: 'S1'},
    {id: 'S2'},
    {id: 'S3'},
    {id: 'S4'}
  ] AS i
MATCH (c:FrameClass {name: 'SeccionDeLaSintesis'})
MERGE (n:FrameInst {id: i.id})
MERGE (n)-[:INSTANCE_OF]->(c);
UNWIND [
    {id: 'S1', slot: 'nombre', value: 'Descripción general'},
    {id: 'S1', slot: 'orden', value: 1},
    {id: 'S1', slot: 'contenido', value: 'Tipo de descripción, archivo analizado, cantidad de clases y de categorías.'},
    {id: 'S1', slot: 'debe_incluir', value: []},
    {id: 'S2', slot: 'nombre', value: 'Resultados relevantes'},
    {id: 'S2', slot: 'orden', value: 2},
    {id: 'S2', slot: 'contenido_novato', value: 'Un apartado por conjunto difuso, de mayor a menor relevancia. En cada uno: con qué clases se asocia, qué tienen en común y en qué proporción de sus valores.'},
    {id: 'S2', slot: 'contenido', value: 'Un apartado por conjunto difuso, en orden de fuerza. En cada uno: con qué clases se asocia y qué tienen en común (las variables que comparten), sus asociaciones de mayor valor test con las cifras y, si las hay, sus transiciones con conjuntos contiguos.'},
    {id: 'S2', slot: 'debe_incluir', value: []},
    {id: 'S3', slot: 'nombre', value: 'Interpretación conclusiva'},
    {id: 'S3', slot: 'orden', value: 3},
    {id: 'S3', slot: 'contenido', value: 'Lectura de conjunto de los patrones, en términos estadísticos: en qué se parecen y en qué se diferencian las clases o grupos de clases según los conjuntos con que se asocian. Sólo cuando los conjuntos difieren en ello, cuáles se asocian con muchas clases (patrones constantes) y cuáles con pocas (singularidades).'},
    {id: 'S3', slot: 'debe_incluir', value: ['distinción entre las diferencias estadísticamente relevantes y las que no lo son']},
    {id: 'S4', slot: 'nombre', value: 'Limitaciones metodológicas'},
    {id: 'S4', slot: 'orden', value: 4},
    {id: 'S4', slot: 'contenido', value: 'Límites del método que condicionan la lectura de los resultados.'},
    {id: 'S4', slot: 'debe_incluir', value: ['escalado de la tabla', 'elección de los conjuntos difusos']}
  ] AS v
MATCH (n:FrameInst {id: v.id}), (s:Slot {name: v.slot})
MERGE (n)-[h:HAS_VALUE]->(s)
SET h.value = v.value;

// Plantilla
UNWIND [
    {id: 'P-MI-1'},
    {id: 'P-MI-2'},
    {id: 'P-MI-3'},
    {id: 'P-MI-4'},
    {id: 'P-MI-5'},
    {id: 'PV-1-N'},
    {id: 'PV-1-I'},
    {id: 'PV-1-E'},
    {id: 'PV-2-N'},
    {id: 'PV-2-I'},
    {id: 'PV-2-E'},
    {id: 'PV-3-N'},
    {id: 'PV-3-I'},
    {id: 'PV-3-E'},
    {id: 'PV-4-N'},
    {id: 'PV-4-I'},
    {id: 'PV-4-E'},
    {id: 'PV-5-N'},
    {id: 'PV-6-N'},
    {id: 'PV-7-N'},
    {id: 'PV-5-I'},
    {id: 'PV-5-E'},
    {id: 'PT-1'},
    {id: 'PT-1-N'}
  ] AS i
MATCH (c:FrameClass {name: 'Plantilla'})
MERGE (n:FrameInst {id: i.id})
MERGE (n)-[:INSTANCE_OF]->(c);
UNWIND [
    {id: 'P-MI-1', slot: 'perfil', value: 'todos'},
    {id: 'P-MI-1', slot: 'texto', value: 'Muy significativo. La categoría «[categoría]» tiene una fuerte asociación en [clase] (valor test = [V]; p < 0,01).'},
    {id: 'P-MI-1', slot: 'campos', value: ['categoría', 'clase', 'V']},
    {id: 'P-MI-2', slot: 'perfil', value: 'todos'},
    {id: 'P-MI-2', slot: 'texto', value: 'Significativo. La categoría «[categoría]» tiene una asociación en [clase] (valor test = [V]; p = [p]).'},
    {id: 'P-MI-2', slot: 'campos', value: ['categoría', 'clase', 'V', 'p']},
    {id: 'P-MI-3', slot: 'perfil', value: 'todos'},
    {id: 'P-MI-3', slot: 'texto', value: 'Poco significativo. La categoría «[categoría]» tiene una asociación débil en [clase] (valor test = [V]; p = [p]).'},
    {id: 'P-MI-3', slot: 'campos', value: ['categoría', 'clase', 'V', 'p']},
    {id: 'P-MI-4', slot: 'perfil', value: 'todos'},
    {id: 'P-MI-4', slot: 'texto', value: 'La característica evaluada no muestra evidencia suficiente para considerarse propia del grupo analizado, debido a que el valor test no alcanza el valor crítico.'},
    {id: 'P-MI-4', slot: 'campos', value: []},
    {id: 'P-MI-5', slot: 'perfil', value: 'todos'},
    {id: 'P-MI-5', slot: 'texto', value: 'La modalidad presenta asociación inversa con la clase, dado que el valor test es negativo y estadísticamente relevante.'},
    {id: 'P-MI-5', slot: 'campos', value: []},
    {id: 'PV-1-N', slot: 'perfil', value: 'novato'},
    {id: 'PV-1-N', slot: 'texto', value: 'En [bloque], el [Cat.Class] % de los valores corresponde a [línea], mientras que en el total esa proporción es del [Global] %. Esa concentración distingue a [bloque] de los demás y es muy poco probable que se deba al azar. No indica que el fenómeno sea más intenso en [bloque].'},
    {id: 'PV-1-N', slot: 'campos', value: ['bloque', 'línea', 'Cat.Class', 'Global']},
    {id: 'PV-1-I', slot: 'perfil', value: 'intermedio'},
    {id: 'PV-1-I', slot: 'texto', value: '[línea] caracteriza a [bloque]: valor test = [V] (altamente significativo). Su contribución a [bloque] es del [Cat.Class] %, frente al [Global] % del total. El valor test indica significación de la asociación, no magnitud del fenómeno.'},
    {id: 'PV-1-I', slot: 'campos', value: ['línea', 'bloque', 'V', 'Cat.Class', 'Global']},
    {id: 'PV-1-E', slot: 'perfil', value: 'experto'},
    {id: 'PV-1-E', slot: 'texto', value: '[línea] en [bloque]: V = [V]; [p] (R-MI-1, sobre-representación). Cat.Class = [Cat.Class] %; Global = [Global] %; razón de proporciones = [razón]; Class.Cat = [Class.Cat] %. El valor test expresa la improbabilidad de la asociación bajo independencia, no la intensidad del fenómeno.'},
    {id: 'PV-1-E', slot: 'campos', value: ['línea', 'bloque', 'V', 'p', 'Cat.Class', 'Global', 'razón', 'Class.Cat']},
    {id: 'PV-2-N', slot: 'perfil', value: 'novato'},
    {id: 'PV-2-N', slot: 'texto', value: 'En [bloque], el [Cat.Class] % de los valores corresponde a [línea], mientras que en el total esa proporción es del [Global] %. Es poco probable que esa diferencia se deba al azar. No indica que el fenómeno sea más intenso en [bloque].'},
    {id: 'PV-2-N', slot: 'campos', value: ['bloque', 'línea', 'Cat.Class', 'Global']},
    {id: 'PV-2-I', slot: 'perfil', value: 'intermedio'},
    {id: 'PV-2-I', slot: 'texto', value: '[línea] caracteriza a [bloque]: valor test = [V] (significativamente probable). Su contribución a [bloque] es del [Cat.Class] %, frente al [Global] % del total. El valor test indica significación de la asociación, no magnitud del fenómeno.'},
    {id: 'PV-2-I', slot: 'campos', value: ['línea', 'bloque', 'V', 'Cat.Class', 'Global']},
    {id: 'PV-2-E', slot: 'perfil', value: 'experto'},
    {id: 'PV-2-E', slot: 'texto', value: '[línea] en [bloque]: V = [V]; [p] (R-MI-2, sobre-representación). Cat.Class = [Cat.Class] %; Global = [Global] %; razón de proporciones = [razón]; Class.Cat = [Class.Cat] %. El valor test expresa la improbabilidad de la asociación bajo independencia, no la intensidad del fenómeno.'},
    {id: 'PV-2-E', slot: 'campos', value: ['línea', 'bloque', 'V', 'p', 'Cat.Class', 'Global', 'razón', 'Class.Cat']},
    {id: 'PV-3-N', slot: 'perfil', value: 'novato'},
    {id: 'PV-3-N', slot: 'texto', value: 'En [bloque], el [Cat.Class] % de los valores corresponde a [línea], mientras que en el total esa proporción es del [Global] %. La diferencia es un indicio, pero podría deberse al azar. No indica que el fenómeno sea más intenso en [bloque].'},
    {id: 'PV-3-N', slot: 'campos', value: ['bloque', 'línea', 'Cat.Class', 'Global']},
    {id: 'PV-3-I', slot: 'perfil', value: 'intermedio'},
    {id: 'PV-3-I', slot: 'texto', value: '[línea] se asocia con [bloque]: valor test = [V] (sugerente). Su contribución a [bloque] es del [Cat.Class] %, frente al [Global] % del total. El valor test indica significación de la asociación, no magnitud del fenómeno.'},
    {id: 'PV-3-I', slot: 'campos', value: ['línea', 'bloque', 'V', 'Cat.Class', 'Global']},
    {id: 'PV-3-E', slot: 'perfil', value: 'experto'},
    {id: 'PV-3-E', slot: 'texto', value: '[línea] en [bloque]: V = [V]; [p] (R-MI-3, sobre-representación). Cat.Class = [Cat.Class] %; Global = [Global] %; razón de proporciones = [razón]; Class.Cat = [Class.Cat] %. El valor test expresa la improbabilidad de la asociación bajo independencia, no la intensidad del fenómeno.'},
    {id: 'PV-3-E', slot: 'campos', value: ['línea', 'bloque', 'V', 'p', 'Cat.Class', 'Global', 'razón', 'Class.Cat']},
    {id: 'PV-4-N', slot: 'perfil', value: 'novato'},
    {id: 'PV-4-N', slot: 'texto', value: 'En [bloque], el [Cat.Class] % de los valores corresponde a [línea], frente al [Global] % del total. Esa diferencia es pequeña y bien puede deberse al azar, por lo que no hay evidencia suficiente para decir que [línea] distingue a [bloque]. No indica que el fenómeno sea más ni menos intenso en [bloque].'},
    {id: 'PV-4-N', slot: 'campos', value: ['bloque', 'línea', 'Cat.Class', 'Global']},
    {id: 'PV-4-I', slot: 'perfil', value: 'intermedio'},
    {id: 'PV-4-I', slot: 'texto', value: '[línea] no se asocia de forma significativa con [bloque]: valor test = [V] (no significativo). Su contribución a [bloque] es del [Cat.Class] %, frente al [Global] % del total. El valor test indica significación de la asociación, no magnitud del fenómeno.'},
    {id: 'PV-4-I', slot: 'campos', value: ['línea', 'bloque', 'V', 'Cat.Class', 'Global']},
    {id: 'PV-4-E', slot: 'perfil', value: 'experto'},
    {id: 'PV-4-E', slot: 'texto', value: '[línea] en [bloque]: V = [V]; [p] ([regla], no significativo). Cat.Class = [Cat.Class] %; Global = [Global] %; razón de proporciones = [razón]; Class.Cat = [Class.Cat] %. El valor test expresa la improbabilidad de la asociación bajo independencia, no la intensidad del fenómeno.'},
    {id: 'PV-4-E', slot: 'campos', value: ['línea', 'bloque', 'V', 'p', 'regla', 'Cat.Class', 'Global', 'razón', 'Class.Cat']},
    {id: 'PV-5-N', slot: 'perfil', value: 'novato'},
    {id: 'PV-5-N', slot: 'texto', value: 'En [bloque], [línea] aparece menos de lo esperado: el [Cat.Class] % de los valores, frente al [Global] % del total. La diferencia es un indicio, pero podría deberse al azar. No indica que el fenómeno sea menos intenso en [bloque].'},
    {id: 'PV-5-N', slot: 'campos', value: ['bloque', 'línea', 'Cat.Class', 'Global']},
    {id: 'PV-6-N', slot: 'perfil', value: 'novato'},
    {id: 'PV-6-N', slot: 'texto', value: 'En [bloque], [línea] aparece menos de lo esperado: el [Cat.Class] % de los valores, frente al [Global] % del total. Es poco probable que esa diferencia se deba al azar. No indica que el fenómeno sea menos intenso en [bloque].'},
    {id: 'PV-6-N', slot: 'campos', value: ['bloque', 'línea', 'Cat.Class', 'Global']},
    {id: 'PV-7-N', slot: 'perfil', value: 'novato'},
    {id: 'PV-7-N', slot: 'texto', value: 'En [bloque], [línea] aparece menos de lo esperado: el [Cat.Class] % de los valores, frente al [Global] % del total. Es muy poco probable que esa diferencia se deba al azar. No indica que el fenómeno sea menos intenso en [bloque].'},
    {id: 'PV-7-N', slot: 'campos', value: ['bloque', 'línea', 'Cat.Class', 'Global']},
    {id: 'PV-5-I', slot: 'perfil', value: 'intermedio'},
    {id: 'PV-5-I', slot: 'texto', value: '[línea] presenta sub-representación en [bloque]: valor test = [V] ([significación]). Su contribución a [bloque] es del [Cat.Class] %, frente al [Global] % del total. El valor test indica significación de la asociación, no magnitud del fenómeno.'},
    {id: 'PV-5-I', slot: 'campos', value: ['línea', 'bloque', 'V', 'significación', 'Cat.Class', 'Global']},
    {id: 'PV-5-E', slot: 'perfil', value: 'experto'},
    {id: 'PV-5-E', slot: 'texto', value: '[línea] en [bloque]: V = [V]; [p] ([regla], sub-representación). Cat.Class = [Cat.Class] %; Global = [Global] %; razón de proporciones = [razón]; Class.Cat = [Class.Cat] %. El valor test expresa la improbabilidad de la asociación bajo independencia, no la intensidad del fenómeno.'},
    {id: 'PV-5-E', slot: 'campos', value: ['línea', 'bloque', 'V', 'p', 'regla', 'Cat.Class', 'Global', 'razón', 'Class.Cat']},
    {id: 'PT-1', slot: 'perfil', value: 'todos'},
    {id: 'PT-1', slot: 'texto', value: 'En [clase], [categoría] es contigua a [contigua]; en conjunto describen una transición entre categorías contiguas.'},
    {id: 'PT-1', slot: 'campos', value: ['clase', 'categoría', 'contigua']},
    {id: 'PT-1-N', slot: 'perfil', value: 'novato'},
    {id: 'PT-1-N', slot: 'texto', value: '[clase] se asocia además con [contigua], al lado de [categoría] en la escala de valores.'},
    {id: 'PT-1-N', slot: 'campos', value: ['clase', 'categoría', 'contigua']}
  ] AS v
MATCH (n:FrameInst {id: v.id}), (s:Slot {name: v.slot})
MERGE (n)-[h:HAS_VALUE]->(s)
SET h.value = v.value;

// Regla
UNWIND [
    {id: 'R-MI-1'},
    {id: 'R-MI-2'},
    {id: 'R-MI-3'},
    {id: 'R-MI-4'},
    {id: 'R-MI-5'},
    {id: 'R-MI-6'},
    {id: 'R-MI-7'},
    {id: 'R-MI-8'},
    {id: 'R-MI-9'},
    {id: 'R-MI-10'},
    {id: 'R-MI-11'},
    {id: 'R-MI-12'},
    {id: 'R-MI-13'},
    {id: 'R-MS-1'},
    {id: 'R-MS-2'},
    {id: 'R-MS-3'},
    {id: 'R-MS-4'},
    {id: 'R-MS-5'},
    {id: 'R-MS-6'},
    {id: 'R-MS-7'},
    {id: 'R-MS-8'},
    {id: 'R-MS-9'},
    {id: 'R-MS-10'},
    {id: 'R-MS-11'},
    {id: 'R-MS-12'},
    {id: 'R-PU-1'},
    {id: 'R-PU-2'},
    {id: 'R-PU-3'},
    {id: 'R-PU-4'}
  ] AS i
MATCH (c:FrameClass {name: 'Regla'})
MERGE (n:FrameInst {id: i.id})
MERGE (n)-[:INSTANCE_OF]->(c);
UNWIND [
    {id: 'R-MI-1', slot: 'enunciado', value: 'V ≥ 2,58: altamente significativo, sobre-representación, fuerte.'},
    {id: 'R-MI-1', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-1', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-1', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MI-1', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-1', slot: 'fuente', value: 'F2; F3'},
    {id: 'R-MI-1', slot: 'subprocesos', value: ['SP3']},
    {id: 'R-MI-1', slot: 'condicion', value: '{"todas": [{"campo": "valor_observado[ValorTest].valor_crisp", "op": "en_rango", "valor": "RG1"}]}'},
    {id: 'R-MI-1', slot: 'conclusion', value: '{"asigna": [{"campo": "valor_observado[ValorTest].rango_resultante", "op": "=", "valor": "RG1"}, {"campo": "par.estado", "op": "=", "valor": "E1"}]}'},
    {id: 'R-MI-1', slot: 'excepcion', value: ''},
    {id: 'R-MI-1', slot: 'explicacion', value: 'Los umbrales 1,65, 1,96 y 2,58 y el signo del valor test delimitan siete rangos disjuntos que cubren la recta (catálogo A4, 4.1; Informe Inicial).'},
    {id: 'R-MI-1', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MI-1', slot: 'decision', value: ''},
    {id: 'R-MI-2', slot: 'enunciado', value: '1,96 ≤ V < 2,58: significativamente probable, sobre-representación, moderada.'},
    {id: 'R-MI-2', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-2', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-2', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MI-2', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-2', slot: 'fuente', value: 'F2; F3'},
    {id: 'R-MI-2', slot: 'subprocesos', value: ['SP3']},
    {id: 'R-MI-2', slot: 'condicion', value: '{"todas": [{"campo": "valor_observado[ValorTest].valor_crisp", "op": "en_rango", "valor": "RG2"}]}'},
    {id: 'R-MI-2', slot: 'conclusion', value: '{"asigna": [{"campo": "valor_observado[ValorTest].rango_resultante", "op": "=", "valor": "RG2"}, {"campo": "par.estado", "op": "=", "valor": "E2"}]}'},
    {id: 'R-MI-2', slot: 'excepcion', value: ''},
    {id: 'R-MI-2', slot: 'explicacion', value: 'Los umbrales 1,65, 1,96 y 2,58 y el signo del valor test delimitan siete rangos disjuntos que cubren la recta (catálogo A4, 4.1; Informe Inicial).'},
    {id: 'R-MI-2', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MI-2', slot: 'decision', value: ''},
    {id: 'R-MI-3', slot: 'enunciado', value: '1,65 ≤ V < 1,96: sugerente, sobre-representación, débil.'},
    {id: 'R-MI-3', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-3', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-3', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MI-3', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-3', slot: 'fuente', value: 'F2; F3'},
    {id: 'R-MI-3', slot: 'subprocesos', value: ['SP3']},
    {id: 'R-MI-3', slot: 'condicion', value: '{"todas": [{"campo": "valor_observado[ValorTest].valor_crisp", "op": "en_rango", "valor": "RG3"}]}'},
    {id: 'R-MI-3', slot: 'conclusion', value: '{"asigna": [{"campo": "valor_observado[ValorTest].rango_resultante", "op": "=", "valor": "RG3"}, {"campo": "par.estado", "op": "=", "valor": "E3"}]}'},
    {id: 'R-MI-3', slot: 'excepcion', value: ''},
    {id: 'R-MI-3', slot: 'explicacion', value: 'Los umbrales 1,65, 1,96 y 2,58 y el signo del valor test delimitan siete rangos disjuntos que cubren la recta (catálogo A4, 4.1; Informe Inicial).'},
    {id: 'R-MI-3', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MI-3', slot: 'decision', value: ''},
    {id: 'R-MI-4', slot: 'enunciado', value: '−1,65 < V < 1,65: no significativo, neutra, nula.'},
    {id: 'R-MI-4', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-4', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-4', slot: 'aplicabilidad', value: 'Latente'},
    {id: 'R-MI-4', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-4', slot: 'fuente', value: 'F2; F3'},
    {id: 'R-MI-4', slot: 'subprocesos', value: ['SP3']},
    {id: 'R-MI-4', slot: 'condicion', value: '{"todas": [{"campo": "valor_observado[ValorTest].valor_crisp", "op": "en_rango", "valor": "RG4"}]}'},
    {id: 'R-MI-4', slot: 'conclusion', value: '{"asigna": [{"campo": "valor_observado[ValorTest].rango_resultante", "op": "=", "valor": "RG4"}, {"campo": "par.estado", "op": "=", "valor": "E4"}]}'},
    {id: 'R-MI-4', slot: 'excepcion', value: 'Latente: la exportación actual no incluye pares con |V| menor que 1,65.'},
    {id: 'R-MI-4', slot: 'explicacion', value: 'Los umbrales 1,65, 1,96 y 2,58 y el signo del valor test delimitan siete rangos disjuntos que cubren la recta (catálogo A4, 4.1; Informe Inicial).'},
    {id: 'R-MI-4', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MI-4', slot: 'decision', value: ''},
    {id: 'R-MI-5', slot: 'enunciado', value: '−1,96 < V ≤ −1,65: sugerente, sub-representación, débil.'},
    {id: 'R-MI-5', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-5', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-5', slot: 'aplicabilidad', value: 'Latente'},
    {id: 'R-MI-5', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-5', slot: 'fuente', value: 'F2; F3'},
    {id: 'R-MI-5', slot: 'subprocesos', value: ['SP3']},
    {id: 'R-MI-5', slot: 'condicion', value: '{"todas": [{"campo": "valor_observado[ValorTest].valor_crisp", "op": "en_rango", "valor": "RG5"}]}'},
    {id: 'R-MI-5', slot: 'conclusion', value: '{"asigna": [{"campo": "valor_observado[ValorTest].rango_resultante", "op": "=", "valor": "RG5"}, {"campo": "par.estado", "op": "=", "valor": "E5"}]}'},
    {id: 'R-MI-5', slot: 'excepcion', value: ''},
    {id: 'R-MI-5', slot: 'explicacion', value: 'Los umbrales 1,65, 1,96 y 2,58 y el signo del valor test delimitan siete rangos disjuntos que cubren la recta (catálogo A4, 4.1; Informe Inicial).'},
    {id: 'R-MI-5', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MI-5', slot: 'decision', value: ''},
    {id: 'R-MI-6', slot: 'enunciado', value: '−2,58 < V ≤ −1,96: significativamente probable, sub-representación, moderada.'},
    {id: 'R-MI-6', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-6', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-6', slot: 'aplicabilidad', value: 'Latente'},
    {id: 'R-MI-6', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-6', slot: 'fuente', value: 'F2; F3'},
    {id: 'R-MI-6', slot: 'subprocesos', value: ['SP3']},
    {id: 'R-MI-6', slot: 'condicion', value: '{"todas": [{"campo": "valor_observado[ValorTest].valor_crisp", "op": "en_rango", "valor": "RG6"}]}'},
    {id: 'R-MI-6', slot: 'conclusion', value: '{"asigna": [{"campo": "valor_observado[ValorTest].rango_resultante", "op": "=", "valor": "RG6"}, {"campo": "par.estado", "op": "=", "valor": "E6"}]}'},
    {id: 'R-MI-6', slot: 'excepcion', value: ''},
    {id: 'R-MI-6', slot: 'explicacion', value: 'Los umbrales 1,65, 1,96 y 2,58 y el signo del valor test delimitan siete rangos disjuntos que cubren la recta (catálogo A4, 4.1; Informe Inicial).'},
    {id: 'R-MI-6', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MI-6', slot: 'decision', value: ''},
    {id: 'R-MI-7', slot: 'enunciado', value: 'V ≤ −2,58: altamente significativo, sub-representación, fuerte.'},
    {id: 'R-MI-7', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-7', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-7', slot: 'aplicabilidad', value: 'Latente'},
    {id: 'R-MI-7', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-7', slot: 'fuente', value: 'F2; F3'},
    {id: 'R-MI-7', slot: 'subprocesos', value: ['SP3']},
    {id: 'R-MI-7', slot: 'condicion', value: '{"todas": [{"campo": "valor_observado[ValorTest].valor_crisp", "op": "en_rango", "valor": "RG7"}]}'},
    {id: 'R-MI-7', slot: 'conclusion', value: '{"asigna": [{"campo": "valor_observado[ValorTest].rango_resultante", "op": "=", "valor": "RG7"}, {"campo": "par.estado", "op": "=", "valor": "E7"}]}'},
    {id: 'R-MI-7', slot: 'excepcion', value: ''},
    {id: 'R-MI-7', slot: 'explicacion', value: 'Los umbrales 1,65, 1,96 y 2,58 y el signo del valor test delimitan siete rangos disjuntos que cubren la recta (catálogo A4, 4.1; Informe Inicial).'},
    {id: 'R-MI-7', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MI-7', slot: 'decision', value: ''},
    {id: 'R-MI-8', slot: 'enunciado', value: 'Toda interpretación aclara que el valor test indica significación y no magnitud.'},
    {id: 'R-MI-8', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-8', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-8', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MI-8', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-8', slot: 'fuente', value: 'F3; F5'},
    {id: 'R-MI-8', slot: 'subprocesos', value: ['SP4']},
    {id: 'R-MI-8', slot: 'condicion', value: '{"todas": [{"campo": "par.valores[ValorTest]", "op": "presente", "valor": true}]}'},
    {id: 'R-MI-8', slot: 'conclusion', value: '{"agrega": [{"campo": "interpretacion.advertencias", "op": "+=", "valor": "AD1"}]}'},
    {id: 'R-MI-8', slot: 'excepcion', value: ''},
    {id: 'R-MI-8', slot: 'explicacion', value: 'El valor test mide la significación de la asociación, no la magnitud del fenómeno; la advertencia evita esa lectura (D5, A4).'},
    {id: 'R-MI-8', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MI-8', slot: 'decision', value: ''},
    {id: 'R-MI-9', slot: 'enunciado', value: 'El p-valor se informa exacto si es mayor o igual que 0,01 y como p < 0,01 en caso contrario.'},
    {id: 'R-MI-9', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-9', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-9', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MI-9', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-9', slot: 'fuente', value: 'F1, 5.2.2'},
    {id: 'R-MI-9', slot: 'subprocesos', value: ['SP4']},
    {id: 'R-MI-9', slot: 'condicion', value: '{"todas": [{"campo": "valor_observado[PValor].valor_crisp", "op": ">=", "valor": {"parametro": "umbral_p_exacto"}}]}'},
    {id: 'R-MI-9', slot: 'conclusion', value: '{"si": {"asigna": [{"campo": "interpretacion.p_texto", "op": "=", "valor": "p = {p_valor}"}]}, "sino": {"asigna": [{"campo": "interpretacion.p_texto", "op": "=", "valor": "p < 0,01"}]}}'},
    {id: 'R-MI-9', slot: 'excepcion', value: ''},
    {id: 'R-MI-9', slot: 'explicacion', value: 'La tesis informa el p-valor exacto cuando es mayor o igual que 0,01 y como p < 0,01 en caso contrario (F1, 5.2.2).'},
    {id: 'R-MI-9', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MI-9', slot: 'decision', value: ''},
    {id: 'R-MI-10', slot: 'enunciado', value: 'Los porcentajes se presentan como frecuencias relativas.'},
    {id: 'R-MI-10', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-10', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-10', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MI-10', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-10', slot: 'fuente', value: 'F4; F5'},
    {id: 'R-MI-10', slot: 'subprocesos', value: ['SP4']},
    {id: 'R-MI-10', slot: 'condicion', value: '{"todas": [{"campo": "interpretacion", "op": "existe", "valor": true}]}'},
    {id: 'R-MI-10', slot: 'conclusion', value: '{"asigna": [{"campo": "interpretacion.rotulo_porcentajes", "op": "=", "valor": "frecuencia relativa"}]}'},
    {id: 'R-MI-10', slot: 'excepcion', value: ''},
    {id: 'R-MI-10', slot: 'explicacion', value: 'Los porcentajes provienen de una tabla escalada: se rotulan como frecuencias relativas y no como porcentajes de observaciones.'},
    {id: 'R-MI-10', slot: 'formalizacion', value: 'Con decisión propuesta'},
    {id: 'R-MI-10', slot: 'decision', value: 'Se aplica a Cat.Class, Class.Cat y Global en toda interpretación, como indica RF-MI-6.'},
    {id: 'R-MI-11', slot: 'enunciado', value: 'Si la categoría tiene un peso muy bajo, se advierte que la asociación se apoya en pocos datos.'},
    {id: 'R-MI-11', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-11', slot: 'tipo_conocimiento', value: 'Heurística'},
    {id: 'R-MI-11', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MI-11', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-11', slot: 'fuente', value: 'Análisis del estudiante'},
    {id: 'R-MI-11', slot: 'subprocesos', value: ['SP4']},
    {id: 'R-MI-11', slot: 'condicion', value: '{"todas": [{"campo": "par.peso_bajo", "op": "=", "valor": true}]}'},
    {id: 'R-MI-11', slot: 'conclusion', value: '{"agrega": [{"campo": "interpretacion.advertencias", "op": "+=", "valor": "AD2"}]}'},
    {id: 'R-MI-11', slot: 'excepcion', value: ''},
    {id: 'R-MI-11', slot: 'explicacion', value: 'Un elemento de poco peso aporta pocos datos a la asociación; la advertencia lo hace visible al lector.'},
    {id: 'R-MI-11', slot: 'formalizacion', value: 'Con decisión propuesta'},
    {id: 'R-MI-11', slot: 'decision', value: '«Peso muy bajo» se precisa como Global < 2 %, donde Global es el peso de la línea del par. El umbral es un parámetro de la base de conocimiento.'},
    {id: 'R-MI-12', slot: 'enunciado', value: 'Dos categorías contiguas de la misma variable asociadas a una clase se interpretan como una transición.'},
    {id: 'R-MI-12', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-12', slot: 'tipo_conocimiento', value: 'Heurística'},
    {id: 'R-MI-12', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MI-12', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-12', slot: 'fuente', value: 'F1, 5.2.2 (discusión)'},
    {id: 'R-MI-12', slot: 'subprocesos', value: ['SP4']},
    {id: 'R-MI-12', slot: 'condicion', value: '{"todas": [{"campo": "par.clase", "op": "=", "valor": "par2.clase"}, {"campo": "par.categoria.variable", "op": "=", "valor": "par2.categoria.variable"}, {"campo": "abs(par.categoria.indice - par2.categoria.indice)", "op": "=", "valor": {"parametro": "distancia_contigua"}}, {"campo": "par.estado.significacion", "op": "!=", "valor": "no significativo"}, {"campo": "par2.estado.significacion", "op": "!=", "valor": "no significativo"}]}'},
    {id: 'R-MI-12', slot: 'conclusion', value: '{"asigna": [{"campo": "interpretacion.es_transicion", "op": "=", "valor": true}, {"campo": "interpretacion.contigua", "op": "=", "valor": "par2.categoria"}]}'},
    {id: 'R-MI-12', slot: 'excepcion', value: 'No se aplica a categorías sin número de orden (variables no difusas).'},
    {id: 'R-MI-12', slot: 'explicacion', value: 'Dos categorías contiguas de la misma variable describen un paso gradual de la variable y no dos hallazgos independientes (F1, 5.2.2).'},
    {id: 'R-MI-12', slot: 'formalizacion', value: 'Con decisión propuesta'},
    {id: 'R-MI-12', slot: 'decision', value: '«Contiguas» se precisa como números de orden consecutivos dentro de la misma variable.'},
    {id: 'R-MI-13', slot: 'enunciado', value: 'Si el valor test no es finito, se informa como asociación extrema con el p-valor sin transformar.'},
    {id: 'R-MI-13', slot: 'modulo', value: 'MI'},
    {id: 'R-MI-13', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MI-13', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MI-13', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MI-13', slot: 'fuente', value: 'Análisis del estudiante'},
    {id: 'R-MI-13', slot: 'subprocesos', value: ['SP2']},
    {id: 'R-MI-13', slot: 'condicion', value: '{"todas": [{"campo": "valor_observado[ValorTest].valor_crisp", "op": "no_finito", "valor": true}]}'},
    {id: 'R-MI-13', slot: 'conclusion', value: '{"asigna": [{"campo": "interpretacion.extrema", "op": "=", "valor": true}, {"campo": "interpretacion.p_texto", "op": "=", "valor": "{p_valor}"}]}'},
    {id: 'R-MI-13', slot: 'excepcion', value: 'Tiene prioridad sobre R-MI-9: el p-valor se informa sin transformar.'},
    {id: 'R-MI-13', slot: 'explicacion', value: 'Un valor test infinito indica una asociación extrema; el valor no se muestra y se informa el p-valor sin transformar.'},
    {id: 'R-MI-13', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MI-13', slot: 'decision', value: ''},
    {id: 'R-MS-1', slot: 'enunciado', value: 'La síntesis se construye sólo con interpretaciones significativas.'},
    {id: 'R-MS-1', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-1', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MS-1', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-1', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-1', slot: 'fuente', value: 'F3'},
    {id: 'R-MS-1', slot: 'subprocesos', value: ['SP5']},
    {id: 'R-MS-1', slot: 'condicion', value: '{"todas": [{"campo": "par.estado.significacion", "op": "!=", "valor": "no significativo"}]}'},
    {id: 'R-MS-1', slot: 'conclusion', value: '{"si": {"asigna": [{"campo": "interpretacion.es_significativa", "op": "=", "valor": true}]}, "sino": {"asigna": [{"campo": "interpretacion.es_significativa", "op": "=", "valor": false}]}}'},
    {id: 'R-MS-1', slot: 'excepcion', value: ''},
    {id: 'R-MS-1', slot: 'explicacion', value: 'Son significativas todas las interpretaciones salvo las clasificadas por R-MI-4, es decir, las de |V| ≥ 1,65 (RF-MS-2).'},
    {id: 'R-MS-1', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MS-1', slot: 'decision', value: ''},
    {id: 'R-MS-2', slot: 'enunciado', value: 'Las interpretaciones se agrupan por conjunto difuso.'},
    {id: 'R-MS-2', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-2', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MS-2', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-2', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-2', slot: 'fuente', value: 'F3'},
    {id: 'R-MS-2', slot: 'subprocesos', value: ['SP6']},
    {id: 'R-MS-2', slot: 'condicion', value: '{"todas": [{"campo": "interpretacion.es_significativa", "op": "=", "valor": true}]}'},
    {id: 'R-MS-2', slot: 'conclusion', value: '{"agrupa": [{"campo": "interpretacion", "op": "por", "valor": "par.categoria"}, {"campo": "grupo", "op": "es", "valor": "PatronEmergente"}]}'},
    {id: 'R-MS-2', slot: 'excepcion', value: ''},
    {id: 'R-MS-2', slot: 'explicacion', value: 'En la tabla de contingencia el conjunto difuso es la columna, es decir, la categoría del par (F3).'},
    {id: 'R-MS-2', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MS-2', slot: 'decision', value: ''},
    {id: 'R-MS-3', slot: 'enunciado', value: 'La fuerza de un patrón es la suma de los valores test absolutos que lo componen.'},
    {id: 'R-MS-3', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-3', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MS-3', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-3', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-3', slot: 'fuente', value: 'F3'},
    {id: 'R-MS-3', slot: 'subprocesos', value: ['SP7']},
    {id: 'R-MS-3', slot: 'condicion', value: '{"todas": [{"campo": "patron.interpretaciones", "op": "no_vacia", "valor": true}]}'},
    {id: 'R-MS-3', slot: 'conclusion', value: '{"asigna": [{"campo": "patron.fuerza", "op": "=", "valor": "suma(abs(valor_test))"}]}'},
    {id: 'R-MS-3', slot: 'excepcion', value: 'Si algún valor test no es finito, la fuerza del patrón es infinita.'},
    {id: 'R-MS-3', slot: 'explicacion', value: 'La fuerza resume la relevancia estadística de un conjunto difuso sumando sus valores test absolutos (F3, 5.2).'},
    {id: 'R-MS-3', slot: 'formalizacion', value: 'Con decisión propuesta'},
    {id: 'R-MS-3', slot: 'decision', value: 'Un valor infinito produce una fuerza infinita y el patrón se ordena primero.'},
    {id: 'R-MS-4', slot: 'enunciado', value: 'Los grupos y sus pares se ordenan por relevancia decreciente.'},
    {id: 'R-MS-4', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-4', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MS-4', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-4', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-4', slot: 'fuente', value: 'F2; F3'},
    {id: 'R-MS-4', slot: 'subprocesos', value: ['SP7']},
    {id: 'R-MS-4', slot: 'condicion', value: '{"todas": [{"campo": "sintesis.patrones", "op": "no_vacia", "valor": true}]}'},
    {id: 'R-MS-4', slot: 'conclusion', value: '{"ordena": [{"campo": "sintesis.patrones", "op": "por", "valor": "fuerza desc, nombre asc"}, {"campo": "patron.interpretaciones", "op": "por", "valor": "abs(valor_test) desc, clase asc"}]}'},
    {id: 'R-MS-4', slot: 'excepcion', value: ''},
    {id: 'R-MS-4', slot: 'explicacion', value: 'El orden decreciente destaca primero lo más relevante (F2, F3).'},
    {id: 'R-MS-4', slot: 'formalizacion', value: 'Con decisión propuesta'},
    {id: 'R-MS-4', slot: 'decision', value: 'Los empates se resuelven por nombre para que la misma entrada produzca siempre la misma salida (RNF-2).'},
    {id: 'R-MS-5', slot: 'enunciado', value: 'Una categoría significativa en muchas clases se informa como patrón constante.'},
    {id: 'R-MS-5', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-5', slot: 'tipo_conocimiento', value: 'Heurística'},
    {id: 'R-MS-5', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-5', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-5', slot: 'fuente', value: 'F1, 5.2.2'},
    {id: 'R-MS-5', slot: 'subprocesos', value: ['SP7']},
    {id: 'R-MS-5', slot: 'condicion', value: '{"todas": [{"campo": "exportacion.n_clases", "op": ">=", "valor": {"parametro": "minimo_clases"}}, {"campo": "patron.pertenencia_muchas", "op": ">=", "valor": {"parametro": "corte_pertenencia"}}]}'},
    {id: 'R-MS-5', slot: 'conclusion', value: '{"clasifica": [{"campo": "patron", "op": "instancia_de", "valor": "PatronConstante"}]}'},
    {id: 'R-MS-5', slot: 'excepcion', value: 'Con menos clases que el mínimo el patrón no se clasifica.'},
    {id: 'R-MS-5', slot: 'explicacion', value: 'La experta destaca como constante a la categoría que se repite en muchas clases (V3_BrisaMuyDebil en 8 de 12 meses).'},
    {id: 'R-MS-5', slot: 'formalizacion', value: 'Con decisión propuesta'},
    {id: 'R-MS-5', slot: 'decision', value: '«Muchas clases» se precisa con la etiqueta lingüística «muchas»: función trapezoidal (0,30; 0,60; 1; 1) sobre la proporción de clases.'},
    {id: 'R-MS-6', slot: 'enunciado', value: 'Una categoría significativa sólo en algunas clases se informa como singularidad.'},
    {id: 'R-MS-6', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-6', slot: 'tipo_conocimiento', value: 'Heurística'},
    {id: 'R-MS-6', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-6', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-6', slot: 'fuente', value: 'F1, 5.2.2'},
    {id: 'R-MS-6', slot: 'subprocesos', value: ['SP7']},
    {id: 'R-MS-6', slot: 'condicion', value: '{"todas": [{"campo": "exportacion.n_clases", "op": ">=", "valor": {"parametro": "minimo_clases"}}, {"campo": "patron.pertenencia_algunas", "op": ">=", "valor": {"parametro": "corte_pertenencia"}}]}'},
    {id: 'R-MS-6', slot: 'conclusion', value: '{"clasifica": [{"campo": "patron", "op": "instancia_de", "valor": "Singularidad"}]}'},
    {id: 'R-MS-6', slot: 'excepcion', value: 'Con menos clases que el mínimo el patrón no se clasifica.'},
    {id: 'R-MS-6', slot: 'explicacion', value: 'La experta destaca como singular a la categoría que aparece sólo en algunas clases (V2_Ventolina en 3 de 12 meses).'},
    {id: 'R-MS-6', slot: 'formalizacion', value: 'Con decisión propuesta'},
    {id: 'R-MS-6', slot: 'decision', value: '«Sólo algunas clases» se precisa con la etiqueta lingüística «algunas»: función trapezoidal (0; 0; 0,25; 0,50) sobre la proporción de clases.'},
    {id: 'R-MS-7', slot: 'enunciado', value: 'La síntesis tiene una estructura fija de secciones.'},
    {id: 'R-MS-7', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-7', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MS-7', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-7', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-7', slot: 'fuente', value: 'F2; F3'},
    {id: 'R-MS-7', slot: 'subprocesos', value: ['SP8']},
    {id: 'R-MS-7', slot: 'condicion', value: '{"todas": [{"campo": "sintesis", "op": "existe", "valor": true}]}'},
    {id: 'R-MS-7', slot: 'conclusion', value: '{"asigna": [{"campo": "sintesis.secciones", "op": "=", "valor": ["S1", "S2", "S3", "S4"]}]}'},
    {id: 'R-MS-7', slot: 'excepcion', value: ''},
    {id: 'R-MS-7', slot: 'explicacion', value: 'La síntesis tiene cuatro secciones fijas: tres de la propuesta y la de limitaciones que agrega el Informe Inicial (D7).'},
    {id: 'R-MS-7', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MS-7', slot: 'decision', value: ''},
    {id: 'R-MS-8', slot: 'enunciado', value: 'Las conclusiones distinguen qué diferencias son estadísticamente relevantes.'},
    {id: 'R-MS-8', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-8', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MS-8', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-8', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-8', slot: 'fuente', value: 'F2'},
    {id: 'R-MS-8', slot: 'subprocesos', value: ['SP8']},
    {id: 'R-MS-8', slot: 'condicion', value: '{"todas": [{"campo": "seccion", "op": "=", "valor": "S3"}]}'},
    {id: 'R-MS-8', slot: 'conclusion', value: '{"exige": [{"campo": "seccion.debe_incluir", "op": "contiene", "valor": "distinción entre las diferencias estadísticamente relevantes y las que no lo son"}]}'},
    {id: 'R-MS-8', slot: 'excepcion', value: ''},
    {id: 'R-MS-8', slot: 'explicacion', value: 'La conclusión debe separar lo que la estadística respalda de lo que no (F2).'},
    {id: 'R-MS-8', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MS-8', slot: 'decision', value: ''},
    {id: 'R-MS-9', slot: 'enunciado', value: 'Las asociaciones no significativas no se listan: se informan como cantidad.'},
    {id: 'R-MS-9', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-9', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MS-9', slot: 'aplicabilidad', value: 'Latente'},
    {id: 'R-MS-9', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-9', slot: 'fuente', value: 'Análisis del estudiante'},
    {id: 'R-MS-9', slot: 'subprocesos', value: ['SP5']},
    {id: 'R-MS-9', slot: 'condicion', value: '{"todas": [{"campo": "sintesis.n_no_significativas", "op": ">", "valor": 0}]}'},
    {id: 'R-MS-9', slot: 'conclusion', value: '{"asigna": [{"campo": "sintesis.cantidad_no_significativas", "op": "=", "valor": "sintesis.n_no_significativas"}]}'},
    {id: 'R-MS-9', slot: 'excepcion', value: 'Latente: la exportación actual no incluye pares no significativos.'},
    {id: 'R-MS-9', slot: 'explicacion', value: 'Las asociaciones no significativas no se listan para no saturar el texto; se informa cuántas son.'},
    {id: 'R-MS-9', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MS-9', slot: 'decision', value: ''},
    {id: 'R-MS-10', slot: 'enunciado', value: 'Las limitaciones mencionan al menos el escalado y la elección de los conjuntos difusos.'},
    {id: 'R-MS-10', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-10', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MS-10', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-10', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-10', slot: 'fuente', value: 'F1, 4.1.4; F5'},
    {id: 'R-MS-10', slot: 'subprocesos', value: ['SP8']},
    {id: 'R-MS-10', slot: 'condicion', value: '{"todas": [{"campo": "seccion", "op": "=", "valor": "S4"}]}'},
    {id: 'R-MS-10', slot: 'conclusion', value: '{"exige": [{"campo": "seccion.debe_incluir", "op": "contiene", "valor": "escalado de la tabla"}, {"campo": "seccion.debe_incluir", "op": "contiene", "valor": "elección de los conjuntos difusos"}]}'},
    {id: 'R-MS-10', slot: 'excepcion', value: ''},
    {id: 'R-MS-10', slot: 'explicacion', value: 'El escalado y la elección de los conjuntos difusos condicionan la lectura de los valores test (F1, 4.1.4; F5).'},
    {id: 'R-MS-10', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MS-10', slot: 'decision', value: ''},
    {id: 'R-MS-11', slot: 'enunciado', value: 'Cada enunciado de la síntesis debe rastrearse hasta una interpretación de MI.'},
    {id: 'R-MS-11', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-11', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MS-11', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-11', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-11', slot: 'fuente', value: 'F3; F5'},
    {id: 'R-MS-11', slot: 'subprocesos', value: ['SP9']},
    {id: 'R-MS-11', slot: 'condicion', value: '{"todas": [{"campo": "seccion.enunciados", "op": "no_vacia", "valor": true}]}'},
    {id: 'R-MS-11', slot: 'conclusion', value: '{"exige": [{"campo": "seccion.interpretaciones_usadas", "op": "no_vacia", "valor": true}]}'},
    {id: 'R-MS-11', slot: 'excepcion', value: 'Una sección sin interpretaciones de respaldo invalida la síntesis redactada.'},
    {id: 'R-MS-11', slot: 'explicacion', value: 'La trazabilidad permite controlar cada enunciado contra la interpretación que lo originó (RNF-1, RF-MS-10).'},
    {id: 'R-MS-11', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MS-11', slot: 'decision', value: ''},
    {id: 'R-MS-12', slot: 'enunciado', value: 'El modelo de lenguaje sólo redacta: no agrega asociaciones ni modifica valores.'},
    {id: 'R-MS-12', slot: 'modulo', value: 'MS'},
    {id: 'R-MS-12', slot: 'tipo_conocimiento', value: 'Determinística'},
    {id: 'R-MS-12', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-MS-12', slot: 'estado', value: 'Confirmada'},
    {id: 'R-MS-12', slot: 'fuente', value: 'F3; F5'},
    {id: 'R-MS-12', slot: 'subprocesos', value: ['SP8']},
    {id: 'R-MS-12', slot: 'condicion', value: '{"todas": [{"campo": "texto.valores_numericos", "op": "subconjunto_de", "valor": "hallazgos.valores"}]}'},
    {id: 'R-MS-12', slot: 'conclusion', value: '{"si": {"asigna": [{"campo": "sintesis.verificada", "op": "=", "valor": true}]}, "sino": {"asigna": [{"campo": "sintesis.verificada", "op": "=", "valor": false}]}}'},
    {id: 'R-MS-12', slot: 'excepcion', value: 'Si la verificación falla, el estado de redacción pasa a «estructurada» (demonio IF-CHANGED).'},
    {id: 'R-MS-12', slot: 'explicacion', value: 'El modelo de lenguaje sólo redacta: todo valor del texto debe figurar entre los hallazgos (RF-MS-8, RF-MS-9).'},
    {id: 'R-MS-12', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-MS-12', slot: 'decision', value: ''},
    {id: 'R-PU-1', slot: 'enunciado', value: 'Novato: explicaciones conceptuales, analogías simples y frecuencias relativas, sin jerga técnica.'},
    {id: 'R-PU-1', slot: 'modulo', value: 'Perfil'},
    {id: 'R-PU-1', slot: 'tipo_conocimiento', value: 'Contextual'},
    {id: 'R-PU-1', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-PU-1', slot: 'estado', value: 'Confirmada'},
    {id: 'R-PU-1', slot: 'fuente', value: 'F3, 5.3'},
    {id: 'R-PU-1', slot: 'subprocesos', value: ['SP4', 'SP8']},
    {id: 'R-PU-1', slot: 'condicion', value: '{"todas": [{"campo": "usuario.perfil", "op": "=", "valor": "novato"}]}'},
    {id: 'R-PU-1', slot: 'conclusion', value: '{"asigna": [{"campo": "configuracion_salida", "op": "=", "valor": "PerfilNovato"}, {"campo": "plantilla", "op": "=", "valor": "según regla y perfil"}]}'},
    {id: 'R-PU-1', slot: 'excepcion', value: ''},
    {id: 'R-PU-1', slot: 'explicacion', value: 'La tabla de adaptación por perfil (A5, 7.1) fija qué datos se muestran y con qué terminología; los hallazgos son los mismos para los tres perfiles (RF-PU-4).'},
    {id: 'R-PU-1', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-PU-1', slot: 'decision', value: ''},
    {id: 'R-PU-2', slot: 'enunciado', value: 'Intermedio: terminología estadística básica, valor test y contribución.'},
    {id: 'R-PU-2', slot: 'modulo', value: 'Perfil'},
    {id: 'R-PU-2', slot: 'tipo_conocimiento', value: 'Contextual'},
    {id: 'R-PU-2', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-PU-2', slot: 'estado', value: 'Confirmada'},
    {id: 'R-PU-2', slot: 'fuente', value: 'F3, 5.3'},
    {id: 'R-PU-2', slot: 'subprocesos', value: ['SP4', 'SP8']},
    {id: 'R-PU-2', slot: 'condicion', value: '{"todas": [{"campo": "usuario.perfil", "op": "=", "valor": "intermedio"}]}'},
    {id: 'R-PU-2', slot: 'conclusion', value: '{"asigna": [{"campo": "configuracion_salida", "op": "=", "valor": "PerfilIntermedio"}, {"campo": "plantilla", "op": "=", "valor": "según regla y perfil"}]}'},
    {id: 'R-PU-2', slot: 'excepcion', value: ''},
    {id: 'R-PU-2', slot: 'explicacion', value: 'La tabla de adaptación por perfil (A5, 7.1) fija qué datos se muestran y con qué terminología; los hallazgos son los mismos para los tres perfiles (RF-PU-4).'},
    {id: 'R-PU-2', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-PU-2', slot: 'decision', value: ''},
    {id: 'R-PU-3', slot: 'enunciado', value: 'Experto: formulación técnica completa.'},
    {id: 'R-PU-3', slot: 'modulo', value: 'Perfil'},
    {id: 'R-PU-3', slot: 'tipo_conocimiento', value: 'Contextual'},
    {id: 'R-PU-3', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-PU-3', slot: 'estado', value: 'Confirmada'},
    {id: 'R-PU-3', slot: 'fuente', value: 'F3, 5.3'},
    {id: 'R-PU-3', slot: 'subprocesos', value: ['SP4', 'SP8']},
    {id: 'R-PU-3', slot: 'condicion', value: '{"todas": [{"campo": "usuario.perfil", "op": "=", "valor": "experto"}]}'},
    {id: 'R-PU-3', slot: 'conclusion', value: '{"asigna": [{"campo": "configuracion_salida", "op": "=", "valor": "PerfilExperto"}, {"campo": "plantilla", "op": "=", "valor": "según regla y perfil"}]}'},
    {id: 'R-PU-3', slot: 'excepcion', value: ''},
    {id: 'R-PU-3', slot: 'explicacion', value: 'La tabla de adaptación por perfil (A5, 7.1) fija qué datos se muestran y con qué terminología; los hallazgos son los mismos para los tres perfiles (RF-PU-4).'},
    {id: 'R-PU-3', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-PU-3', slot: 'decision', value: ''},
    {id: 'R-PU-4', slot: 'enunciado', value: 'El perfil lo elige el usuario antes de solicitar la interpretación.'},
    {id: 'R-PU-4', slot: 'modulo', value: 'Perfil'},
    {id: 'R-PU-4', slot: 'tipo_conocimiento', value: 'Contextual'},
    {id: 'R-PU-4', slot: 'aplicabilidad', value: 'Activa'},
    {id: 'R-PU-4', slot: 'estado', value: 'Confirmada'},
    {id: 'R-PU-4', slot: 'fuente', value: 'Análisis del estudiante'},
    {id: 'R-PU-4', slot: 'subprocesos', value: ['SP4', 'SP8']},
    {id: 'R-PU-4', slot: 'condicion', value: '{"todas": [{"campo": "invocacion", "op": "existe", "valor": true}]}'},
    {id: 'R-PU-4', slot: 'conclusion', value: '{"asigna": [{"campo": "usuario.perfil", "op": "=", "valor": "parámetro de invocación"}]}'},
    {id: 'R-PU-4', slot: 'excepcion', value: 'Si no se indica, el perfil por defecto es intermedio (A5, firma de aida()).'},
    {id: 'R-PU-4', slot: 'explicacion', value: 'El perfil es un parámetro que se fija antes de ejecutar MI y MS (RF-PU-1).'},
    {id: 'R-PU-4', slot: 'formalizacion', value: 'Directa'},
    {id: 'R-PU-4', slot: 'decision', value: ''}
  ] AS v
MATCH (n:FrameInst {id: v.id}), (s:Slot {name: v.slot})
MERGE (n)-[h:HAS_VALUE]->(s)
SET h.value = v.value;

// ---------- 4. Referencias entre instancias (relaciones con el nombre del slot)
UNWIND [
    {de: 'RG1', a: 'ValorTest'},
    {de: 'RG2', a: 'ValorTest'},
    {de: 'RG3', a: 'ValorTest'},
    {de: 'RG4', a: 'ValorTest'},
    {de: 'RG5', a: 'ValorTest'},
    {de: 'RG6', a: 'ValorTest'},
    {de: 'RG7', a: 'ValorTest'}
  ] AS r
MATCH (a:FrameInst {id: r.de}), (b:FrameInst {id: r.a})
MERGE (a)-[:MAGNITUD]->(b);

UNWIND [
    {de: 'RG1', a: 'E1'},
    {de: 'RG2', a: 'E2'},
    {de: 'RG3', a: 'E3'},
    {de: 'RG4', a: 'E4'},
    {de: 'RG5', a: 'E5'},
    {de: 'RG6', a: 'E6'},
    {de: 'RG7', a: 'E7'}
  ] AS r
MATCH (a:FrameInst {id: r.de}), (b:FrameInst {id: r.a})
MERGE (a)-[:ESTADO_ASOCIADO]->(b);

UNWIND [
    {de: 'RG1', a: 'R-MI-1'},
    {de: 'RG2', a: 'R-MI-2'},
    {de: 'RG3', a: 'R-MI-3'},
    {de: 'RG4', a: 'R-MI-4'},
    {de: 'RG5', a: 'R-MI-5'},
    {de: 'RG6', a: 'R-MI-6'},
    {de: 'RG7', a: 'R-MI-7'},
    {de: 'AD1', a: 'R-MI-8'},
    {de: 'AD2', a: 'R-MI-11'},
    {de: 'AD3', a: 'R-MS-10'},
    {de: 'AD4', a: 'R-MS-10'},
    {de: 'AD5', a: 'R-MS-10'},
    {de: 'AD6', a: 'R-MS-10'},
    {de: 'AD7', a: 'R-MS-10'}
  ] AS r
MATCH (a:FrameInst {id: r.de}), (b:FrameInst {id: r.a})
MERGE (a)-[:REGLA]->(b);

UNWIND [
    {de: 'P-MI-1', a: 'R-MI-1'},
    {de: 'P-MI-2', a: 'R-MI-2'},
    {de: 'P-MI-3', a: 'R-MI-3'},
    {de: 'P-MI-4', a: 'R-MI-4'},
    {de: 'P-MI-5', a: 'R-MI-5'},
    {de: 'P-MI-5', a: 'R-MI-6'},
    {de: 'P-MI-5', a: 'R-MI-7'},
    {de: 'PV-1-N', a: 'R-MI-1'},
    {de: 'PV-1-I', a: 'R-MI-1'},
    {de: 'PV-1-E', a: 'R-MI-1'},
    {de: 'PV-2-N', a: 'R-MI-2'},
    {de: 'PV-2-I', a: 'R-MI-2'},
    {de: 'PV-2-E', a: 'R-MI-2'},
    {de: 'PV-3-N', a: 'R-MI-3'},
    {de: 'PV-3-I', a: 'R-MI-3'},
    {de: 'PV-3-E', a: 'R-MI-3'},
    {de: 'PV-4-N', a: 'R-MI-4'},
    {de: 'PV-4-I', a: 'R-MI-4'},
    {de: 'PV-4-E', a: 'R-MI-4'},
    {de: 'PV-5-N', a: 'R-MI-5'},
    {de: 'PV-6-N', a: 'R-MI-6'},
    {de: 'PV-7-N', a: 'R-MI-7'},
    {de: 'PV-5-I', a: 'R-MI-5'},
    {de: 'PV-5-I', a: 'R-MI-6'},
    {de: 'PV-5-I', a: 'R-MI-7'},
    {de: 'PV-5-E', a: 'R-MI-5'},
    {de: 'PV-5-E', a: 'R-MI-6'},
    {de: 'PV-5-E', a: 'R-MI-7'},
    {de: 'PT-1', a: 'R-MI-12'},
    {de: 'PT-1-N', a: 'R-MI-12'}
  ] AS r
MATCH (a:FrameInst {id: r.de}), (b:FrameInst {id: r.a})
MERGE (a)-[:REGLAS]->(b);

// ---------- 5. Reglas: frames que usan y a los que conducen
UNWIND [
    {regla: 'R-MI-1', frame: 'ValorObservado'},
    {regla: 'R-MI-1', frame: 'Rango'},
    {regla: 'R-MI-2', frame: 'ValorObservado'},
    {regla: 'R-MI-2', frame: 'Rango'},
    {regla: 'R-MI-3', frame: 'ValorObservado'},
    {regla: 'R-MI-3', frame: 'Rango'},
    {regla: 'R-MI-4', frame: 'ValorObservado'},
    {regla: 'R-MI-4', frame: 'Rango'},
    {regla: 'R-MI-5', frame: 'ValorObservado'},
    {regla: 'R-MI-5', frame: 'Rango'},
    {regla: 'R-MI-6', frame: 'ValorObservado'},
    {regla: 'R-MI-6', frame: 'Rango'},
    {regla: 'R-MI-7', frame: 'ValorObservado'},
    {regla: 'R-MI-7', frame: 'Rango'},
    {regla: 'R-MI-8', frame: 'Magnitud'},
    {regla: 'R-MI-9', frame: 'Magnitud'},
    {regla: 'R-MI-9', frame: 'ValorObservado'},
    {regla: 'R-MI-10', frame: 'Magnitud'},
    {regla: 'R-MI-10', frame: 'Exportacion'},
    {regla: 'R-MI-11', frame: 'Magnitud'},
    {regla: 'R-MI-11', frame: 'ValorObservado'},
    {regla: 'R-MI-12', frame: 'Clase'},
    {regla: 'R-MI-12', frame: 'Categoria'},
    {regla: 'R-MI-13', frame: 'Magnitud'},
    {regla: 'R-MI-13', frame: 'ValorObservado'},
    {regla: 'R-MS-1', frame: 'InterpretacionAtomica'},
    {regla: 'R-MS-1', frame: 'EstadoInterpretado'},
    {regla: 'R-MS-2', frame: 'InterpretacionAtomica'},
    {regla: 'R-MS-2', frame: 'ConjuntoDifuso'},
    {regla: 'R-MS-3', frame: 'Magnitud'},
    {regla: 'R-MS-3', frame: 'ValorObservado'},
    {regla: 'R-MS-4', frame: 'PatronEmergente'},
    {regla: 'R-MS-4', frame: 'ValorObservado'},
    {regla: 'R-MS-5', frame: 'Categoria'},
    {regla: 'R-MS-5', frame: 'Clase'},
    {regla: 'R-MS-6', frame: 'Categoria'},
    {regla: 'R-MS-6', frame: 'Clase'},
    {regla: 'R-MS-7', frame: 'Sintesis'},
    {regla: 'R-MS-8', frame: 'EstadoInterpretado'},
    {regla: 'R-MS-9', frame: 'EstadoInterpretado'},
    {regla: 'R-MS-10', frame: 'Exportacion'},
    {regla: 'R-MS-10', frame: 'ConjuntoDifuso'},
    {regla: 'R-MS-11', frame: 'InterpretacionAtomica'},
    {regla: 'R-MS-12', frame: 'InterpretacionAtomica'},
    {regla: 'R-MS-12', frame: 'ValorObservado'},
    {regla: 'R-PU-1', frame: 'PerfilNovato'},
    {regla: 'R-PU-1', frame: 'Magnitud'},
    {regla: 'R-PU-2', frame: 'PerfilIntermedio'},
    {regla: 'R-PU-2', frame: 'Magnitud'},
    {regla: 'R-PU-3', frame: 'PerfilExperto'},
    {regla: 'R-PU-3', frame: 'Magnitud'},
    {regla: 'R-PU-4', frame: 'Usuario'},
    {regla: 'R-PU-4', frame: 'PerfilDeUsuario'}
  ] AS r
MATCH (a:FrameInst {id: r.regla}), (b:FrameClass {name: r.frame})
MERGE (a)-[:USA]->(b);

UNWIND [
    {regla: 'R-MI-1', frame: 'EstadoInterpretado'},
    {regla: 'R-MI-2', frame: 'EstadoInterpretado'},
    {regla: 'R-MI-3', frame: 'EstadoInterpretado'},
    {regla: 'R-MI-4', frame: 'EstadoInterpretado'},
    {regla: 'R-MI-5', frame: 'EstadoInterpretado'},
    {regla: 'R-MI-6', frame: 'EstadoInterpretado'},
    {regla: 'R-MI-7', frame: 'EstadoInterpretado'},
    {regla: 'R-MI-8', frame: 'AdvertenciaMetodologica'},
    {regla: 'R-MI-9', frame: 'InterpretacionAtomica'},
    {regla: 'R-MI-10', frame: 'InterpretacionAtomica'},
    {regla: 'R-MI-11', frame: 'AdvertenciaMetodologica'},
    {regla: 'R-MI-12', frame: 'InterpretacionAtomica'},
    {regla: 'R-MI-13', frame: 'InterpretacionAtomica'},
    {regla: 'R-MS-1', frame: 'Sintesis'},
    {regla: 'R-MS-2', frame: 'PatronEmergente'},
    {regla: 'R-MS-3', frame: 'PatronEmergente'},
    {regla: 'R-MS-4', frame: 'PatronEmergente'},
    {regla: 'R-MS-5', frame: 'PatronConstante'},
    {regla: 'R-MS-6', frame: 'Singularidad'},
    {regla: 'R-MS-7', frame: 'SeccionDeLaSintesis'},
    {regla: 'R-MS-8', frame: 'SeccionDeLaSintesis'},
    {regla: 'R-MS-9', frame: 'Sintesis'},
    {regla: 'R-MS-10', frame: 'SeccionDeLaSintesis'},
    {regla: 'R-MS-11', frame: 'Sintesis'},
    {regla: 'R-MS-12', frame: 'Sintesis'},
    {regla: 'R-PU-1', frame: 'InterpretacionAtomica'},
    {regla: 'R-PU-1', frame: 'Sintesis'},
    {regla: 'R-PU-2', frame: 'InterpretacionAtomica'},
    {regla: 'R-PU-2', frame: 'Sintesis'},
    {regla: 'R-PU-3', frame: 'InterpretacionAtomica'},
    {regla: 'R-PU-3', frame: 'Sintesis'},
    {regla: 'R-PU-4', frame: 'InterpretacionAtomica'},
    {regla: 'R-PU-4', frame: 'Sintesis'}
  ] AS r
MATCH (a:FrameInst {id: r.regla}), (b:FrameClass {name: r.frame})
MERGE (a)-[:CONDUCE_A]->(b);

// ---------- 6. Enlaces con el modelo conceptual (A7)
// Cada concepto de A7 se vincula con el frame, el slot, la instancia o el valor que lo formaliza.
UNWIND [
    {concepto: 'ConjuntoDifuso', nombre: 'ConjuntoDifuso', como: 'frame'},
    {concepto: 'Clase', nombre: 'Clase', como: 'frame'},
    {concepto: 'Categoria', nombre: 'Categoria', como: 'frame'},
    {concepto: 'Exportacion', nombre: 'Exportacion', como: 'frame'},
    {concepto: 'TipoDeDescripcion', nombre: 'Exportacion', como: 'especialización'},
    {concepto: 'DescripcionDeFilas', nombre: 'DescripcionDeFilas', como: 'frame'},
    {concepto: 'DescripcionDeColumnas', nombre: 'DescripcionDeColumnas', como: 'frame'},
    {concepto: 'DescripcionDeGrupos', nombre: 'DescripcionDeGrupos', como: 'frame'},
    {concepto: 'ParDeAsociacion', nombre: 'ParDeAsociacion', como: 'frame'},
    {concepto: 'Magnitud', nombre: 'Magnitud', como: 'frame'},
    {concepto: 'ValorObservado', nombre: 'ValorObservado', como: 'frame'},
    {concepto: 'Rango', nombre: 'Rango', como: 'frame'},
    {concepto: 'EstadoInterpretado', nombre: 'EstadoInterpretado', como: 'frame'},
    {concepto: 'Regla', nombre: 'Regla', como: 'frame'},
    {concepto: 'InterpretacionAtomica', nombre: 'InterpretacionAtomica', como: 'frame'},
    {concepto: 'Plantilla', nombre: 'Plantilla', como: 'frame'},
    {concepto: 'AdvertenciaMetodologica', nombre: 'AdvertenciaMetodologica', como: 'frame'},
    {concepto: 'PatronEmergente', nombre: 'PatronEmergente', como: 'frame'},
    {concepto: 'PatronConstante', nombre: 'PatronConstante', como: 'frame'},
    {concepto: 'Singularidad', nombre: 'Singularidad', como: 'frame'},
    {concepto: 'Sintesis', nombre: 'Sintesis', como: 'frame'},
    {concepto: 'SeccionDeLaSintesis', nombre: 'SeccionDeLaSintesis', como: 'frame'},
    {concepto: 'Usuario', nombre: 'Usuario', como: 'frame'},
    {concepto: 'PerfilDeUsuario', nombre: 'PerfilDeUsuario', como: 'frame'},
    {concepto: 'PerfilNovato', nombre: 'PerfilNovato', como: 'frame'},
    {concepto: 'PerfilIntermedio', nombre: 'PerfilIntermedio', como: 'frame'},
    {concepto: 'PerfilExperto', nombre: 'PerfilExperto', como: 'frame'}
  ] AS x
MATCH (f:FrameClass {name: x.nombre}), (c:Concepto {id: x.concepto})
MERGE (f)-[r:FORMALIZA]->(c) SET r.como = x.como;

UNWIND [
    {concepto: 'EscaladoLineal', slot: 'escalado_lineal', como: 'slot'},
    {concepto: 'GrupoDeFilas', slot: 'origen', como: 'valor'},
    {concepto: 'Significacion', slot: 'significacion', como: 'slot'},
    {concepto: 'Direccion', slot: 'direccion', como: 'slot'},
    {concepto: 'SobreRepresentacion', slot: 'direccion', como: 'valor'},
    {concepto: 'SubRepresentacion', slot: 'direccion', como: 'valor'},
    {concepto: 'IntensidadRelativa', slot: 'intensidad', como: 'slot'},
    {concepto: 'FuerzaDelPatron', slot: 'fuerza', como: 'slot'},
    {concepto: 'GradoDePertenencia', slot: 'pertenencia_algunas', como: 'slot'},
    {concepto: 'GradoDePertenencia', slot: 'pertenencia_muchas', como: 'slot'},
    {concepto: 'FuncionDePertenencia', slot: 'funcion_pertenencia', como: 'slot'},
    {concepto: 'FuncionDePertenencia', slot: 'parametros', como: 'slot'}
  ] AS x
MATCH (s:Slot {name: x.slot}), (c:Concepto {id: x.concepto})
MERGE (s)-[r:FORMALIZA]->(c) SET r.como = x.como;

UNWIND [
    {concepto: 'ValorTest', id: 'ValorTest'},
    {concepto: 'PValor', id: 'PValor'},
    {concepto: 'CatClass', id: 'CatClass'},
    {concepto: 'ClassCat', id: 'ClassCat'},
    {concepto: 'Global', id: 'Global'},
    {concepto: 'Weight', id: 'Weight'}
  ] AS x
MATCH (i:FrameInst {id: x.id}), (c:Concepto {id: x.concepto})
MERGE (i)-[r:FORMALIZA]->(c) SET r.como = 'instancia';

MATCH (i:FrameInst)-[:INSTANCE_OF]->(:FrameClass {name: 'Regla'}), (r:Regla {id: i.id})
MERGE (i)-[:FORMALIZA]->(r);
