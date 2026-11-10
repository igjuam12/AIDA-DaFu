"""AIDA · Módulo de Síntesis de Resultados, parte en Python (RF-MS-6 a RF-MS-11).

Lee hallazgos.json (escrito por la parte en R), arma el prompt con Jinja2,
obtiene la redacción del modelo de lenguaje (llm.py), verifica los valores
numéricos del texto (R-MS-12) y escribe sintesis.json. La sección de limitaciones
se arma con los textos de la base de conocimiento, sin pasar por el modelo (R-MS-10).
"""
import datetime
import functools
import importlib.util
import json
import math
import os
import re

from jinja2 import Environment, FileSystemLoader

DIR = os.path.dirname(os.path.abspath(__file__))


def _cargar_llm():
    """Carga llm.py de esta carpeta por su ruta, para no chocar con otro módulo llamado «llm»."""
    spec = importlib.util.spec_from_file_location("aida_llm", os.path.join(DIR, "llm.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


llm = _cargar_llm()
TIPOS = {"filas": "descripción de filas", "columnas": "descripción de columnas", "grupos": "descripción de grupos"}
# Umbrales del método que el texto puede citar aunque no sean valores de los hallazgos.
CONSTANTES = ["1,65", "1,96", "2,58", "0,01"]
# El nombre del archivo no sale del equipo: el modelo recibe este marcador y se reemplaza al recibir el texto.
MARCADOR_ARCHIVO = "ARCHIVO_ANALIZADO"
NO_NUMEROS = ("NA", "no calculable", "infinito", "menos infinito")


def num(x, d):
    """Número con coma decimal y d decimales, como en la parte en R."""
    if x is None or isinstance(x, str):          # R escribe NA, NaN e Inf como null
        return "no calculable"
    r = round(x + math.copysign(1e-9, x), d) if x else 0.0
    return f"{r if r else 0.0:.{d}f}".replace(".", ",")   # sin «-0,00»


# Plantilla del prompt: el «Prompt Estructurado» del modelado académico de AIDA (sección 5.3), con los datos de MI.
PLANTILLA = "prompt_aida.j2"
# Tope del prompt: no depende de cuántos datos entren. Al modelo sólo se le detallan los MAX_GRUPOS conjuntos de mayor
# relevancia y, en total, unas MAX_DETALLE asociaciones (las de mayor valor test de cada conjunto, con un mínimo de MIN_POR_GRUPO);
# el resto se resume con cantidades calculadas por código (_resumen_otros_grupos) y se informa que no se detalla.
MAX_GRUPOS = 8
MAX_DETALLE = 40
MIN_POR_GRUPO = 3
MAX_FAMILIAS, MAX_PASOS = 10, 8
MAX_TRANSICIONES = 20
MAX_NOMBRES = 6          # conjuntos que se nombran por cada clase que se repite
# Secciones que redacta el modelo; S4 (limitaciones) sale de la base de conocimiento (R-MS-10).
SECCIONES = ("S1", "S2", "S3")
# Comienzo de cada párrafo de S2, como en el ejemplo del modelado («Hallazgos para el grupo de Ingresos Altos: …»).
_INICIO_GRUPO = re.compile(r"Hallazgos\s+para\s+el\s+(?:grupo|conjunto)\b", re.IGNORECASE)

# Palabras del ejemplo de estilo del prompt (transporte e ingresos): si aparecen en un texto, el modelo copió el ejemplo.
EJEMPLO_DEL_PROMPT = r"\b(?:transporte|bicicleta|motocicleta|autom[oó]vil|auto\s+privado|ingresos|movilidad|motorizad[oa]s?|poder\s+adquisitivo)"

# Afirmaciones que el archivo no permite hacer cuando no trae asociaciones no significativas: (expresión, motivo).
AFIRMACIONES_SIN_RESPALDO = [
    # «Las demás combinaciones posibles no figuran en el archivo» es correcto: sólo cuenta «asociaciones posibles».
    (r"asociaci\w+\s+posibles\b|\bposibles\s+asociaci\w+", "llama «posibles» a las asociaciones listadas"),
    (r"\btodas\s+las\s+asociaciones\b[^.;]*\bsignificativas\b", "afirma que todas las asociaciones son significativas"),
    (r"\b(?:sin|no)\b[^.;]*\basociaci\w+\b[^.;]*\bno\s+(?:lo\s+sean|lo\s+son|significativ\w+)", "afirma que no hay asociaciones no significativas"),
    (r"\bsignificativas\s+de\s+(?:un\s+total\s+de\s+\w+|\d+)", "presenta las asociaciones listadas como parte de un total conocido"),
    (r"\b(?:las|aquellas)\s+que\s+no\s+(?:lo\s+son|alcanzan)\b", "distingue asociaciones que el archivo no contiene"),
]


# Oraciones sin cifras que dicen algo que los datos no dan (jerga del método, orden temporal, crecimiento, adjetivos inventados).
JERGA_NO_RESPALDADA = re.compile(
    r"n[uú]meros?\s+m[aá]s\s+(?:alto|bajo)|expansi[oó]n|crecimiento|evoluci[oó]n"
    r"|primera\s+fecha|[uú]ltima\s+fecha|fecha\s+(?:inicial|final)|medici[oó]n\s+inicial|intermedi\w+\s+(?:altos|bajos|avanzad\w+|superior\w*)"
    r"|secundari|exclusiv", re.IGNORECASE)
# El tipo de patrón sólo se nombra si no todos los conjuntos tienen el mismo: «los 5 conjuntos son singularidades» no informa nada.
JERGA_DE_TIPOS = re.compile(r"singular(?:es|idad(?:es)?)?\b|patr[oó]n(?:es)?\s+(?:constantes?|de\s+tipo)", re.IGNORECASE)


def _podar(texto, nombres=(), con_tipos=False):
    """Normaliza los corchetes del desglose a paréntesis y quita las oraciones sin cifras que dicen algo que los datos no dan
    (ver JERGA_NO_RESPALDADA y, si todos los conjuntos tienen el mismo tipo de patrón, JERGA_DE_TIPOS). Con cifras, la oración
    se conserva: la deciden los demás controles. Los nombres de clases y conjuntos no cuentan ni como cifras («F3») ni como
    jerga (una clase puede llamarse «Crecimiento»). Nunca vacía el texto."""
    texto = re.sub(r"\[([^\[\]]*,[^\[\]]*)\]", r"(\1)", texto)
    presentes = {n for n in nombres if n and n in texto}          # con muchas clases, sólo se buscan las que el texto nombra
    frases = re.split(r"(?<=[.!?])[ \t]+", texto)

    def sobra(frase):
        f = _sin_nombres(frase, presentes) if presentes else frase
        if re.search(r"\d", f):
            return False
        return bool(JERGA_NO_RESPALDADA.search(f) or (not con_tipos and JERGA_DE_TIPOS.search(f)))
    quedan = [f for f in frases if not sobra(f)]
    return " ".join(quedan) if quedan else texto


# Durante una redacción los hallazgos no cambian: lo que se lee de ellos (nombres, lectura cruzada, clases repetidas) se
# calcula una sola vez, aunque lo pidan los controles de cada párrafo. Fuera de redactar_sintesis() no se guarda nada.
_MEMO = None


def _una_vez(f):
    @functools.wraps(f)
    def envoltura(h, *args):
        if _MEMO is None:
            return f(h, *args)
        clave = (f.__name__, id(h)) + args
        if clave not in _MEMO:
            _MEMO[clave] = f(h, *args)
        return _MEMO[clave]
    return envoltura


@_una_vez
def clases_recurrentes(h, limite=6):
    """Clases que se asocian con más de un conjunto: [(clase, [conjuntos legibles])], de mayor a menor recurrencia."""
    por_clase = {}
    for g in h["grupos"]:
        for p in g["pares"]:
            por_clase.setdefault(p["clase"], []).append(g.get("conjunto_legible") or g["conjunto"])
    r = [(c, list(dict.fromkeys(cs))) for c, cs in por_clase.items()]
    r = [x for x in r if len(x[1]) >= 2]
    return sorted(r, key=lambda x: -len(x[1]))[:limite]


def _es_numerico(nombre):
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", str(nombre or "")))


def _clase_txt(clase):
    """Nombre de la clase en el prompt: si es sólo un número, «clase N», para no confundirlo con una cifra."""
    return f"clase {clase}" if _es_numerico(clase) else clase


def _familias(h):
    """Lectura cruzada de las clases: las que comparten el nombre salvo el último componente («E47_F1», «E47_F2», «E47_F3»)
    forman una familia, y de cada clase se informa el conjunto con el que más se asocia (el de mayor valor test).
    Sólo hay familias si todas las clases tienen nombre compuesto; el orden es el de los nombres."""
    mejor = _mejor_conjunto(h)
    if not mejor or any(_es_numerico(c) or "_" not in c for c in mejor):
        return []
    por_base = {}
    for c in sorted(mejor):
        por_base.setdefault(c.rsplit("_", 1)[0], []).append(c)
    familias = [dict(base=b, pasos=[dict(clase=c, conjunto=mejor[c][1]) for c in cs[:MAX_PASOS]]) for b, cs in por_base.items() if len(cs) >= 2]
    return familias[:MAX_FAMILIAS]


def _variables(h):
    """Nombres de las variables de agrupación (por ejemplo, Cepa, Fecha), si el usuario los indicó."""
    return _lista(h.get("variables"))


def _lista(v):
    """Un vector de un solo elemento viaja desde R como escalar: aquí vuelve a ser lista."""
    return [] if v is None else (list(v) if isinstance(v, (list, tuple)) else [v])


@_una_vez
def _clases_compuestas(h):
    """(clases, cantidad de componentes) si todas las clases tienen nombre compuesto con la misma cantidad de partes
    separadas por «_» (como las de una descripción de grupos: «E47_F2»); si no, None."""
    clases = {p["clase"] for g in h["grupos"] for p in g["pares"]}
    if not clases or any(_es_numerico(c) or "_" not in c for c in clases):
        return None
    n = {len(c.split("_")) for c in clases}
    if len(n) != 1:
        return None
    k, variables = n.pop(), _variables(h)
    # Si se conocen las variables y no son tantas como las partes del nombre, algún valor trae «_» adentro («E_47_F1»):
    # partir el nombre por «_» daría una lectura falsa, así que no se hace.
    return None if (variables and len(variables) != k) else (clases, k)


def _desglose(clase, variables):
    """«cepa E47, fecha F3» para la clase «E47_F3», si se conocen los nombres de las variables y coinciden en cantidad."""
    partes = clase.split("_")
    # Con una sola variable la clase ya es su valor: «E47BIS (tratamiento E47BIS)» no agrega nada.
    if not variables or len(variables) < 2 or len(variables) != len(partes) or _es_numerico(clase):
        return ""
    return ", ".join(f"{v.lower()} {p}" for v, p in zip(variables, partes))


# Nombre de un conjunto difuso: «Are3_20.9a31.4_» (como lo escribe DaFu) o «CO4.9.5a10.5.» (igual, con puntos en lugar de guiones
# bajos, como llega de algunos CSV; ahí sólo vale si el resto es un rango completo).
_NUM = r"-?\d+(?:\.\d+)?"
_CONJUNTO = re.compile(r"^([A-Za-z]+)(\d+)(?:_|\." + _NUM + "a" + _NUM + r"\.$)")
_RANGO_CONJUNTO = re.compile(r"^[A-Za-z]+\d+[_.](" + _NUM + ")a(" + _NUM + r")[_.]$")


def _indice_conjunto(nombre):
    m = _CONJUNTO.match(nombre)
    return int(m.group(2)) if m else None


def _variable_conjunto(nombre):
    """Variable difusa de un conjunto («Are» en «Are3_20.9a31.4_»), o None si el nombre no tiene esa forma."""
    m = _CONJUNTO.match(nombre)
    return m.group(1) if m else None


def _nombre_corto(conjunto):
    """«Are3» para «Are3_20.9a31.4_» y «CO4» para «CO4.9.5a10.5.»; si el nombre no es de un conjunto difuso, lo que hay antes del primer «_»."""
    m = _CONJUNTO.match(conjunto)
    return m.group(1) + m.group(2) if m else conjunto.split("_")[0]


def _orden_natural(s):
    """Clave para ordenar «F2» antes que «F10»."""
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", str(s))]


def _plural(palabra):
    w = palabra.lower()
    return w + ("s" if w[-1] in "aeiouáéíóú" else "es")


@_una_vez
def _comunes(h, k):
    """Qué tienen en común las clases de cada uno de los primeros k conjuntos, en palabras llanas: por cada componente del
    nombre de la clase, el nivel que todas comparten (y si son todas las clases de ese nivel que hay en el análisis) o los
    niveles que reúnen. Con los nombres de las variables dice «Fecha: todas las clases tienen fecha F1»; sin ellos, «todas las
    clases terminan en F1»."""
    info = _clases_compuestas(h)
    if not info:
        return [], set()
    clases, n = info
    vars_ = _variables(h)
    con_nombres = len(vars_) == n
    totales = [{} for _ in range(n)]
    for c in clases:
        for i, x in enumerate(c.split("_")):
            totales[i][x] = totales[i].get(x, 0) + 1
    salida, numeros = [], set()
    for g in h["grupos"][:k]:
        cs = {p["clase"] for p in g["pares"]}
        if len(cs) < 2:
            continue
        lineas = []
        for i in range(n):
            cuenta = {}
            for c in cs:
                x = c.split("_")[i]
                cuenta[x] = cuenta.get(x, 0) + 1
            if len(cuenta) == 1:
                (x, _), = cuenta.items()
                tot = totales[i][x]
                cobertura = (f"son las {len(cs)} que hay con {x} en el análisis" if tot == len(cs)
                             else f"son {len(cs)} de las {tot} que hay con {x} en el análisis")
                numeros.update([str(len(cs)), str(tot)])
                if con_nombres:
                    lineas.append(f"{vars_[i]}: todas las clases tienen {vars_[i].lower()} {x} ({cobertura})")
                elif i == 0:
                    lineas.append(f"todas las clases empiezan con {x} ({cobertura})")
                elif i == n - 1:
                    lineas.append(f"todas las clases terminan en {x} ({cobertura})")
                else:
                    lineas.append(f"todas las clases tienen {x} en la parte {i + 1} de su nombre ({cobertura})")
            else:
                orden = sorted(cuenta.items(), key=lambda kv: (-kv[1], kv[0]))
                lista = ", ".join(f"{x} ({m})" for x, m in orden[:6]) + (f" y {len(orden) - 6} más" if len(orden) > 6 else "")
                numeros.update(str(m) for _, m in orden[:6]); numeros.add(str(len(orden)))
                if con_nombres:
                    lineas.append(f"{vars_[i]}: hay clases con {vars_[i].lower()} {lista}")
                elif i == 0:
                    lineas.append(f"las clases empiezan con {lista}")
                elif i == n - 1:
                    lineas.append(f"las clases terminan en {lista}")
                else:
                    lineas.append(f"en la parte {i + 1} del nombre hay clases con {lista}")
        salida.append(dict(conjunto=g.get("conjunto_legible") or g["conjunto"], lineas=lineas))
    return salida, numeros


def _comparacion(h):
    """Comparación entre familias en cada nivel del último componente («F1», «F2», «F3»): con qué conjunto se asocia cada familia
    («E47», «ECO», «FLO») y cuál es el conjunto de número más alto. Es la lectura que hace la experta en la conclusión
    («en F2 y en F3, E47 se asocia con la categoría más alta, FLO con la más baja»)."""
    info = _clases_compuestas(h)
    if not info or info[1] < 2:
        return []
    mejor = _mejor_conjunto(h)
    vars_ = _variables(h)
    nombrado = len(vars_) == info[1]
    fam = _plural(vars_[0]) if (nombrado and info[1] == 2) else "familias"
    etiqueta = (lambda nv: f"{vars_[-1]} {nv}") if nombrado else (lambda nv: nv)
    niveles = {}
    for c, (_, nombre, idx, var) in mejor.items():
        base, nivel = c.rsplit("_", 1)
        niveles.setdefault(nivel, []).append((base, nombre, idx, var))
    salida, divergentes = [], []
    for nivel in sorted(niveles, key=_orden_natural)[:MAX_FAMILIAS]:
        items = sorted(niveles[nivel], key=lambda t: (-(t[2] if t[2] is not None else -1), t[0]))
        if len(items) < 2:
            continue
        # «Are3 es de valores más altos que Are2» sólo vale entre conjuntos de la misma variable difusa.
        comparable = (len({t[3] for t in items}) == 1 and items[0][2] is not None and items[-1][2] is not None
                      and items[0][2] != items[-1][2])
        conjuntos = {t[1] for t in items}
        if len(conjuntos) == 1:
            salida.append(f"{etiqueta(nivel)}: las {len(items)} {fam} ({', '.join(t[0] for t in items[:MAX_PASOS])}) se asocian sobre todo con {items[0][1]}")
            continue
        por_conjunto = {}
        for base, nombre, _idx, _var in items[:MAX_PASOS * 2]:
            por_conjunto.setdefault(nombre, []).append(base)
        partes = [f"{' y '.join(b) if len(b) < 3 else ', '.join(b[:-1]) + ' y ' + b[-1]} se {'asocian' if len(b) > 1 else 'asocia'} sobre todo con {n}"
                  for n, b in por_conjunto.items()]
        texto = "; ".join(partes)
        if comparable:
            texto += f". {items[0][1]} es un conjunto de valores más altos que {items[-1][1]}"
        salida.append(f"{etiqueta(nivel)}: {texto}")
        if comparable:
            altos = [t[0] for t in items if t[2] == items[0][2]]
            divergentes.append((nivel, altos, sorted(t[0] for t in items if t[2] != items[0][2])))
    # Conclusión de conjunto: la misma familia queda siempre en el conjunto más alto, y las demás van juntas.
    # Sólo con dos variables: con tres o más, «la familia» es ya una combinación («E47_F3») y la línea no dice nada útil
    # («E47_F3 se asocia con valores más altos que todas las demás»).
    if info[1] == 2 and len(divergentes) >= 1 and len({tuple(d[1]) for d in divergentes}) == 1 and len({tuple(d[2]) for d in divergentes}) == 1:
        altos, resto = divergentes[0][1], divergentes[0][2]
        niveles_div = [d[0] for d in divergentes]
        union = lambda xs: xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]
        if nombrado and info[1] == 2:      # con los nombres de las variables, sin depender de su género: «las de cepa E47»
            salida.append(f"En conjunto: en las clases con {vars_[-1].lower()} {union(niveles_div)}, las de {vars_[0].lower()} {union(altos)} "
                          f"tienen siempre su asociación principal en un conjunto de valores más altos que las de {vars_[0].lower()} {union(resto)}")
        else:
            salida.append(f"En conjunto: en {union(niveles_div)}, {union(altos)} {'tiene' if len(altos) == 1 else 'tienen'} "
                          f"siempre su asociación principal en un conjunto de valores más altos que {union(resto)}")
    return salida


def _union(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


@_una_vez
def _afines(h):
    """Lectura cruzada cuando las clases no tienen nombre compuesto (una sola variable, o filas sueltas): qué clases se asocian
    con los mismos conjuntos y cuáles con conjuntos en los que no figura ninguna otra. Es lo que _comparacion() no puede dar
    sin familias y niveles. Devuelve (líneas, cantidades que aparecen en ellas)."""
    de_clase, de_conjunto = {}, {}
    for g in h["grupos"]:
        n = g.get("conjunto_legible") or g["conjunto"]
        for p in g["pares"]:
            de_clase.setdefault(p["clase"], set()).add(n)
            de_conjunto.setdefault(n, set()).add(p["clase"])
    if len(de_clase) < 2 or len(de_conjunto) < 2:
        return [], set()
    por_perfil = {}
    for c, cs in de_clase.items():
        por_perfil.setdefault(tuple(sorted(cs, key=_orden_natural)), []).append(c)
    lineas, numeros = [], set()
    orden = sorted(por_perfil.items(), key=lambda kv: (-len(kv[1]), _orden_natural(min(kv[1]))))
    con_varios = [cs for cs in por_perfil if len(cs) > 1]
    solo_ellas = len(con_varios) == 1 and len(por_perfil) > 1
    for conjuntos, clases in orden[:MAX_FAMILIAS]:
        clases = sorted(clases, key=_orden_natural)
        nombres = [_clase_txt(c) for c in clases[:MAX_PASOS]]
        if len(clases) > MAX_PASOS:
            nombres.append(f"{len(clases) - MAX_PASOS} más")
            numeros.add(str(len(clases) - MAX_PASOS))
        lista = _union(conjuntos[:MAX_NOMBRES]) + (f" y otros {len(conjuntos) - MAX_NOMBRES}" if len(conjuntos) > MAX_NOMBRES else "")
        if len(conjuntos) > MAX_NOMBRES:
            numeros.add(str(len(conjuntos) - MAX_NOMBRES))
        uno = len(conjuntos) == 1
        if len(clases) > 1:
            texto = f"{_union(nombres)} se asocian con {'el mismo conjunto' if uno else 'los mismos conjuntos'}: {lista}"
        else:
            texto = f"{nombres[0]} se asocia con {lista}"
        if all(de_conjunto[n] == set(clases) for n in conjuntos):      # sólo vale para lo que el archivo informa
            texto += f"; en el archivo, ninguna otra clase figura asociada con {'ese conjunto' if uno else 'esos conjuntos'}"
        if solo_ellas and not uno:
            texto += "; a diferencia de las demás clases, que se asocian con un solo conjunto"
        lineas.append(texto)
    return lineas, numeros


@_una_vez
def _mejor_conjunto(h):
    """Para cada clase, (valor test, conjunto legible, número de orden del conjunto, variable difusa) del conjunto con el que
    más se asocia."""
    mejor = {}
    for g in h["grupos"]:
        idx, var = _indice_conjunto(g["conjunto"]), _variable_conjunto(g["conjunto"])
        for p in g["pares"]:
            v = p["valor_test"] if isinstance(p.get("valor_test"), (int, float)) else float("-inf")
            if p["clase"] not in mejor or v > mejor[p["clase"]][0]:
                mejor[p["clase"]] = (v, g.get("conjunto_legible") or g["conjunto"], idx, var)
    return mejor


def _variables_txt(h):
    info, v = _clases_compuestas(h), _variables(h)
    return " y ".join(v) if info and v and len(v) == info[1] else ""


def _ejemplo_desglose(h):
    info = _clases_compuestas(h)
    if not info or not _variables_txt(h):
        return ""
    c = sorted(info[0])[0]
    return f"«{c}» es {_desglose(c, _variables(h))}"


def _ejemplo_palabras(h):
    """«cepa E47, fecha F3»: la primera clase compuesta, nombrada con sus variables (vacío si no se conocen)."""
    info = _clases_compuestas(h)
    return _desglose(sorted(info[0])[0], _variables(h)) if info and _variables_txt(h) else ""


def _ejemplo_fin(h):
    """Último componente de la primera clase compuesta («F3» en «E47_F3»), para el ejemplo cuando no se conocen las variables."""
    info = _clases_compuestas(h)
    return sorted(info[0])[0].split("_")[-1] if info else ""


def _posicion(g, h):
    """Dónde cae el conjunto entre los del análisis, en palabras (sin cifras): «el de valores más bajos», «el de valores
    más altos» o «de valores intermedios». Sólo si el nombre trae el número de orden («Are1»)."""
    idx, var = _indice_conjunto(g["conjunto"]), _variable_conjunto(g["conjunto"])
    if idx is None:
        return ""
    # La tabla puede tener conjuntos sin ninguna asociación, que el archivo no trae: si se conoce la lista completa
    # (`conjuntos_tabla`, la manda la aplicación), se usa; si no, «el más alto» sólo se afirma entre los que figuran.
    completos = _lista(h.get("conjuntos_tabla"))
    nombres = completos or [o["conjunto"] for o in h["grupos"]]
    indices = sorted({_indice_conjunto(n) for n in nombres if _variable_conjunto(n) == var} - {None})
    if len(indices) < 3 or idx not in indices:
        return ""
    if idx == indices[0]:
        return "el de valores más bajos" if (completos or idx == 1) else "el de valores más bajos entre los conjuntos que figuran en el archivo"
    if idx == indices[-1]:
        return "el de valores más altos" if completos else "el de valores más altos entre los conjuntos que figuran en el archivo"
    return "de valores intermedios"


@_una_vez
def _componentes(h):
    """Componentes de los nombres de clase compuestos («E47», «F1» en «E47_F1»): no son datos numéricos."""
    return {x for g in h["grupos"] for p in g["pares"] if not _es_numerico(p["clase"]) for x in p["clase"].split("_") if x}


def _tipo_asociacion(p, llana=None):
    """«Sobre-representación fuerte», como en la lista de patrones del modelado. Dirección e intensidad salen de la
    base de conocimiento (estados de R-MI-1 a R-MI-7); si no vienen, se usa el nivel de significación. Para el perfil que
    no usa jerga, `llana` da la misma idea en palabras comunes («Aparece mucho más de lo esperable»)."""
    frase = ((llana or {}).get(p.get("direccion")) or {}).get(p.get("intensidad"))
    if frase:
        return "Aparece " + frase
    if p.get("direccion"):
        return f"{p['direccion']} {p.get('intensidad') or ''}".strip().capitalize()
    return str(p["significacion"]).capitalize()


_PERFILES_KB = {}


def _perfil_kb(perfil, ruta=None):
    """Perfil de la base de conocimiento (guía de redacción y ejemplo de estilo), por si los hallazgos no los traen."""
    ruta = ruta or os.path.join(DIR, "..", "kb", "base_conocimiento.json")
    if ruta not in _PERFILES_KB:
        try:
            with open(ruta, encoding="utf-8") as f:
                _PERFILES_KB[ruta] = json.load(f).get("perfiles") or {}
        except (OSError, ValueError):
            _PERFILES_KB[ruta] = {}
    return _PERFILES_KB[ruta].get(perfil) or {}


def _tipo_del_perfil(tipo, perfil, tipo_novato):
    """Tipo de patrón de un conjunto como se lo dice al modelo: el experto lee el término técnico («singularidad»); los demás,
    sólo en palabras comunes («se asocia con pocas clases»), para que el texto no traiga jerga."""
    if perfil == "experto" or tipo not in tipo_novato:
        return tipo
    return re.sub(r"\s*\((?:singularidad|patrón constante)\)", "", tipo_novato[tipo])


def datos_prompt(h, ruta_kb=None):
    """Hallazgos con los números ya formateados y los datos visibles según el perfil (RF-PU-2, RF-PU-3)."""
    perfil = h["perfil"]
    kb_perfil = {} if (h.get("guia_redaccion") and h.get("ejemplo_estilo") and "intensidad_llana" in h) else _perfil_kb(perfil, ruta_kb)
    llana = h.get("intensidad_llana") or kb_perfil.get("intensidad_llana") or {}
    vis = h.get("visibles") or dict(valor_test=perfil != "novato", p_valor=perfil == "experto",
                                    class_cat=perfil == "experto", razon=perfil == "experto")
    tipo_novato = h.get("tipo_novato") or {}
    # El prompt tiene un tope fijo (ver MAX_GRUPOS): se formatea sólo lo que viaja al modelo.
    k = min(len(h["grupos"]), MAX_GRUPOS)
    por_grupo = max(MIN_POR_GRUPO, MAX_DETALLE // max(k, 1))
    variables = _variables(h)
    comunes, numeros_extra = _comunes(h, k)
    comparacion = _comparacion(h)
    numeros_extra = set(numeros_extra) | {x for t in comparacion for x in re.findall(r"las (\d+) \w+ \(", t)}
    afines, numeros_afines = ([], set()) if comparacion else _afines(h)      # sin familias ni niveles, la lectura cruzada es por clase
    numeros_extra |= numeros_afines
    if vis["p_valor"] and any(_no_significativa_al_5(p) for g in h["grupos"][:k] for p in g["pares"]):
        numeros_extra |= {"5", "0,05"}                  # «no significativa al 5 %» (ver _marcar_no_significativas)
    variable_unica = variables[0] if (len(variables) == 1 and not _clases_compuestas(h)) else ""
    grupos = []
    for g in h["grupos"][:k]:
        pares = [dict(clase=_clase_txt(p["clase"]), desglose=_desglose(p["clase"], variables),
                      significacion=p["significacion"], tipo_asociacion=_tipo_asociacion(p, llana),
                      valor_test=p.get("valor_test_txt") or num(p["valor_test"], 3),
                      p_texto=p["p_texto"] or "", cat_class=num(p["cat_class"], 1), global_=num(p["global"], 1),
                      class_cat=num(p["class_cat"], 1), razon=num(p["razon"], 2),
                      transicion=p.get("transicion_legible") or p.get("transicion", ""), peso_bajo=p.get("peso_bajo", False))
                 for p in g["pares"][:por_grupo]]
        for p in pares:
            p["global"] = p.pop("global_")
        grupos.append(dict(conjunto=g.get("conjunto_legible") or g["conjunto"], posicion=_posicion(g, h), fuerza=g.get("fuerza_txt") or num(g["fuerza"], 3), n_pares=g["n_pares"],
                           omitidas=max(0, len(g["pares"]) - por_grupo),
                           tipo=_tipo_del_perfil(g["tipo"], perfil, tipo_novato), pares=pares))
    por_tipo = {}
    for g in h["grupos"]:
        t = _tipo_del_perfil(g["tipo"], perfil, tipo_novato)
        por_tipo[t] = por_tipo.get(t, 0) + 1
    nom = {g["conjunto"]: g.get("conjunto_legible") or g["conjunto"] for g in h["grupos"]}
    trans = []
    for g in h["grupos"][:k]:
        for p in g["pares"]:
            for otro in (x.strip() for x in (p.get("transicion") or "").split(",") if x.strip()):
                par = tuple(sorted([nom[g["conjunto"]], nom.get(otro, otro)]))
                if par not in trans:
                    trans.append(par)
        if len(trans) >= MAX_TRANSICIONES:
            break
    return dict(
        contexto_estudio=(h.get("contexto") or "").strip(), variables_txt=_variables_txt(h), desglose_ejemplo=_ejemplo_desglose(h),
        palabras_ejemplo=_ejemplo_palabras(h), fin_ejemplo=_ejemplo_fin(h),       # ejemplos de forma tomados de los datos, no del prompt
        guia_redaccion=_lista(h.get("guia_redaccion") or kb_perfil.get("guia_redaccion")),      # RF-PU-3: salen de la base de conocimiento
        ejemplo_estilo=h.get("ejemplo_estilo") or kb_perfil.get("ejemplo_estilo") or "",
        tipos_distintos=len(por_tipo) > 1,
        hay_sub=any(str(p.get("direccion") or "").startswith("sub") for g in h["grupos"][:k] for p in g["pares"]),
        transiciones=[f"{a} y {b}" for a, b in trans[:MAX_TRANSICIONES]],
        comunes=comunes, comparacion=comparacion, afines=afines, variable_unica=variable_unica, numeros_extra=sorted(numeros_extra),
        secciones=[dict(id=s["id"], nombre=s["nombre"],
                        contenido="" if (not vis["valor_test"] and re.search(r"valor test|fuerza", s["contenido"], re.IGNORECASE)) else s["contenido"])
                   for s in h["secciones"] if s["id"] in SECCIONES],
        recurrentes=[dict(clase=_clase_txt(c), n=len(cs),
                          conjuntos=", ".join(cs[:MAX_NOMBRES]) + (f" y {len(cs) - MAX_NOMBRES} más" if len(cs) > MAX_NOMBRES else ""))
                     for c, cs in clases_recurrentes(h)],
        por_tipo=[dict(tipo=t, n=n) for t, n in por_tipo.items()],
        tipo=TIPOS[h["descripcion"]], archivo=MARCADOR_ARCHIVO, n_clases=h["n_clases"], n_categorias=h["n_categorias"],
        n_significativas=h["n_significativas"], n_pares=h["n_pares"], minimo_clases=h["minimo_clases"],
        n_no_significativas=h.get("n_no_significativas", 0),
        n_grupos=len(h["grupos"]), n_grupos_detallados=k, n_detalladas=sum(len(g["pares"]) for g in grupos),
        grupos=grupos, perfil=perfil, instruccion_registro=h["instruccion_registro"],
        hay_peso_bajo=any(p.get("peso_bajo") for g in h["grupos"] for p in g["pares"]),
        mostrar_valor_test=vis["valor_test"], mostrar_p=vis["p_valor"], mostrar_class_cat=vis["class_cat"] or vis["razon"])


def _resumen_otros_grupos(h, desde):
    """Párrafo, calculado por código, de los conjuntos que no se detallan al modelo (a partir del índice `desde`)."""
    resto = h["grupos"][desde:]
    if not resto:
        return ""
    nombres = [g.get("conjunto_legible") or g["conjunto"] for g in resto]
    total = sum(g["n_pares"] for g in resto)
    lista = ", ".join(nombres[:10]) + (f" y {len(nombres) - 10} más" if len(nombres) > 10 else "")
    return (f"Otros {len(resto)} {'conjunto' if len(resto) == 1 else 'conjuntos'}, con {total} "
            f"{'asociación' if total == 1 else 'asociaciones'} en total, no se detallan en esta síntesis: {lista}.")


_ENTORNO = Environment(loader=FileSystemLoader(os.path.join(DIR, "plantillas")), trim_blocks=False)


def armar_prompt(h, pd=None):
    """Prompt único de la síntesis (RF-MS-6): el del modelado académico, con los datos visibles del perfil."""
    return _ENTORNO.get_template(PLANTILLA).render(**(pd or datos_prompt(h)))


def _citas_ajenas_al_conjunto(t, h, k):
    """Problemas de un párrafo sobre el conjunto k: sólo puede nombrar clases de ese conjunto y, como transición,
    conjuntos contiguos a él. Complementa a verificar_relaciones, que corta las oraciones en los dos puntos."""
    g = h["grupos"][k]
    propias = {p["clase"] for p in g["pares"]}
    vecinos = {x.strip() for p in g["pares"] for x in (p.get("transicion") or "").split(",") if x.strip()}
    variables = _variables(h)

    def citada(c, t=t):                 # por su nombre («FLO_F3») o con palabras («la cepa FLO en la fecha F3»)
        if _cita_clase(t, c):
            return True
        partes = c.split("_")
        if not variables or len(variables) != len(partes) or not all(x in t for x in partes):
            return False
        return re.search(_alias_palabras(c, variables), t, re.IGNORECASE) is not None
    problemas = [f"la clase {c} no pertenece al conjunto" for c in sorted({p["clase"] for o in h["grupos"] for p in o["pares"]} - propias)
                 if citada(c)]
    frases = re.split(r"(?<=[.!?;])\s+", t)
    for o in h["grupos"]:
        if o is g or o["conjunto"] in vecinos:
            continue
        donde = [f for f in frases if any(_cita(f, n) for n in _cortos(o))]
        if not donde:
            continue
        # Otro conjunto sólo se puede nombrar para decir algo cierto: que una clase de este conjunto también se asocia con
        # él («la cepa E47 en la fecha F2 también se asocia con c4»), sin llamarlo vecino ni transición.
        ambas = propias & {p["clase"] for p in o["pares"]}
        if not ambas or any(re.search(r"vecin|contigu|transici|al\s+lado", f, re.IGNORECASE) or not any(citada(c, f) for c in ambas)
                            for f in donde):
            problemas.append(f"el conjunto {o.get('conjunto_legible') or o['conjunto']} no es contiguo al conjunto")
    return problemas


def _grupo_citado(texto, h):
    """Índice del grupo que nombra el texto (el que aparece primero), o None."""
    pos = []
    for i, g in enumerate(h["grupos"]):
        for n in _cortos(g):
            m = n and re.search(r"(?<![\w])" + re.escape(n) + r"(?![\w])", texto)
            if m:
                pos.append((m.start(), i))
    return min(pos)[1] if pos else None


def _total_explicito(parrafo, g):
    """«Frente al mismo total» → «frente al 29,1 % del total». En las descripciones de filas y de grupos el porcentaje del
    total es del conjunto, el mismo para todas sus clases: si el modelo lo abrevia, el código repone la cifra (al lector
    novato «el mismo total» no le dice nada). Si las asociaciones del conjunto no comparten ese porcentaje, no toca nada."""
    totales = {num(p["global"], 1) for p in g["pares"] if p.get("global") is not None}
    if len(totales) != 1:
        return parrafo
    total = totales.pop()
    return re.sub(r"frente\s+al\s+(?:mismo\s+total|total(?:\s+(?:mencionado|anterior|indicado|ya\s+citado|citado))?)(?:\s+de(?:l)?\s+" + re.escape(total) + r"\s*%)?",
                  f"frente al {total} % del total", parrafo, flags=re.IGNORECASE)


def _rangos_en_su_lugar(texto, h):
    """Quita el rango de un conjunto («(1,3 a 9,3)») cuando no va pegado al nombre de ese conjunto: «las clases con fecha F1
    (1,3 a 9,3)» le atribuye a la fecha los límites de Are1. R-MS-12 no lo ve, porque los números existen."""
    duenos = {}
    for g in h["grupos"]:
        m = re.fullmatch(r"(\S+) \((.+ a .+)\)", g.get("conjunto_legible") or "")
        if m:
            duenos.setdefault(m.group(2), set()).add(m.group(1))
    if not duenos:
        return texto

    def revisar(m):
        suyos = duenos.get(re.sub(r"\s+", " ", m.group(1)))
        if not suyos:
            return m.group(0)
        antes = texto[:m.start()]
        return m.group(0) if any(re.search(r"(?<!\w)" + re.escape(d) + r"$", antes) for d in suyos) else ""
    return re.sub(r"\s*\((-?\d+(?:,\d+)?\s+a\s+-?\d+(?:,\d+)?)\)", revisar, texto)


_ORDINALES = {"segundo", "segunda", "tercer", "tercero", "tercera", "cuarto", "cuarta", "quinto", "quinta", "sexto", "sexta",
              "séptimo", "séptima", "octavo", "octava", "noveno", "novena", "décimo", "décima"}


def _cifras(texto, nombres=()):
    """«tres conjuntos» → «3 conjuntos» (regla 5 del prompt: las cantidades van con cifras). Sólo cardinales seguidos de una
    palabra; con la cifra a la vista, los controles de conteos («N conjuntos», «N clases») también la revisan. Una clase o
    un conjunto que se llame como un número («Dos») no se toca."""
    propios = {str(n).lower() for n in nombres if n}
    cardinales = {k: v for k, v in _UNIDADES.items() if v <= 29 and k not in _ORDINALES and k not in propios}
    if not cardinales:
        return texto
    palabras = "|".join(sorted(cardinales, key=len, reverse=True))
    sustituir = lambda m: str(cardinales[m.group(1).lower()])
    texto = re.sub(r"(?<![\w_])(" + palabras + r")(?![\w_])(?=\s+(?!puntos\b)[a-záéíóúñ])", sustituir, texto, flags=re.IGNORECASE)
    # Al final de una oración («abarcando tres.»), sólo después de un verbo o preposición que pide una cantidad.
    return re.sub(r"(\b(?:abarcando|abarca|con|de|son|hay|suman|incluye|reúne|reúnen)\s)(" + palabras + r")(?=[.,;](?:\s|$))",
                  lambda m: m.group(1) + str(cardinales[m.group(2).lower()]), texto, flags=re.IGNORECASE)


# Tropiezos de redacción que se repiten y se corrigen sin cambiar lo que el texto dice: (expresión, reemplazo).
_MULETILLAS = [
    (re.compile(r"\bde\s+fuerza\s+fuerte\b", re.IGNORECASE), "fuerte"),
    (re.compile(r"\bcon\s+(?:una\s+)?fuerza\s+fuerte\b", re.IGNORECASE), "de forma fuerte"),
    (re.compile(r"\bfuerza\s+fuerte\b", re.IGNORECASE), "intensidad fuerte"),
    (re.compile(r"\bEn conjunto,\s+(?=(?:el|este|los|estos|cada)\s+conjuntos?\b)"), "En resumen, "),
    (re.compile(r"\bconjunto de valores(?=(?:\s+\w+){0,2}\s+(?:el\s+)?de\s+valores\b)", re.IGNORECASE), "conjunto"),
    # Conectores de relleno que la guía de redacción prohíbe: «Le sigue la asociación con X» → «También se asocia con X».
    (re.compile(r"\bLe\s+sigue\s+la\s+asociación\s+con\b"), "También se asocia con"),
    (re.compile(r"\bLe\s+sigue\s+((?:la|el|las|los)\s)"), lambda m: m.group(1).capitalize()),
]


def _muletillas(texto):
    for patron, nuevo in _MULETILLAS:
        texto = patron.sub(nuevo, texto)
    return texto


def _podar_s1(texto, h):
    """La descripción general sólo lleva el tipo de descripción, el archivo y las cantidades: una oración que no trae nada de
    eso («La estructura metodológica se limita a…») es relleno. Con contexto del estudio no se toca: puede decir qué se estudió."""
    if (h.get("contexto") or "").strip():
        return texto
    frases = re.split(r"(?<=[.!?])[ \t]+", texto)
    quedan = [f for f in frases if re.search(r"\d|descripci[oó]n\s+de\s+(?:grupos|filas|columnas)", f, re.IGNORECASE) or h["archivo"] in f]
    return " ".join(quedan) if quedan else texto


_MENOS_MARCADA = re.compile(r"(?:,\s*)?(?:aunque\s+)?(?:de\s+(?:una\s+)?(?:forma|manera)\s+menos\s+marcada|en\s+menor\s+(?:medida|grado)"
                            r"|con\s+menos\s+fuerza)(?:\s*,)?", re.IGNORECASE)


def _sin_comparativo_falso(parrafo, g):
    """Quita «de forma menos marcada», «en menor medida» y «con menos fuerza» cuando todas las asociaciones del conjunto tienen
    la misma intensidad: el modelo las copia del ejemplo de estilo y contradicen lo que dice a continuación."""
    if len(g["pares"]) < 2 or len({p.get("intensidad") for p in g["pares"]}) != 1:
        return parrafo

    def quitar(m):
        al_comienzo = not parrafo[:m.start()].strip() or parrafo[:m.start()].rstrip()[-1:] in ".:;!?"
        return m.group(0) if al_comienzo else ""
    return re.sub(r" {2,}", " ", _MENOS_MARCADA.sub(quitar, parrafo))


_VACIAS = {"en", "el", "la", "los", "las", "un", "una", "se", "con", "este", "esta", "estos", "estas", "conjunto", "conjuntos", "resumen", "síntesis", "para", "como", "sólo", "solo",
           "entre", "clase", "clases", "tanto", "también", "donde", "cual", "cuales", "sobre", "todo", "todas", "todos"}


def _sin_cierre_repetido(parrafo):
    """Quita la última oración de un párrafo de S2 cuando sólo repite la primera (mismas palabras, sin cifras propias)."""
    m = _INICIO_GRUPO.match(parrafo)
    fin = parrafo.find(":", m.end()) if m else -1
    cab, cuerpo = (parrafo[:fin + 1] + " ", parrafo[fin + 1:].strip()) if fin >= 0 else ("", parrafo)
    frases = re.split(r"(?<=[.!?])\s+", cuerpo)
    if len(frases) < 3 or re.search(r"\d\s*%", frases[-1]):
        return parrafo
    def palabras(s):           # palabras de contenido y nombres propios («ECO», «F3»), sin la «s» del plural
        w = {x.lower() for x in re.findall(r"[\wáéíóúñ]+", s) if len(x) >= 4 or re.search(r"[A-Z0-9]", x)} - _VACIAS
        return {x[:-1] if (len(x) > 4 and x.endswith("s")) else x for x in w}
    ultima, primera = palabras(frases[-1]), palabras(frases[0])
    if len(ultima) >= 2 and len(ultima & primera) / len(ultima) >= 0.75:
        return (cab + " ".join(frases[:-1])).strip()
    return parrafo


def _no_significativa_al_5(p):
    return isinstance(p.get("p_valor"), (int, float)) and p["p_valor"] >= 0.05 and bool(p.get("p_texto"))


def _marcar_no_significativas(parrafo, g):
    """Perfil experto: junto a un p-valor de 0,05 o más agrega «no significativa al 5 %», si el texto no lo dice ya. DaFu
    exporta desde un valor test de 1,65, así que las asociaciones débiles (p entre 0,05 y 0,10) entran sin ser significativas
    al nivel habitual, y un lector experto debe verlo."""
    for valor in {p["p_texto"].replace("p = ", "") for p in g["pares"] if _no_significativa_al_5(p)}:
        def anotar(m):
            sigue = parrafo[m.end():m.end() + 60]
            # «16,5 %» no es «5 %»: la cifra debe estar suelta.
            return m.group(0) if re.search(r"(?<![\d,.])5\s*%|(?<!\d)0,05(?!\d)", sigue) else m.group(0) + ", no significativa al 5 %"
        parrafo = re.sub(r"\bp\s*[=:]\s*" + re.escape(valor) + r"(?!\d)", anotar, parrafo)
    return parrafo


def _podar_s3(texto, h):
    """Quita de la conclusión las oraciones generales que no nombran ninguna clase ni conjunto ni traen cifras («Las
    asociaciones varían según la combinación analizada»): no dicen nada. La aclaración sobre lo que contiene el archivo queda."""
    nombres = _nombres_de(h)
    frases = re.split(r"(?<=[.!?])[ \t]+", texto)

    def dice_algo(f):
        if re.search(r"\d|DaFu|archivo|umbral|significativ|pocos\s+datos", f, re.IGNORECASE):
            return True
        return any(tok in nombres for tok in re.findall(r"[\w.]+", f))
    quedan = [f for f in frases if dice_algo(f)]
    return " ".join(quedan) if quedan else texto


def _clase_con_nombre_completo(texto, h):
    """«la cepa FLO y fecha F1» → «la clase cepa FLO, fecha F1». Sólo se reescribe la forma exacta del desglose de una clase que existe."""
    variables = _variables(h)
    if len(variables) < 2:
        return texto
    for clase in {p["clase"] for g in h["grupos"] for p in g["pares"]}:
        desglose = _desglose(clase, variables)
        partes = desglose.split(", ") if desglose else []
        if not partes or partes[0].lower() not in texto.lower():
            continue
        con_y = ", ".join(partes[:-1]) + " y " + partes[-1] if len(partes) > 2 else " y ".join(partes)
        texto = re.sub(r"\b(la|el)\s+" + re.escape(con_y) + r"(?![\w,])",
                       lambda m: ("La" if m.group(1)[0].isupper() else "la") + " clase " + desglose, texto, flags=re.IGNORECASE)
        # «es cepa E47, fecha F3» / «pasa con cepa ECO, fecha F3»: sin «la clase» delante (salvo en «las clases con cepa…», que es una lista).
        texto = re.sub(r"(?<!clases )(?<!clase )\b(es|con)\s+" + re.escape(desglose) + r"(?![\w])",
                       lambda m: f"{m.group(1)} la clase {desglose}", texto, flags=re.IGNORECASE)
    return texto


def _porcentaje_con_articulo(texto):
    """«Porcentaje es la parte de los valores…» (sin artículo, al comienzo de una oración) → «El porcentaje es…»."""
    return re.sub(r"(^|(?<=[.!?:]\s))Porcentaje es\b", "El porcentaje es", texto)


_SIN_CONTRAPARTE = re.compile(r"\bpor\s+otr[oa]\s+(?:lado|parte)\b|\ben\s+cambio\b|\bpor\s+el\s+contrario\b", re.IGNORECASE)


def _sin_por_un_lado(texto):
    """Quita «Por un lado,» cuando el texto no trae su contraparte («por otro lado», «en cambio»): sin contraste, sólo estorba."""
    if not re.search(r"\bpor\s+un\s+lado\b", texto, re.IGNORECASE) or _SIN_CONTRAPARTE.search(texto):
        return texto
    texto = re.sub(r"(^|(?<=[.!?:]\s))Por\s+un\s+lado,\s*(\w)", lambda m: m.group(1) + m.group(2).upper(), texto)
    return re.sub(r"(,\s*)por\s+un\s+lado,\s*", r"\1", texto, flags=re.IGNORECASE)


_DICE_CONJUNTOS_DISTINTOS = re.compile(r"\bconjuntos?\s+(?:distintos|diferentes)\b|\b(?:distintos|diferentes)\s+conjuntos\b", re.IGNORECASE)


def _sin_conjuntos_distintos_falsos(texto, h):
    """Quita la oración que dice «conjuntos distintos» de clases que, en los datos, tienen exactamente los mismos conjuntos."""
    if not _DICE_CONJUNTOS_DISTINTOS.search(texto):
        return texto
    conjuntos = {}
    for g in h["grupos"]:
        for p in g["pares"]:
            conjuntos.setdefault(p["clase"], set()).add(g["conjunto"])
    variables = _variables(h)
    detectores = {c: _detector_de_clase(c, variables) for c in conjuntos}
    partes = re.split(r"(?<=[.!?])(\s+)", texto)
    quedan = []
    for frase, separador in zip(partes[0::2], partes[1::2] + [""]):
        if _DICE_CONJUNTOS_DISTINTOS.search(frase):
            nombradas = [c for c, d in detectores.items() if d(frase)]
            if len(nombradas) >= 2 and len({frozenset(conjuntos[c]) for c in nombradas}) == 1:
                continue
        quedan.append(frase + separador)
    return "".join(quedan).rstrip() or texto


def _sin_oraciones_que_no_verifican(texto, h, pd):
    """(texto, [(oración, motivos)]): quita las oraciones que no pasan los controles, si queda alguna que sí pase."""
    partes = re.split(r"(?<=[.!?])(\s+)", texto)
    frases, separadores = partes[0::2], partes[1::2] + [""]
    if len(frases) < 2:
        return texto, []

    def motivos_de(frase):
        ajenos = verificar([frase], h, pd)
        return (([_motivo_valores(ajenos)] if ajenos else []) + verificar_relaciones([frase], h)
                + verificar_atribuciones([frase], h, pd) + verificar_afirmaciones([frase], h))
    malas = {i: m for i, f in enumerate(frases) if (m := motivos_de(f))}
    if not malas or len(malas) == len(frases):
        return texto, []
    quedan = "".join(f + s for i, (f, s) in enumerate(zip(frases, separadores)) if i not in malas).rstrip()
    return quedan, [(frases[i], m) for i, m in malas.items()]


_EXPLICACION_VALOR_TEST = re.compile(
    r"([^.!?\n]*?[^\s.!?,;:])\s*(?:[,;:]|\s[—-])\s*(?:y\s+)?((?:el\s+)?valor\s+test\s+(?:mide|indica|expresa|señala|refleja|sirve)\b[^.!?\n]*[.!?])",
    re.IGNORECASE)


def _explicacion_aparte(texto):
    """La oración que explica qué es el valor test, pegada con «;» o «,» al final de otra, pasa a ser una oración propia."""
    def aparte(m):
        if re.match(r"\s*Hallazgos\s+para\b", m.group(1), re.IGNORECASE):
            return m.group(0)
        e = m.group(2)
        return f"{m.group(1)}. {e[0].upper()}{e[1:]}"
    return _EXPLICACION_VALOR_TEST.sub(aparte, texto)


_TRANSICION_SUELTA = re.compile(r"^(?:La misma clase|La clase)\s+(?P<c>.+?)\s+también se asocia con el conjunto vecino\s+(?P<n>.+?)\.$")


def _transiciones_juntas(texto):
    """«La clase 7 también se asocia con el conjunto vecino ent1. La clase 12 también se asocia con el conjunto vecino ent1.»
    → «Las clases 7 y 12 también se asocian con el conjunto vecino ent1.» (oraciones seguidas con el mismo vecino)."""
    frases, salida, i = re.split(r"(?<=[.!?])[ \t]+", texto), [], 0
    while i < len(frases):
        m = _TRANSICION_SUELTA.match(frases[i])
        j, clases = i + 1, [m.group("c")] if m else []
        while m and j < len(frases):
            otra = _TRANSICION_SUELTA.match(frases[j])
            if not (otra and otra.group("n") == m.group("n")):
                break
            clases.append(otra.group("c"))
            j += 1
        if len(clases) > 1:
            salida.append(f"Las clases {', '.join(clases[:-1])} y {clases[-1]} también se asocian con el conjunto vecino {m.group('n')}.")
        else:
            salida.append(frases[i])
            j = i + 1
        i = j
    return " ".join(salida)


def _vecinos_sin_nombrar(parrafo, h, g):
    """Motivos de rechazo si el párrafo habla de un conjunto vecino sin decir cuál es: «la misma clase también se asocia con el
    conjunto vecino.» deja al lector sin el dato. Sólo se mira a los vecinos que figuran como conjuntos del análisis."""
    por_nombre = {o["conjunto"]: o for o in h["grupos"]}
    problemas = set()
    for p in g["pares"]:
        for v in (x.strip() for x in (p.get("transicion") or "").split(",") if x.strip()):
            o = por_nombre.get(v)
            if o and not any(_cita(parrafo, n) for n in _cortos(o)):
                problemas.add(f"no nombra el conjunto vecino {o.get('conjunto_legible') or v} de {p['clase']}")
    return sorted(problemas)


_DICE_NIVEL = re.compile(r"\b(?:fuerte|moderad|d[eé]bil)\w*", re.IGNORECASE)


_COMO_LA_ANTERIOR = re.compile(r"algo\s+(?:muy\s+)?(?:parecido|similar)|de\s+(?:manera|forma)\s+(?:muy\s+)?similar|lo\s+mismo|del\s+mismo\s+modo",
                               re.IGNORECASE)


def _detector_de_clase(clase, variables):
    """Función que dice si una oración nombra a la clase (por su nombre, por su desglose en palabras o, si es un número, como «clase N»)."""
    if _es_numerico(clase):
        return lambda frase: clase in _clases_numericas_citadas(frase)
    rx = re.compile(_alias_clase(clase, variables), re.IGNORECASE)
    return lambda frase: rx.search(frase) is not None


def _sin_intensidad(parrafo, h, g, gp, llano):
    """([(par, par del prompt) cuya clase no dice su intensidad], {clase: detector de su nombre}, oraciones del párrafo)."""
    variables = _variables(h)
    frases = re.split(r"(?<=[.!?])\s+", parrafo)           # sin «;»: separa cifras dentro de un paréntesis («valor test: 12,8; 88,4 %»)
    nivel_llano = re.compile("|".join(rx.pattern for rx in _INTENSIDADES.values()), re.IGNORECASE)
    alias = {}
    for p in g["pares"][:len(gp["pares"])]:
        c = p["clase"]
        if p.get("intensidad") and (c if _es_numerico(c) else c.split("_")[0]) in parrafo:
            alias[c] = _detector_de_clase(c, variables)
    generales = [f for f in frases if not any(d(f) for d in alias.values()) and re.search(r"\bclases\b", f)]
    faltan = []
    for p, q in zip(g["pares"], gp["pares"]):
        c = p["clase"]
        if c not in alias:
            continue
        con_la_clase = [f for f in frases if alias[c](f)]
        if not con_la_clase:
            continue
        dice = nivel_llano if llano else _DICE_NIVEL
        if any(dice.search(f) or (llano and _COMO_LA_ANTERIOR.search(f)) for f in con_la_clase):
            continue
        if llano and any(_INTENSIDADES[p["intensidad"]].search(f) for f in generales if p["intensidad"] in _INTENSIDADES):
            continue
        faltan.append((p, q))
    return faltan, alias, frases


def verificar_intensidad_por_asociacion(parrafo, h, g, gp, llano=False):
    """Que cada asociación detallada diga su intensidad en alguna oración que nombra su clase («fuerte», «moderada» o «débil»; con
    `llano`, «mucho más de lo esperable» y similares). Con `llano` cuentan también «algo parecido pasa con X» y una oración general sobre «las clases»."""
    problemas = []
    for p, q in _sin_intensidad(parrafo, h, g, gp, llano)[0]:
        if llano:
            frase = q["tipo_asociacion"]
            problemas.append(f"no dice la intensidad de {p['clase']}: debe decir «{frase[0].lower() + frase[1:]}»")
        else:
            problemas.append(f"no dice si la asociación de {p['clase']} es fuerte, moderada o débil")
    return problemas


def _completar_para_novato(parrafo, h, g, gp):
    """Perfil sin valor test: agrega por código la intensidad y el conjunto vecino que el modelo omitió y los hallazgos ya traen.
    Sólo actúa sobre una oración con porcentaje que nombra a la clase, y si todas las clases sin intensidad de esa oración tienen la misma."""
    faltan, alias, _ = _sin_intensidad(parrafo, h, g, gp, True)
    partes = re.split(r"(?<=[.!?])(\s+)", parrafo)
    frases, separadores = partes[0::2], partes[1::2] + [""]

    def oracion_de_datos(clase):
        return next((i for i, f in enumerate(frases) if alias[clase](f) and "%" in f), None)

    def nombradas(i):
        return [c for c, d in alias.items() if d(frases[i])]

    por_frase = {}
    for p, q in faltan:
        i = oracion_de_datos(p["clase"])
        if i is not None and q["tipo_asociacion"].startswith("Aparece"):
            por_frase.setdefault(i, []).append((p, q))
    for i, items in por_frase.items():
        if len({p["intensidad"] for p, _ in items}) != 1 or len(nombradas(i)) != len(items):
            continue
        dicha = items[0][1]["tipo_asociacion"][0].lower() + items[0][1]["tipo_asociacion"][1:]
        enlace = "" if len(items) == 1 else (" en ambos casos" if len(items) == 2 else " en todos los casos")
        cierre = re.search(r"[.!?]+$", frases[i])
        cuerpo, fin = (frases[i][:cierre.start()], frases[i][cierre.start():]) if cierre else (frases[i], "")
        frases[i] = f"{cuerpo}:{enlace} {dicha}{fin}"
    ahora = "".join(f + s for f, s in zip(frases, separadores))
    por_nombre = {o["conjunto"]: o for o in h["grupos"]}
    nuevas = {}
    for p in g["pares"][:len(gp["pares"])]:
        c = p["clase"]
        if c not in alias:
            continue
        sin_nombrar = [por_nombre[v].get("conjunto_legible") or v for v in (x.strip() for x in (p.get("transicion") or "").split(",") if x.strip())
                       if v in por_nombre and not any(_cita(ahora, n) for n in _cortos(por_nombre[v]))]
        i = oracion_de_datos(c)
        if sin_nombrar and i is not None and len(nombradas(i)) == 1 and i not in nuevas:
            vecinos = sin_nombrar[0] if len(sin_nombrar) == 1 else ", ".join(sin_nombrar[:-1]) + " y " + sin_nombrar[-1]
            nuevas[i] = f"La misma clase también se asocia con {'el conjunto vecino' if len(sin_nombrar) == 1 else 'los conjuntos vecinos'} {vecinos}."
    salida = []
    for i, f in enumerate(frases):
        salida.append(f + (" " + nuevas[i] if i in nuevas else "") + separadores[i])
    return "".join(salida)


_ACLARA_TRANSICION = "Una transición es la misma clase asociada con conjuntos vecinos."
_YA_ACLARADA = re.compile(r"misma\s+clase[^.]{0,40}conjuntos?\s+vecinos?", re.IGNORECASE)


def _con_transicion_aclarada(textos, h):
    """Intermedio: aclara qué es una transición justo después de la primera oración que la nombra, si ningún párrafo la aclaró."""
    if h.get("perfil") != "intermedio" or any(_YA_ACLARADA.search(t) for t in textos):
        return textos
    for i, t in enumerate(textos):
        m = re.search(r"\btransici[oó]n(?:es)?\b", t, re.IGNORECASE)
        if m:
            fin = re.search(r"(?<=[.!?])\s|$", t[m.end():])
            pos = m.end() + fin.start()
            return textos[:i] + [t[:pos] + " " + _ACLARA_TRANSICION + t[pos:]] + textos[i + 1:]
    return textos


_EXPLICA_VALOR_TEST = "El valor test mide cuán improbable es que la asociación sea casual; no mide cuán intenso es el fenómeno."
_EXPLICA_PORCENTAJE = ("El porcentaje es la parte de los valores de la clase que cae en el conjunto, comparada con la parte que ese "
                       "conjunto representa en el total.")
_DICE_VALOR_TEST = re.compile(r"\bvalor\s+test\s+(?:mide|indica|expresa|señala|refleja|sirve)\b", re.IGNORECASE)
_DICE_PORCENTAJE = re.compile(r"\bporcentaj\w*\b[^.]{0,80}\b(?:parte|proporci\w+)\b|\bparte\s+de\s+los\s+valores\s+de\s+(?:la|cada)\s+clase\b", re.IGNORECASE)


def _con_explicaciones(texto, h, pd, g):
    """Agrega, tras la primera oración del primer párrafo, la explicación del porcentaje (novato e intermedio) y del valor test (intermedio) si faltan."""
    if not texto or h.get("perfil") not in ("novato", "intermedio") or g is not h["grupos"][0]:
        return texto
    faltan = []
    if h["perfil"] == "intermedio" and pd.get("mostrar_valor_test") and not _DICE_VALOR_TEST.search(texto):
        faltan.append(_EXPLICA_VALOR_TEST)
    if not _DICE_PORCENTAJE.search(texto):
        faltan.append(_EXPLICA_PORCENTAJE)
    if not faltan:
        return texto
    m = re.search(r"(?<=[.!?])\s+", texto)
    return texto + " " + " ".join(faltan) if not m else texto[:m.start()] + " " + " ".join(faltan) + texto[m.start():]


def _pulir(texto, h, pd, g=None):
    """Arreglos que se hacen por código antes de verificar un texto del modelo: no cambian ningún dato. `g` es el conjunto del
    párrafo, si es de S2."""
    texto = _podar(texto, _nombres_de(h), pd.get("tipos_distintos", False))
    if not h.get("n_no_significativas"):
        # Una oración que afirma lo que el archivo no permite saber se quita, en lugar de descartar toda la síntesis por ella.
        frases = re.split(r"(?<=[.!?])[ \t]+", texto)
        quedan = [f for f in frases if not any(re.search(patron, f, re.IGNORECASE) for patron, _ in AFIRMACIONES_SIN_RESPALDO)]
        if quedan and len(quedan) < len(frases):
            texto = " ".join(quedan)
    texto = _porcentaje_con_articulo(_muletillas(_cifras(_rangos_en_su_lugar(texto, h), _nombres_de(h))))
    texto = _clase_con_nombre_completo(texto, h)
    texto = _explicacion_aparte(_sin_conjuntos_distintos_falsos(_sin_por_un_lado(texto), h))
    if g is not None and texto:
        texto = _sin_cierre_repetido(_sin_comparativo_falso(_total_explicito(texto, g), g))
        if pd.get("mostrar_p"):
            texto = _marcar_no_significativas(texto, g)
        texto = _transiciones_juntas(_sin_vecino_falso(texto, h, g))
    return texto


def _sin_vecino_falso(parrafo, h, g):
    """«También se asocia con el conjunto vecino c4» → «…con el conjunto c4» cuando c4 no figura como contiguo de este
    conjunto: que la clase se asocia con los dos es un dato; que sean vecinos, no (sólo lo dicen las transiciones, R-MI-12)."""
    vecinos = {x.strip() for p in g["pares"] for x in (p.get("transicion") or "").split(",") if x.strip()}
    for o in h["grupos"]:
        if o is g or o["conjunto"] in vecinos:
            continue
        for n in sorted((x for x in _cortos(o) if x and x in parrafo), key=len, reverse=True):
            parrafo = re.sub(r"\b(conjuntos?)\s+(?:vecinos?|contiguos?)\s+(?=" + re.escape(n) + r"(?!\w))", r"\1 ", parrafo, flags=re.IGNORECASE)
    return parrafo


def _partir_por_grupo(t, h):
    """Separa S2 en los párrafos de cada grupo: ({índice del grupo: [párrafos]}, [texto antes del primer grupo]).
    Un párrafo pertenece al grupo que nombra en su encabezado («Hallazgos para el conjunto …:»); el que no nombra ninguno
    continúa el del grupo anterior."""
    partes = [x.strip() for x in re.split(r"\n\s*\n|(?=" + _INICIO_GRUPO.pattern + r")", t, flags=re.IGNORECASE) if x and x.strip()]
    con_encabezado = any(_INICIO_GRUPO.match(x) for x in partes)
    por_grupo, introduccion, actual = {}, [], None
    for parte in partes:
        # Con encabezados, sólo un encabezado abre un grupo: una continuación que nombra a un vecino («transición con
        # Are2») sigue siendo del grupo anterior. Sin encabezados, el grupo es el que nombra la primera oración.
        cabeza = re.split(r"(?<=[.:;])\s", parte, maxsplit=1)[0]
        i = _grupo_citado(cabeza, h) if (_INICIO_GRUPO.match(parte) or not con_encabezado) else None
        actual = i if i is not None else actual
        if actual is None:
            introduccion.append(parte)
        else:
            por_grupo.setdefault(actual, []).append(parte)
    return por_grupo, introduccion


def _revisar_parrafo(partes, i, h, pd):
    """Pule y verifica el párrafo del conjunto i: (texto, motivos de rechazo)."""
    g = h["grupos"][i]
    p = _pulir(" ".join(partes), h, pd, g)
    if not p:
        return p, ["el modelo no redactó este grupo"]
    if not pd["mostrar_valor_test"]:
        p = _completar_para_novato(p, h, g, pd["grupos"][i])
    ajenos = verificar([p], h, pd)
    motivos = (([_motivo_valores(ajenos)] if ajenos else []) + verificar_relaciones([p], h, g)
               + _citas_ajenas_al_conjunto(p, h, i) + verificar_atribuciones([p], h, pd) + verificar_intensidad(p, h, g)
               + (verificar_intensidad_dicha(p, g, pd["grupos"][i]) + _vecinos_sin_nombrar(p, h, g)
                  + verificar_intensidad_por_asociacion(p, h, g, pd["grupos"][i], llano=True) if not pd["mostrar_valor_test"] else [])
               + (verificar_intensidad_por_asociacion(p, h, g, pd["grupos"][i]) if h.get("perfil") == "intermedio" else [])
               + verificar_afirmaciones([p], h))
    return (p if motivos else _con_explicaciones(p, h, pd, g)), motivos     # las frases fijas se agregan sólo a un texto que verificó


def _parrafo_de_respaldo(g, gp, pd):
    """Párrafo de un conjunto armado por código con los datos del perfil, para cuando el texto del modelo no verifica
    (RF-MS-9). Tiene la misma forma que los demás («Hallazgos para el conjunto …») y no usa jerga que el perfil no ve."""
    n = g["n_pares"]
    frases = [f"Hallazgos para el conjunto {gp['conjunto']}: Este conjunto se asocia con {n} {'clase' if n == 1 else 'clases'}."]
    for p in gp["pares"]:
        nombre = p["clase"] + (f" ({p['desglose']})" if p["desglose"] else "")
        nombre = nombre[0].upper() + nombre[1:]
        tipo = p["tipo_asociacion"][0].lower() + p["tipo_asociacion"][1:]
        if not pd["mostrar_valor_test"]:
            llana = f" {tipo}" if tipo.startswith("aparece") else ""
            f = f"{nombre}{llana}: el {p['cat_class']} % de sus valores está en este conjunto, frente al {p['global']} % del total."
        elif not pd["mostrar_p"]:
            f = f"{nombre}: {tipo} (valor test {p['valor_test']}; {p['cat_class']} % frente al {p['global']} % del total)."
        else:
            f = (f"{nombre}: {tipo} (valor test {p['valor_test']}; {p['p_texto']}; {p['cat_class']} % frente al {p['global']} % del total; "
                 f"Class.Cat {p['class_cat']} %; razón de proporciones {p['razon']}).")
        if p["transicion"]:
            f += (f" También se asocia con el conjunto vecino {p['transicion']}." if not pd["mostrar_valor_test"]
                  else f" Transición con {p['transicion']}.")
        if p["peso_bajo"]:
            f += " Se apoya en pocos datos."
        frases.append(f)
    if gp.get("omitidas"):
        frases.append(f"Hay {gp['omitidas']} {'asociación más' if gp['omitidas'] == 1 else 'asociaciones más'} de menor relevancia, que no se detallan.")
    return " ".join(frases)


def _hallazgos_por_grupo(t, h, pd, reintentar=None):
    """S2 redactada en una sola respuesta: se separa en un párrafo por grupo y cada uno se verifica por separado.

    Si el párrafo de un grupo no pasa R-MS-12 ni los demás controles, o el modelo no lo escribió, se le pide al modelo una
    vez más (`reintentar` recibe [(conjunto, motivos)] y devuelve una S2 nueva, o None); si tampoco verifica, ese grupo se
    informa con un párrafo armado por código (RF-MS-9).
    Devuelve (texto, grupos con respaldo, textos rechazados)."""
    por_grupo, introduccion = _partir_por_grupo(t, h)
    textos, respaldo, rechazados = [], [], []
    if introduccion:
        intro = " ".join(introduccion)
        ajenos = verificar([intro], h, pd)
        motivos = ([_motivo_valores(ajenos)] if ajenos else []) + verificar_relaciones([intro], h) + verificar_afirmaciones([intro], h)
        if motivos:
            rechazados.append(dict(seccion="S2", conjunto="", texto=intro, motivos=motivos))
        else:
            textos.append(intro)
    detallados = min(pd.get("n_grupos_detallados", len(h["grupos"])), len(h["grupos"]))
    nombre_de = lambda i: h["grupos"][i].get("conjunto_legible") or h["grupos"][i]["conjunto"]
    anotar = lambda i, p, motivos: rechazados.append(dict(seccion="S2", conjunto=nombre_de(i), texto=p, motivos=motivos))
    revisados = {}
    for i in range(detallados):
        revisados[i] = _revisar_parrafo(por_grupo.get(i, []), i, h, pd)
        if revisados[i][1]:
            anotar(i, *revisados[i])
    fallidos = [i for i in revisados if revisados[i][1]]
    nuevo = reintentar([(nombre_de(i), revisados[i][1]) for i in fallidos]) if (fallidos and reintentar) else None
    if nuevo:
        otra, _ = _partir_por_grupo(nuevo, h)
        for i in fallidos:
            antes = revisados[i][0]
            revisados[i] = _revisar_parrafo(otra.get(i, []), i, h, pd)
            if revisados[i][1] and revisados[i][0] != antes:       # el mismo texto no se registra dos veces
                anotar(i, *revisados[i])
    verificados = []
    for i, (p, motivos) in revisados.items():
        if not motivos:
            textos.append(p)
            verificados.append(len(textos) - 1)
            continue
        respaldo.append(nombre_de(i))
        textos.append(_con_explicaciones(_parrafo_de_respaldo(h["grupos"][i], pd["grupos"][i], pd), h, pd, h["grupos"][i]))
    for i, nuevo_texto in zip(verificados, _quitar_repetidas([textos[i] for i in verificados], h)):
        textos[i] = nuevo_texto
    textos = _con_transicion_aclarada(textos, h)
    resumen = _resumen_otros_grupos(h, detallados)
    if resumen:
        textos.append(resumen)
    return "\n\n".join(textos), respaldo, rechazados


def _quitar_repetidas(parrafos, h):
    """Quita de los párrafos de S2 las oraciones sin cifras que repiten, cambiando sólo los nombres, una oración de un
    párrafo anterior («Este conjunto se asocia con pocas clases…» en cada conjunto). Nunca vacía un párrafo."""
    nombres = sorted({n for g in h["grupos"] for n in _cortos(g)} | {p["clase"] for g in h["grupos"] for p in g["pares"][:MAX_DETALLE]},
                     key=len, reverse=True)
    patron = re.compile("|".join(re.escape(n) for n in nombres if n and not _es_numerico(n))) if nombres else None
    vistas, salida = set(), []
    for par in parrafos:
        m = _INICIO_GRUPO.match(par)
        cab, resto = "", par
        if m:
            fin = par.find(":", m.end())
            cab, resto = (par[:fin + 1] + " ", par[fin + 1:].strip()) if fin >= 0 else ("", par)
        frases = re.split(r"(?<=[.!?])\s+", resto)
        claves = []
        for f in frases:
            k = re.sub(r"\s+", " ", (patron.sub("X", f) if patron else f).lower()).strip(" .")
            claves.append(None if (re.search(r"\d", f) or len(k.split()) < 5) else k)
        conservadas = [f for f, k in zip(frases, claves) if k is None or k not in vistas]
        if not conservadas:
            conservadas = frases[:1]
        vistas |= {k for k in claves if k}
        salida.append((cab + " ".join(conservadas)).strip())
    return salida


def _expandir_resto(h):
    """R manda completas las primeras asociaciones de cada conjunto y, del resto, vectores (id, clase, valor test,
    transición): aquí vuelven a ser asociaciones, con sólo esos campos, para los controles del texto."""
    for g in h["grupos"]:
        r = g.pop("resto", None)
        if not r:
            continue
        uno = lambda x: x if isinstance(x, list) else [x]        # un vector de un solo elemento viaja como escalar
        ids, clases, vs, trs = (uno(r.get(k, [])) for k in ("id", "clase", "valor_test", "transicion"))
        g["pares"] = g["pares"] + [dict(id=i, clase=c, caracteristica=g["conjunto"], valor_test=v, transicion=t)
                                   for i, c, v, t in zip(ids, clases, vs, trs)]
    return h


def _texto(resp, sid):
    v = resp.get(sid) if isinstance(resp, dict) else None
    return v.strip() if isinstance(v, str) and v.strip() else None


def valores_permitidos(h, prompt_datos):
    """Conjunto de números que el texto puede contener: los de los hallazgos mostrados y los umbrales."""
    vals = set(CONSTANTES)
    for k in ("n_clases", "n_categorias", "n_significativas", "n_pares"):
        vals.add(str(prompt_datos[k]))
    if prompt_datos.get("n_no_significativas"):
        vals.add(str(prompt_datos["n_no_significativas"]))
    vals.update(str(t["n"]) for t in prompt_datos.get("por_tipo", []))
    for i, g in enumerate(prompt_datos["grupos"], start=1):
        vals.update([str(i), str(g["n_pares"])])
    vals.update(str(r["n"]) for r in prompt_datos.get("recurrentes", []))
    for k in ("n_grupos", "n_grupos_detallados", "n_detalladas"):
        if prompt_datos.get(k) is not None:
            vals.add(str(prompt_datos[k]))
    vals.update(prompt_datos.get("numeros_extra", []))             # cantidades de la lectura cruzada, calculadas por el código
    vals.update(str(g["omitidas"]) for g in prompt_datos["grupos"] if g.get("omitidas"))
    for i, g in enumerate(prompt_datos["grupos"], start=1):
        if prompt_datos["mostrar_valor_test"]:
            vals.add(g["fuerza"])
        for p in g["pares"]:
            vals.update([p["cat_class"], p["global"]])
            if prompt_datos["mostrar_valor_test"]:
                vals.add(p["valor_test"])
            if prompt_datos["mostrar_class_cat"]:
                vals.update([p["class_cat"], p["razon"]])
            if prompt_datos["mostrar_p"]:
                if p["p_texto"]:
                    vals.add(p["p_texto"].replace("p = ", "").replace("p < ", ""))
    return {_norm(v) for v in vals if v not in NO_NUMEROS}


def _norm(v):
    """Valor numérico comparable: acepta coma o punto decimal, miles con punto y signo."""
    t = str(v).strip().lstrip("-+−")
    if "," in t and "." in t:
        t = t.replace(".", "")
    elif re.fullmatch(r"[1-9]\d{0,2}(\.\d{3})+", t):       # 45.000 son miles, no 45,0
        t = t.replace(".", "")
    try:
        return round(float(t.replace(",", ".")), 6)
    except ValueError:
        return v


# Un nombre de clase numérico sólo cuenta como cita si dice «clase N» o «clases N, M y P»: suelto puede ser un dato,
# un conteo («39 asociaciones») o parte de un intervalo («31,4»).
_ITEM_CLASE = r"\d+(?:\.\d+)?(?![.,]?\d)(?!\s*%)(?!\s+(?:asociaci|clases?\b|categor|conjuntos?\b))"
_LISTA_CLASES = re.compile(r"\b(?:clases?\s*(?::|(?:tales\s+)?como)?|las?)\s+(" + _ITEM_CLASE + r"(?:\s*(?:,|\by\b|\be\b)\s*" + _ITEM_CLASE + r")*)", re.IGNORECASE)


def _clases_numericas_citadas(texto):
    return {x for m in _LISTA_CLASES.finditer(texto) for x in re.findall(r"\d+(?:\.\d+)?", m.group(1))}


def _sin_nombres(texto, nombres):
    """Texto sin los nombres de clases y conjuntos. Sólo se quita el nombre completo: la clase «2» no tapa el 2 de «42» ni de «2,5».
    Un nombre numérico sólo se quita en la forma «clase N»; suelto se controla como cualquier otro número."""
    def sin_clases(m):
        return " ".join(x for x in re.findall(r"\d+(?:\.\d+)?", m.group(1)) if x not in nombres) or " "
    texto = _LISTA_CLASES.sub(sin_clases, texto)
    # Sólo se buscan los nombres que el texto contiene: con miles de clases, una expresión regular por cada una era lo más lento.
    presentes = [n for n in nombres if n and n in texto and not _es_numerico(n)]
    for n in sorted(presentes, key=len, reverse=True):
        texto = re.sub(r"(?<![\w.,])" + re.escape(n) + r"(?!\w|[.,]\d)", " ", texto)
    return texto


def numeros_del_texto(texto, nombres):
    """Valores numéricos del texto, sin contar los que forman parte de nombres de clases o conjuntos.
    Un número negativo conserva el signo, y una lista sin espacios («1,2,3») se separa en sus elementos."""
    res = []
    for m in re.finditer(r"(?<![\d.,])(?:(?<![\w)])([-−]))?(\d+(?:[.,]\d+)*)", _sin_nombres(texto, nombres)):
        if re.fullmatch(r"\d+(,\d+){2,}", m.group(2)):
            res.extend(m.group(2).split(","))
        else:
            res.append(("-" if m.group(1) else "") + m.group(2))
    return res


_UNIDADES = {"dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
             "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciséis": 16, "diecisiete": 17,
             "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiuno": 21, "veintiún": 21, "veintidós": 22,
             "veintitrés": 23, "veinticuatro": 24, "veinticinco": 25, "veintiséis": 26, "veintisiete": 27,
             "veintiocho": 28, "veintinueve": 29, "cien": 100, "ciento": 100, "mil": 1000,
             "segundo": 2, "segunda": 2, "tercer": 3, "tercero": 3, "tercera": 3, "cuarto": 4, "cuarta": 4,
             "quinto": 5, "quinta": 5, "sexto": 6, "sexta": 6, "séptimo": 7, "séptima": 7, "octavo": 8, "octava": 8,
             "noveno": 9, "novena": 9, "décimo": 10, "décima": 10}
_DECENAS = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90}
_SUMA = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9}
# Proporciones calculadas por el modelo: nunca figuran entre los hallazgos (regla 1 del prompt).
_CALCULOS = ("mitad", "doble", "triple", "cuádruple", "tercio", "cuarta parte")


def numerales_del_texto(texto, nombres):
    """Cantidades escritas con palabras: [(texto, valor)]. Los cálculos («la mitad», «el doble») tienen valor None."""
    t = _sin_nombres(texto, nombres).lower()
    res = [(m.group(0), None) for m in re.finditer(r"\b(?:" + "|".join(_CALCULOS) + r")\b", t)]
    for m in re.finditer(r"\b(" + "|".join(_DECENAS) + r")(?:\s+y\s+(" + "|".join(_SUMA) + r"))?\b", t):
        res.append((m.group(0), _DECENAS[m.group(1)] + _SUMA.get(m.group(2), 0)))
    t = re.sub(r"\b(?:" + "|".join(_DECENAS) + r")(?:\s+y\s+(?:" + "|".join(_SUMA) + r"))?\b", " ", t)
    t = re.sub(r"\bcuarta parte\b", " ", t)
    for m in re.finditer(r"\b(" + "|".join(sorted(_UNIDADES, key=len, reverse=True)) + r")\b", t):
        res.append((m.group(1), _UNIDADES[m.group(1)]))
    return res


@_una_vez
def _nombres_de(h):
    """Nombres de archivo, conjuntos y clases, tal como pueden aparecer en el texto."""
    nombres = {h["archivo"]}
    for g in h["grupos"]:
        nombres.update(_cortos(g))
        for p in g["pares"]:
            nombres.update([p["clase"], p["caracteristica"], p.get("caracteristica_legible")])
            for campo in ("transicion", "transicion_legible"):
                if p.get(campo):
                    nombres.update(x.strip() for x in p[campo].split(","))
    nombres.discard(None)
    nombres.update(_componentes(h))
    # Con tres variables o más, la comparación entre grupos nombra a la familia por el comienzo del nombre («E47_F3» para
    # «E47_F3_D» y «E47_F3_F»): también es un nombre, y su «47» no es una cifra.
    for c in [n for n in nombres if n.count("_") >= 2 and not _es_numerico(n)]:
        partes = c.split("_")
        nombres.update("_".join(partes[:i]) for i in range(2, len(partes)))
    return nombres


def verificar(textos, h, prompt_datos):
    """R-MS-12: todo número del texto debe figurar entre los hallazgos. Devuelve los que no figuran."""
    permitidos = valores_permitidos(h, prompt_datos)
    nombres = _nombres_de(h)
    # Los límites de un conjunto difuso (p. ej. 20,9 y 31,4 en Are3_20.9a31.4_) también son datos; los del nombre del archivo, no.
    for g in h["grupos"]:
        rango = _RANGO_CONJUNTO.match(g["conjunto"])
        resto = "_".join(rango.groups()) if rango else (g["conjunto"].split("_", 1)[-1] if "_" in g["conjunto"] else "")
        for x in re.findall(r"\d+(?:\.\d+)?", resto):
            permitidos.add(_norm(x))
    negativos = {_norm(p["valor_test"]) for g in prompt_datos["grupos"] for p in g["pares"]
                 if prompt_datos["mostrar_valor_test"] and str(p["valor_test"]).startswith("-")}
    ajenos = []
    for t in textos:
        for n in numeros_del_texto(t, nombres):
            if _norm(n) not in permitidos or (n.startswith("-") and _norm(n) not in negativos):
                ajenos.append(n)
        for palabra, valor in numerales_del_texto(t, nombres):
            if valor is None or round(float(valor), 6) not in permitidos:
                ajenos.append(palabra)
    return ajenos


def _cita(frase, nombre):
    return bool(nombre) and re.search(r"(?<![\w])" + re.escape(nombre) + r"(?![\w])", frase) is not None


def _cita_clase(frase, clase):
    """¿La frase cita esta clase? Un nombre numérico sólo se reconoce en la forma «clase N» (ver _LISTA_CLASES)."""
    if clase not in frase:                 # descarte rápido: con muchas clases, evita una expresión regular por cada una
        return False
    return clase in _clases_numericas_citadas(frase) if _es_numerico(clase) else _cita(frase, clase)


def _motivo_valores(ajenos):
    return "el texto contiene valores que no figuran en los hallazgos: " + ", ".join(sorted(set(ajenos)))


def _alias_clase(clase, variables):
    """Expresión que reconoce a una clase en un texto: su nombre («E47_F1») o su desglose en palabras («cepa E47 en la fecha F1»)."""
    alias = [r"(?<![\w])" + re.escape(clase) + r"(?![\w])"]      # con límites: «E47_F1» no es el comienzo de «E47_F10»
    if variables and len(variables) == len(clase.split("_")):
        alias.append(_alias_palabras(clase, variables))
    return "(?:" + "|".join(alias) + ")"


def _alias_palabras(clase, variables):
    """Expresión de una clase nombrada por sus variables, en el orden del nombre: «cepa E47 en la fecha F1», «cepa E47, fecha F1»."""
    trozos = [r"(?<![\w])" + re.escape(v.lower()) + r"\s+" + re.escape(p) + r"(?![\w])" for v, p in zip(variables, clase.split("_"))]
    return r"(?:[,;]?\s+(?:y\s+|en\s+|de\s+)?(?:la\s+|el\s+)?)".join(trozos)


def verificar_atribuciones(textos, h, pd):
    """Que cada valor test (y cada Cat.Class) esté junto a la clase a la que pertenece. R-MS-12 sólo controla que el número
    exista; esto controla que no se le atribuya a otra clase («E47_F1 … V-test: 13,353» cuando 13,353 es de FLO_F1).
    Cuenta como correcto que la clase dueña del número se nombre poco antes, por si el texto los enumera en lista."""
    variables = _variables(h)
    k = pd.get("n_grupos_detallados", len(h["grupos"]))
    por_v, por_cc, globales = {}, {}, set()
    for g, gp in zip(h["grupos"][:k], pd["grupos"]):
        for p, pp in zip(g["pares"], gp["pares"]):
            if _es_numerico(p["clase"]):
                continue                                           # un nombre numérico no se distingue de una cifra
            if pd.get("mostrar_valor_test"):
                por_v.setdefault(_norm(pp["valor_test"]), set()).add(p["clase"])
            por_cc.setdefault(_norm(pp["cat_class"]), set()).add(p["clase"])
            if pd.get("mostrar_class_cat"):      # Class.Cat y la razón de proporciones también son cifras de su clase: dos medidas pueden coincidir
                for campo in ("class_cat", "razon"):
                    por_cc.setdefault(_norm(pp[campo]), set()).add(p["clase"])
            globales.add(_norm(pp["global"]))
    clases = {c for s in list(por_v.values()) + list(por_cc.values()) for c in s}
    if not clases:
        return []
    alias = {c: re.compile(_alias_clase(c, variables), re.IGNORECASE) for c in clases}
    problemas = set()
    for t in textos:
        menciones = sorted((m.start(), c) for c, rx in alias.items() for m in rx.finditer(t))
        cortes = [m.end() for m in re.finditer(r"[.;:!?]\s", t)]
        # Los límites del nombre de un conjunto («Are1 (1,3 a 9,3)», «ent5 (6,4)») no son cifras de ninguna clase aunque coincidan con una.
        nombres_de_conjunto = [m.span() for m in re.finditer(r"\(\s*\d+(?:,\d+)?(?:\s+a\s+\d+(?:,\d+)?)?\s*\)", t)]
        for m in re.finditer(r"(?<![\d.,])\d+,\d+(?![\d])", t):
            if any(a <= m.start() < b for a, b in nombres_de_conjunto):
                continue
            num = _norm(m.group(0))
            duenos = por_v.get(num) or (por_cc.get(num) if num not in globales else None)
            if not duenos:
                continue
            inicio = max([c for c in cortes if c <= m.start()], default=0)
            fin = min([c for c in cortes if c > m.start()], default=len(t))
            previas = [(pos, c) for pos, c in menciones if pos < m.start()]
            en_la_oracion_antes = [c for pos, c in previas if pos >= inicio]
            en_la_oracion_despues = [c for pos, c in menciones if m.start() < pos < fin]
            if previas and previas[-1][1] in duenos:
                continue
            # «el 88,4 % de los valores de la cepa E47 en la fecha F3»: la cifra va delante de su clase, en la misma oración.
            if not en_la_oracion_antes and en_la_oracion_despues:
                if en_la_oracion_despues[0] in duenos:
                    continue
                atribuida = en_la_oracion_despues[0]
            elif previas:
                atribuida = previas[-1][1]
            else:
                continue                                              # no se nombra ninguna clase cerca: no se puede saber
            if any(c in duenos for pos, c in previas if m.start() - pos <= 250):      # lista de clases seguida de sus valores
                continue
            problemas.add(f"atribuye {m.group(0)} a {atribuida}, pero ese valor es de {', '.join(sorted(duenos))}")
    return sorted(problemas)


# Palabras con que un texto dice la intensidad de una asociación (las técnicas y las llanas del perfil novato). Un
# comparativo («la más fuerte», «menos fuerte») no dice el nivel, así que no cuenta.
_INTENSIDADES = {
    "fuerte": re.compile(r"(?<!más\s)(?<!menos\s)\bfuerte(?:s|mente)?\b|\bmucho\s+(?:más|menos)\s+de\s+lo\s+esperable|(?<!menos\s)\bmuy\s+marcad[ao]s?\b", re.IGNORECASE),
    "moderada": re.compile(r"\bmoderad(?:[ao]s?|amente)\b|\balgo\s+(?:más|menos)\s+de\s+lo\s+esperable", re.IGNORECASE),
    "débil": re.compile(r"\bd[eé]bil(?:es|mente)?\b|\bapenas\s+(?:más|menos)\s+de\s+lo\s+esperable", re.IGNORECASE),
}


def verificar_intensidad(parrafo, h, g):
    """Que el párrafo de un conjunto no le cambie la intensidad a una asociación: «algo más de lo esperable» (moderada) para una
    que es fuerte. Se mira oración por oración: la intensidad que se dice debe ser la de alguna de las clases que la oración
    nombra (o, si no nombra ninguna, la de alguna asociación del conjunto)."""
    nivel_de = {p["clase"]: p["intensidad"] for p in g["pares"] if p.get("intensidad")}
    if not nivel_de:
        return []
    variables = _variables(h)
    alias = {c: _detector_de_clase(c, variables) for c in nivel_de if (c if _es_numerico(c) else c.split("_")[0]) in parrafo}
    problemas = []
    for frase in re.split(r"(?<=[.;!?])\s+", parrafo):
        dichas = {nivel for nivel, rx in _INTENSIDADES.items() if rx.search(frase)}
        if not dichas:
            continue
        nombradas = [c for c, d in alias.items() if d(frase)] or list(nivel_de)
        reales = {nivel_de[c] for c in nombradas}
        for nivel in sorted(dichas - reales):
            de_quien = ", ".join(sorted(nombradas)) if len(nombradas) <= 3 else "este conjunto"
            problemas.append(f"dice que una asociación es {nivel}, y la de {de_quien} es {', '.join(sorted(reales))}")
    return problemas


def verificar_intensidad_dicha(parrafo, g, gp):
    """Que el párrafo diga, en palabras comunes, la intensidad de las asociaciones del conjunto (perfil sin valor test: la
    intensidad es lo único que le dice cuán marcada es cada una). Se pide cada nivel que haya en los pares detallados del
    conjunto; `gp` es el mismo conjunto en los datos del prompt, que traen la frase con que se dice cada intensidad."""
    problemas = []
    for nivel, rx in _INTENSIDADES.items():
        pares = [q for p, q in zip(g["pares"], gp["pares"]) if p.get("intensidad") == nivel]
        if pares and not rx.search(parrafo):
            frase = pares[0]["tipo_asociacion"]
            problemas.append(f"no dice la intensidad de {pares[0]['clase']}: debe decir «{frase[0].lower() + frase[1:]}»")
    return problemas


def verificar_afirmaciones(textos, h):
    """Lo que el texto afirma sobre las combinaciones que no figuran en el archivo: DaFu sólo exporta las que superan
    el umbral, así que, si no hay no significativas, no se puede decir que no existan ni dar un total de «posibles»."""
    problemas = set()
    copiadas = {m.group(0).lower() for t in textos for m in re.finditer(EJEMPLO_DEL_PROMPT, t, re.IGNORECASE)}
    if copiadas:
        # Si los propios datos hablan de transporte o de ingresos, esas palabras no vienen del ejemplo.
        propio = " ".join([str(x) for x in _nombres_de(h)] + _variables(h) + [str(h.get("contexto") or "")]).lower()
        if any(re.sub(r"\s+", " ", c) not in propio for c in copiadas):
            problemas.add("copia datos del ejemplo de estilo del prompt")
    if not h.get("n_no_significativas"):
        problemas |= {motivo for t in textos for patron, motivo in AFIRMACIONES_SIN_RESPALDO if re.search(patron, t, re.IGNORECASE)}
    # «Se apoya en pocos datos» sólo se puede decir de las asociaciones marcadas así (peso bajo, R-MI-11).
    if not any(p.get("peso_bajo") for g in h["grupos"] for p in g["pares"]):
        problemas |= {"dice que una asociación se apoya en pocos datos, y ninguna figura así" for t in textos
                      if re.search(r"\bpocos\s+datos\b", t, re.IGNORECASE)}
    return sorted(problemas)


def _cortos(g):
    """Nombres con los que un texto puede referirse al conjunto: completo, legible o sólo variable e índice («Are1»)."""
    legible = g.get("conjunto_legible") or g["conjunto"]
    return {g["conjunto"], legible, legible.split(" (")[0], _nombre_corto(g["conjunto"])}


def verificar_relaciones(textos, h, propio=None):
    """Segundo control (complementa R-MS-12): lo que el texto afirma sobre conjuntos y clases debe estar en los hallazgos.

    En cada frase, las clases citadas deben pertenecer a alguno de los conjuntos citados, y cada conjunto citado debe
    tener al menos una de las clases citadas. Además, «N clases», «N categorías» y «N asociaciones» deben coincidir
    con los conteos del análisis. `propio` es el conjunto del que habla el párrafo, si es de uno solo: una transición
    «con Are1 y Are3» en el párrafo de Are2 se refiere a Are2 aunque no lo nombre. Devuelve la lista de problemas encontrados.
    """
    grupos = h["grupos"]
    clases = set(p["clase"] for g in grupos for p in g["pares"])
    totales_asoc = {str(h["n_significativas"]), str(h["n_pares"])}
    if h.get("n_no_significativas"):
        totales_asoc.add(str(h["n_no_significativas"]))
    recurrentes = clases_recurrentes(h, 99)
    nums_comunes = _comunes(h, min(len(grupos), MAX_GRUPOS))[1]       # cantidades de la lectura cruzada que se le dieron al modelo
    conjuntos_de = {c: len(cs) for c, cs in recurrentes}
    por_tipo = {}
    for g in grupos:
        por_tipo[g["tipo"]] = por_tipo.get(g["tipo"], 0) + 1
    mejor = _mejor_conjunto(h)
    recorridos = {}
    if mejor and not any(_es_numerico(c) or "_" not in c for c in mejor):
        for c, (_, conj, _i, _v) in mejor.items():
            recorridos.setdefault(c.rsplit("_", 1)[0], set()).add(conj)
    problemas = []
    conocidos = clases | {x for g in grupos for x in _cortos(g)} | {g["conjunto"] for g in grupos}
    for t in textos:
        # Un nombre compuesto («FLO_F4») que no es una clase ni un conjunto del análisis es un nombre inventado.
        for nombre in sorted(set(re.findall(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b", t))):
            if nombre not in conocidos and nombre not in str(h.get("archivo", "")) and not any(nombre in c for c in conocidos if "_" in c):
                problemas.append(f"«{nombre}» no es una clase ni un conjunto del análisis")
        for frase in re.split(r"(?<=[.!?;:])\s+|\n", t):
            citados = [g for g in grupos if any(_cita(frase, n) for n in _cortos(g))]
            en_transicion = citados + [propio] if propio is not None and not any(g is propio for g in citados) else citados
            if "transici" in frase.lower() and len(en_transicion) >= 2:
                for g in en_transicion:                # cada conjunto citado debe ser contiguo a otro de los citados
                    otros = {o["conjunto"] for o in en_transicion if o is not g}
                    if not any(set(x.strip() for x in (p.get("transicion") or "").split(",")) & otros for p in g["pares"]):
                        problemas.append(f"no hay transición entre {g.get('conjunto_legible') or g['conjunto']} y los demás conjuntos citados")
            # Recorrido de una familia: los conjuntos que se le atribuyen deben ser los de sus clases.
            bases = [f for f in recorridos if f in frase and _cita(frase, f)]
            if len(bases) == 1 and citados and re.search(r"familia|recorr|transita|pasa(?:ndo)?\b|trayectoria", frase, re.IGNORECASE):
                ajenos = [g for g in citados if (g.get("conjunto_legible") or g["conjunto"]) not in recorridos[bases[0]]]
                if ajenos and not re.search(r"\b(?:a diferencia|en cambio|mientras|frente a|no\s+se)\b", frase, re.IGNORECASE):
                    problemas.append(f"la familia {bases[0]} no recorre " + ", ".join(g.get("conjunto_legible") or g["conjunto"] for g in ajenos))
            cl = [c for c in clases if _cita_clase(frase, c)]
            # En una oración sobre transiciones se nombra al conjunto vecino junto a clases que no son suyas: sólo se controla la transición.
            if citados and cl and not re.search(r"transici|contigu|vecin", frase, re.IGNORECASE):
                propias = set(p["clase"] for g in citados for p in g["pares"])
                for c in cl:
                    if c not in propias:
                        problemas.append(f"la clase {c} no se asocia con " + ", ".join(g.get("conjunto_legible") or g["conjunto"] for g in citados))
                for g in citados:
                    if not set(p["clase"] for p in g["pares"]) & set(cl):
                        problemas.append(f"el conjunto {g.get('conjunto_legible') or g['conjunto']} no se asocia con ninguna de las clases citadas junto a él")
            for n in re.findall(r"(\d+)\s+conjuntos?", frase):
                if len(cl) == 1 and cl[0] in conjuntos_de:      # «la clase X aparece en N conjuntos»
                    validos = {str(conjuntos_de[cl[0]]), str(len(grupos))}
                else:
                    validos = {str(len(grupos))} | {str(c) for c in conjuntos_de.values()} | {str(c) for c in por_tipo.values()}
                if n not in validos:
                    problemas.append(f"«{n} conjuntos» no coincide con los datos del análisis")
            for n, palabra, resto in re.findall(r"(\d+)\s+(clases?|categor[ií]as?|asociaci[oó]n(?:es)?)(\s+\w+(?:\s+\w+)?)?", frase):
                if palabra.startswith("clase"):
                    if re.match(r"\s+comparten?", resto):          # «las 3 clases comparten F1»: cantidad de la lectura cruzada
                        if n not in nums_comunes and n not in {str(len(recurrentes)), str(len(clases_recurrentes(h)))}:
                            problemas.append(f"«{n} {palabra}{resto}»: no coincide con las clases que comparten un nivel")
                    elif re.match(r"\s+(recurrentes?|que\s+(se\s+repiten?|m[aá]s))", resto):
                        if n not in {str(len(recurrentes)), str(len(clases_recurrentes(h)))}:
                            problemas.append(f"«{n} {palabra}{resto}»: hay {len(recurrentes)} clases que se repiten")
                    elif (n != str(h["n_clases"]) and n not in {str(g.get("n_clases")) for g in citados} and n not in nums_comunes
                          and not (propio is not None and n == str(propio.get("n_clases")))):      # «este conjunto reúne 3 clases»
                        problemas.append(f"«{n} {palabra}»: el análisis tiene {h['n_clases']} clases")
                elif palabra.startswith("categor") and n != str(h["n_categorias"]):
                    problemas.append(f"«{n} {palabra}»: el análisis tiene {h['n_categorias']} categorías")
                elif palabra.startswith("asoc"):
                    # Con un conjunto citado, el número debe ser el de ese conjunto (o un total del análisis).
                    propios = grupos if (not citados or re.search(r"\b(?:dem[aá]s|restantes|otros|cada\s+un[oa])\b", frase, re.IGNORECASE)) else citados
                    validos = totales_asoc | {str(g["n_pares"]) for g in propios}
                    validos |= {str(sum(p["clase"] == c for g in grupos for p in g["pares"])) for c in cl}
                    if n not in validos:
                        problemas.append(f"«{n} {palabra}» no coincide con los conteos del análisis")
    return sorted(set(problemas))


def _leer_respuesta(crudo):
    """JSON de la respuesta del modelo; tolera un bloque ```json o texto antes y después del objeto."""
    t = (crudo or "").strip()
    try:
        resp = json.loads(t, strict=False)
    except json.JSONDecodeError:
        i, j = t.find("{"), t.rfind("}")
        if i < 0 or j <= i:
            raise ValueError("la respuesta del modelo no es un JSON válido")
        try:
            resp = json.loads(t[i:j + 1], strict=False)
        except json.JSONDecodeError:
            raise ValueError("la respuesta del modelo no es un JSON válido")
    if not isinstance(resp, dict):
        raise ValueError("la respuesta del modelo no es un objeto JSON con las secciones")
    return resp


def _mensaje_error(e, modelo):
    """Mensaje en español para los fallos habituales (RNF-6)."""
    nombre = type(e).__name__
    if nombre in ("ConnectionError", "ConnectError") or isinstance(e, ConnectionError):
        if llm.proveedor() == "gemini":
            return "no se pudo conectar con Gemini; revise la conexión a internet"
        return "no se pudo conectar con Ollama; ábralo o ejecute «ollama serve»"
    if nombre == "ResponseError" and getattr(e, "status_code", None) == 404:
        return f"el modelo {modelo} no está descargado; ejecute «ollama pull {modelo}»"
    if "Timeout" in nombre or isinstance(e, TimeoutError):
        return "el modelo tardó demasiado en responder"
    if nombre == "ModuleNotFoundError":
        return f"falta la biblioteca de Python «{getattr(e, 'name', '')}»; instálela con pip"
    if isinstance(e, ValueError):
        return str(e)
    return f"error inesperado al redactar ({nombre})"


def redactar_sintesis(ruta_hallazgos, ruta_kb, modelo=None, generar=None):
    """Redacta la síntesis y devuelve la ruta de sintesis.json (RF-MS-11).

    `generar` permite reemplazar la llamada al modelo en las pruebas.
    """
    global _MEMO
    _MEMO = {}
    try:
        return _redactar(ruta_hallazgos, ruta_kb, modelo, generar)
    finally:
        _MEMO = None


def _redactar(ruta_hallazgos, ruta_kb, modelo, generar):
    proveedor = "simulado" if generar else llm.proveedor()
    modelo = modelo or llm.modelo_por_defecto()
    generar = generar or (lambda prompt: llm.generar_texto(prompt, modelo))
    with open(ruta_hallazgos, encoding="utf-8") as f:
        h = _expandir_resto(json.load(f))
    ruta_s = os.path.join(os.path.dirname(ruta_hallazgos), "sintesis.json")
    ids = [p["id"] for g in h["grupos"] for p in g["pares"]]
    estado, aviso, secciones, rechazados = "redactada", "", [], []
    try:
        pd = datos_prompt(h, ruta_kb)
        prompt = armar_prompt(h, pd)
        with open(os.path.join(os.path.dirname(ruta_hallazgos), "prompt.txt"), "w", encoding="utf-8") as f:
            f.write(prompt)
        resp = None
        for intento in range(2):                        # una sola consulta; un reintento si viene vacía, incompleta o no es JSON
            crudo = generar(prompt)                     # un error del proveedor no se reintenta aquí: lo resuelve llm.py
            try:
                resp = _leer_respuesta(crudo)
            except ValueError:
                if intento == 1:
                    raise
                continue
            if all(_texto(resp, s) for s in SECCIONES if not (s == "S2" and not h["grupos"])):
                break
            if intento == 1:
                resp = resp or {}
        textos, faltan, respaldo = {}, [], []
        for s in SECCIONES:
            if s == "S2" and not h["grupos"]:
                textos[s] = h.get("texto_s2") or "No hay asociaciones significativas."
                continue
            t = _texto(resp, s)
            if t:
                textos[s] = t.replace(MARCADOR_ARCHIVO, h["archivo"])
            else:
                faltan.append(s)
        if faltan:
            raise ValueError("la respuesta del modelo no trae texto en las secciones " + ", ".join(faltan))
        if h["grupos"]:
            def reintentar(fallidos):
                """Segunda consulta, sólo si algún párrafo de S2 no verificó: se le dice al modelo cuáles y por qué."""
                pedido = ("\n\nCORRECCIÓN: en tu respuesta anterior, estos párrafos de S2 no pasaron el control de datos. "
                          "Devuelve otra vez el JSON completo, con esos párrafos redactados de nuevo sin ese error "
                          "(en el párrafo de un conjunto no nombres otros conjuntos, salvo sus transiciones):\n"
                          + "\n".join(f"- Conjunto {c}: {'; '.join(m[:3])}" for c, m in fallidos))
                try:
                    nuevo = _texto(_leer_respuesta(generar(prompt + pedido.replace(h["archivo"], MARCADOR_ARCHIVO))), "S2")
                except Exception:      # el reintento es una mejora: si falla, queda el párrafo armado por código
                    return None
                return nuevo.replace(MARCADOR_ARCHIVO, h["archivo"]) if nuevo else None
            textos["S2"], respaldo, rechazados = _hallazgos_por_grupo(textos["S2"], h, pd, reintentar)
        problemas = []
        for sid in ("S1", "S3"):                        # cada sección por separado, para registrar qué texto falló y por qué
            t = _pulir(_podar_s1(textos[sid], h) if sid == "S1" else _podar_s3(textos[sid], h), h, pd)
            t, quitadas = _sin_oraciones_que_no_verifican(t, h, pd)
            textos[sid] = t
            rechazados.extend(dict(seccion=sid, conjunto="", texto=f, motivos=m) for f, m in quitadas)
            ajenos = verificar([t], h, pd)
            rel = verificar_relaciones([t], h) + verificar_atribuciones([t], h, pd)
            afirm = verificar_afirmaciones([t], h)
            motivos = ([_motivo_valores(ajenos)] if ajenos else []) + rel + afirm
            if motivos:
                rechazados.append(dict(seccion=sid, conjunto="", texto=t, motivos=motivos))
            problemas.append((ajenos, rel, afirm))
        ajenos = [x for p in problemas for x in p[0]]
        rel = sorted({x for p in problemas for x in p[1]})
        afirm = sorted({x for p in problemas for x in p[2]})
        if ajenos:
            estado, aviso = "no verificada", _motivo_valores(ajenos)
        if rel:
            estado = "no verificada"
            aviso = (aviso + "; " if aviso else "") + "el texto atribuye relaciones que no figuran en los hallazgos: " + "; ".join(rel)
        if afirm:
            estado = "no verificada"
            aviso = (aviso + "; " if aviso else "") + "el texto afirma algo que el archivo no permite saber: " + "; ".join(afirm)
        if respaldo and estado == "redactada":
            estado = "parcialmente redactada"
            motivo_de = {r["conjunto"]: r["motivos"][0] for r in reversed(rechazados) if r["seccion"] == "S2"}
            aviso = (f"En {len(respaldo)} de {len(h['grupos'])} conjuntos el texto del modelo no verificó y se informa la versión estructurada: "
                     + ", ".join(f"{c} ({motivo_de[c]})" if c in motivo_de else c for c in respaldo))
        nombres = {s["id"]: s["nombre"] for s in h["secciones"]}
        for sid in SECCIONES:
            t = textos[sid]
            usados = [] if sid == "S1" else ids         # RF-MS-10: la descripción general no se apoya en un par concreto
            if sid == "S3":
                citados = [p["id"] for g in h["grupos"] for p in g["pares"]
                           if any(_cita(t, n) for n in _cortos(g)) or _cita_clase(t, p["clase"])]
                usados = citados or ids
            secciones.append(dict(id=sid, nombre=nombres[sid], texto=t, interpretaciones=usados))
    except Exception as e:  # modelo no disponible, respuesta no JSON, sección faltante
        estado, aviso, secciones = "error", _mensaje_error(e, modelo), []

    s4 = next(s for s in h["secciones"] if s["id"] == "S4")
    secciones.append(dict(id="S4", nombre=s4["nombre"], texto="\n".join(l["texto"] for l in h["limitaciones"]),
                          interpretaciones=[]))
    with open(ruta_s, "w", encoding="utf-8") as f:
        json.dump(dict(estado=estado, aviso=aviso, modelo=modelo, proveedor=proveedor,    # RNF-2: registro de qué redactó el texto
                       fecha=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), secciones=secciones,
                       rechazados=rechazados), f, ensure_ascii=False, indent=2)
    return ruta_s
