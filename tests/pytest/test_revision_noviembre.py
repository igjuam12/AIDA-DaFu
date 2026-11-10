"""Pruebas de las correcciones de la revisión del 04/11/2026. Ninguna usa la red ni una clave real."""
import importlib.util
import io
import json
import os
import re
import sys
import urllib.error

import pytest

AIDA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(AIDA, "python"))
import redaccion  # noqa: E402

KB = os.path.join(AIDA, "kb", "base_conocimiento.json")


def _h(**cambios):
    """Dos conjuntos y tres clases; la clase 9002 aparece en los dos conjuntos."""
    par = lambda i, c, v, cat: {"id": i, "clase": c, "caracteristica": cat, "valor_test": v, "p_valor": 0.0, "p_texto": "p < 0,01",
                                "class_cat": 10.0, "cat_class": 40.0, "global": 20.0, "razon": 2.0, "regla": "R-MI-1",
                                "significacion": "altamente significativo", "peso_bajo": False, "transicion": ""}
    h = {"perfil": "intermedio", "instruccion_registro": "Registro.", "escalado": True, "descripcion": "filas", "archivo": "datos2024_v18.txt",
         "n_pares": 4, "n_clases": 3, "n_categorias": 2, "n_significativas": 4, "n_no_significativas": 0, "n_transiciones": 0, "minimo_clases": 4,
         "secciones": [{"id": f"S{k}", "nombre": f"Sección {k}", "contenido": "", "debe_incluir": []} for k in range(1, 5)],
         "limitaciones": [{"id": "AD3", "texto": "Limitación."}],
         "grupos": [{"conjunto": "Oact", "fuerza": 12.5, "n_pares": 3, "n_clases": 3, "tipo": "singularidad", "posicion": 1,
                     "pares": [par("FIL-P1", "9001", 5.5, "Oact"), par("FIL-P2", "9002", 4.0, "Oact"), par("FIL-P3", "9003", 3.0, "Oact")]},
                    {"conjunto": "SoCap", "fuerza": 3.25, "n_pares": 1, "n_clases": 1, "tipo": "singularidad", "posicion": 2,
                     "pares": [par("FIL-P4", "9002", 3.25, "SoCap")]}]}
    h.update(cambios)
    return h


def _llm(monkeypatch, abrir=None):
    spec = importlib.util.spec_from_file_location("aida_llm_r", os.path.join(os.path.dirname(redaccion.__file__), "llm.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setenv("AIDA_PROVEEDOR", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "SECRETA")
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    if abrir:
        monkeypatch.setattr(m.urllib.request, "urlopen", abrir)
    return m


class R(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): pass


def _ok(texto="{}", motivo="STOP"):
    return R(json.dumps({"candidates": [{"content": {"parts": [{"text": texto}]}, "finishReason": motivo}]}).encode())


# ─── R-MS-12: el verificador ─────────────────────────────────────────────────

def _ajenos(texto, h=None):
    h = h or _h()
    return redaccion.verificar([texto], h, redaccion.datos_prompt(h))


@pytest.mark.parametrize("texto", ["Hay siete grupos.", "Aparece en treinta y dos casos.", "Representa la mitad.", "Es el doble que en 9001."])
def test_las_cantidades_con_palabras_se_controlan(texto):
    assert _ajenos(texto)


def test_las_cantidades_con_palabras_que_figuran_en_los_datos_se_aceptan():
    assert _ajenos("Hay tres clases y dos categorías.") == []


def test_una_y_uno_no_son_cantidades():
    assert _ajenos("Una asociación de uno de los conjuntos.") == []


def test_el_punto_de_miles_no_se_confunde_con_un_decimal():
    h = _h()
    h["grupos"][0]["pares"][0]["cat_class"] = 45.0
    assert _ajenos("Hay 45.000 casos.", h) == ["45.000"]
    assert _ajenos("Hay 45,0 casos.", h) == []


def test_un_nombre_numerico_no_tapa_otros_numeros():
    h = _h()
    h["grupos"][0]["pares"][0]["clase"] = "2"
    assert "42" in _ajenos("En 2 hay 42 casos.", h)
    assert "2,5" in _ajenos("Un valor de 2,5.", h)


def test_los_numeros_del_nombre_del_archivo_no_son_datos():
    assert _ajenos("En 2024 hubo 18 casos.") == ["2024", "18"]


def test_el_numero_de_orden_del_conjunto_no_es_un_dato():
    h = _h()
    h["grupos"][0]["conjunto"] = "Are7_20.9a31.4_"
    assert _ajenos("Hay 7 casos.", h) == ["7"]
    assert _ajenos("Are7 va de 20,9 a 31,4.", h) == []


def test_numero_pegado_a_letras_se_detecta():
    assert _ajenos("El índice x99 es alto.") == ["99"]


def test_un_negativo_inventado_se_rechaza_y_uno_real_no():
    assert _ajenos("V de -5,500.") == ["-5,500"]
    h = _h()
    h["grupos"][0]["pares"][0]["valor_test"] = -5.5
    assert _ajenos("V de -5,500.", h) == []


def test_lista_sin_espacios_se_separa():
    assert _ajenos("Conjuntos 1,2,3 y más.") == []
    assert _ajenos("Conjuntos 1,2,9 y más.") == ["9"]


# ─── Relaciones ──────────────────────────────────────────────────────────────

def test_cantidad_de_clases_recurrentes_no_es_falso_positivo():
    assert redaccion.verificar_relaciones(["Hay 1 clases recurrentes."], _h()) == []
    assert redaccion.verificar_relaciones(["Hay 5 clases recurrentes."], _h())


def test_asociaciones_de_un_conjunto_citado():
    assert redaccion.verificar_relaciones(["Oact tiene 3 asociaciones."], _h()) == []
    assert redaccion.verificar_relaciones(["SoCap tiene 3 asociaciones."], _h())     # 3 son las de Oact


def test_conjuntos_de_una_clase_citada():
    assert redaccion.verificar_relaciones(["La clase 9002 aparece en 2 conjuntos."], _h()) == []
    assert redaccion.verificar_relaciones(["La clase 9002 aparece en 1 conjuntos."], _h())


def test_clases_de_un_conjunto_citado():
    assert redaccion.verificar_relaciones(["SoCap se asocia con 1 clases."], _h()) == []


def test_cantidad_por_tipo_de_patron_se_acepta():
    h = _h()
    h["grupos"].append(dict(h["grupos"][1], conjunto="Otra", tipo="patrón constante"))
    assert redaccion.verificar_relaciones(["Hay 2 conjuntos singulares."], h) == []
    assert redaccion.verificar(["Hay 2 singularidades."], h, redaccion.datos_prompt(h)) == []


# ─── Prompt y privacidad ─────────────────────────────────────────────────────

def test_el_prompt_es_el_del_modelado_y_trae_los_patrones():
    p = redaccion.armar_prompt(_h())
    assert p.startswith("Eres AIDA, un asistente experto en análisis de datos estadísticos.")
    assert "REGLAS ESTRICTAS" in p and "DATOS VALIDADOS (Módulo MI)" in p and "Patrones detectados (ordenados por importancia)" in p
    assert "Redacta la síntesis ahora:" in p and "Perfil del lector: INTERMEDIO" in p
    assert "Conjunto Oact" in p and "9001" in p and p.index("Conjunto Oact") < p.index("Conjunto SoCap")


def test_el_prompt_trae_los_tipos_de_patron_y_las_clases_que_se_repiten():
    p = redaccion.armar_prompt(_h())
    assert "Conjuntos por tipo de patrón" not in p            # los conjuntos del caso tienen todos el mismo tipo: no informa nada
    h = _h(); h["grupos"][0]["tipo"] = "patrón constante"
    q = redaccion.armar_prompt(h)
    assert "Conjuntos por tipo de patrón" in q and "- patrón constante: 1 conjunto" in q
    assert "- clase 9002 se asocia con Oact y SoCap" in p            # la lectura cruzada por clase reemplaza a la lista de clases que se repiten


def test_el_nombre_del_archivo_no_viaja_al_modelo_y_vuelve_en_el_texto(tmp_path):
    h = _h(texto_s2="Resultados.")
    ruta = tmp_path / "hallazgos.json"
    ruta.write_text(json.dumps(h, ensure_ascii=False), encoding="utf-8")
    vistos = []

    def generar(prompt):
        vistos.append(prompt)
        return _resp(S1=f"Se analizó {redaccion.MARCADOR_ARCHIVO}.")
    s = json.load(open(redaccion.redactar_sintesis(str(ruta), KB, generar=generar), encoding="utf-8"))
    assert s["estado"] == "redactada"
    assert all("datos2024" not in p for p in vistos)
    assert "datos2024_v18.txt" in s["secciones"][0]["texto"]
    assert s["proveedor"] == "simulado" and s["fecha"]


def test_el_novato_no_ve_valor_test_en_ningun_prompt():
    h = _h(perfil="novato", visibles=dict(valor_test=False, p_valor=False, class_cat=False, razon=False))
    p = redaccion.armar_prompt(h).lower()
    assert "valor test" not in p and "v-test" not in p and "fuerza" not in p and "5,500" not in p


def test_no_significativas_se_informan_como_cantidad():
    h = _h(n_no_significativas=6, n_pares=10)
    assert "no significativas: 6" in redaccion.armar_prompt(h)
    assert _ajenos("Hay 6 no significativas.", h) == []
    assert _ajenos("Hay 6 no significativas.") == ["6"]


# ─── Redacción ───────────────────────────────────────────────────────────────

def _resp(**secciones):
    """Respuesta del modelo: una sola con las tres secciones. S2 trae un párrafo por conjunto de `_h()`."""
    base = {"S1": "General.",
            "S2": "Hallazgos para el conjunto Oact: las clases 9001, 9002 y 9003.\n\nHallazgos para el conjunto SoCap: la clase 9002.",
            "S3": "Conclusión."}
    base.update(secciones)
    return json.dumps(base)


def _sintesis(tmp_path, generar, h=None):
    ruta = tmp_path / "hallazgos.json"
    ruta.write_text(json.dumps(h or _h(texto_s2="Resultados."), ensure_ascii=False), encoding="utf-8")
    return json.load(open(redaccion.redactar_sintesis(str(ruta), KB, generar=generar), encoding="utf-8"))


def test_json_invalido_se_reintenta(tmp_path):
    n = []

    def generar(prompt):
        n.append(1)
        return "no es json" if len(n) == 1 else _resp()
    s = _sintesis(tmp_path, generar)
    assert s["estado"] == "redactada" and len(n) == 2      # una sola consulta; el primer intento falla y se reintenta


def test_error_del_proveedor_no_se_reintenta_aca(tmp_path):
    n = []

    def generar(prompt):
        n.append(1)
        raise ValueError("Gemini rechazó la clave de API")
    s = _sintesis(tmp_path, generar)
    assert s["estado"] == "error" and "rechazó" in s["aviso"] and len(n) == 1


def test_trazabilidad_de_s1_y_s3(tmp_path):
    s = _sintesis(tmp_path, lambda prompt: _resp(S3="Destaca SoCap."))
    assert s["secciones"][0]["interpretaciones"] == []
    assert s["secciones"][2]["interpretaciones"] == ["FIL-P4"]


def test_s3_no_confunde_conjuntos_por_prefijo(tmp_path):
    h = _h(texto_s2="Resultados.")
    h["grupos"][0]["conjunto"] = "Are10"
    h["grupos"][1]["conjunto"] = "Are1"

    s = _sintesis(tmp_path, lambda prompt: _resp(S2="Hallazgos para el conjunto Are10: la clase 9001.\n\nHallazgos para el conjunto Are1: la clase 9002.", S3="Destaca Are10."), h)
    assert s["secciones"][2]["interpretaciones"] == ["FIL-P1", "FIL-P2", "FIL-P3"]


def test_hallazgos_incompletos_dan_error_en_espanol_y_conservan_s4(tmp_path):
    h = _h()
    del h["grupos"][0]["pares"][0]["significacion"]
    s = _sintesis(tmp_path, lambda p: "{}", h)
    assert s["estado"] == "error" and "error inesperado" in s["aviso"]
    assert s["secciones"][-1]["id"] == "S4"


def test_num_igual_que_en_r():
    assert redaccion.num(-0.0004, 2) == "0,00"
    assert redaccion.num(0, 2) == "0,00"
    assert redaccion.num(1.0005, 3) == "1,001"     # .aida_num suma 1e-9 antes de redondear
    assert redaccion.num(None, 2) == "no calculable"


def test_fuerza_infinita_se_informa_como_en_r():
    h = _h()
    h["grupos"][0]["fuerza"] = None
    h["grupos"][0]["fuerza_txt"] = "infinito"
    assert "fuerza infinito" in redaccion.armar_prompt(h)
    assert _ajenos("Sin números.", h) == []


# ─── Gemini ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("codigo,frag", [(400, "no es válida"), (401, "rechazó la clave"), (403, "rechazó la clave"), (404, "no existe"), (418, "418")])
def test_gemini_errores_no_reintentables(monkeypatch, codigo, frag):
    n = []

    def abrir(req, timeout=None):
        n.append(1)
        raise urllib.error.HTTPError(req.full_url, codigo, "x", {}, None)
    with pytest.raises(ValueError, match=frag) as e:
        _llm(monkeypatch, abrir).generar_texto("x")
    assert len(n) == 1 and "SECRETA" not in str(e.value)


@pytest.mark.parametrize("codigo", [500, 502, 503, 504])
def test_gemini_5xx_agota_los_reintentos(monkeypatch, codigo):
    n = []

    def abrir(req, timeout=None):
        n.append(1)
        raise urllib.error.HTTPError(req.full_url, codigo, "x", {}, None)
    with pytest.raises(ValueError, match="no está disponible"):
        _llm(monkeypatch, abrir).generar_texto("x")
    assert len(n) == 5          # el intento inicial y cuatro reintentos


def test_gemini_503_muestra_el_mensaje_de_google_sin_la_clave(monkeypatch):
    cuerpo = json.dumps({"error": {"message": "The model is overloaded. Please try again later. SECRETA"}}).encode()

    def abrir(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 503, "x", {}, io.BytesIO(cuerpo))     # cada intento recibe su propia respuesta
    with pytest.raises(ValueError, match="overloaded") as e:
        _llm(monkeypatch, abrir).generar_texto("x")
    assert "SECRETA" not in str(e.value) and "***" in str(e.value)


def test_gemini_saturado_prueba_el_modelo_de_respaldo(monkeypatch):
    modelos = []
    monkeypatch.setenv("AIDA_MODELO_RESPALDO", "modelo-respaldo")

    def abrir(req, timeout=None):
        modelos.append(req.full_url)
        if "modelo-respaldo" not in req.full_url:
            raise urllib.error.HTTPError(req.full_url, 503, "x", {}, None)
        return _ok()
    assert _llm(monkeypatch, abrir).generar_texto("x") == "{}"
    assert len(modelos) == 6 and "modelo-respaldo" in modelos[-1]       # 5 intentos con el principal y 1 con el respaldo


def test_gemini_429_con_espera_larga_no_reintenta(monkeypatch):
    n = []

    def abrir(req, timeout=None):
        n.append(1)
        raise urllib.error.HTTPError(req.full_url, 429, "x", {"Retry-After": "3600"}, None)
    with pytest.raises(ValueError, match="cuota"):
        _llm(monkeypatch, abrir).generar_texto("x")
    assert len(n) == 1


def test_gemini_429_respeta_la_espera_pedida(monkeypatch):
    esperas, n = [], []

    def abrir(req, timeout=None):
        n.append(1)
        if len(n) == 1:
            raise urllib.error.HTTPError(req.full_url, 429, "x", {"Retry-After": "12"}, None)
        return _ok()
    m = _llm(monkeypatch, abrir)
    monkeypatch.setattr(m.time, "sleep", esperas.append)
    assert m.generar_texto("x") == "{}" and esperas == [12]


@pytest.mark.parametrize("motivo", ["SAFETY", "RECITATION", "OTHER"])
def test_gemini_no_acepta_texto_de_una_respuesta_cortada(monkeypatch, motivo):
    with pytest.raises(ValueError, match=motivo):
        _llm(monkeypatch, lambda req, timeout=None: _ok('{"S1": "parcial"}', motivo)).generar_texto("x")


def test_gemini_max_tokens(monkeypatch):
    with pytest.raises(ValueError, match="límite de tokens"):
        _llm(monkeypatch, lambda req, timeout=None: _ok('{"S1": "cort', "MAX_TOKENS")).generar_texto("x")


def test_gemini_bloqueada(monkeypatch):
    with pytest.raises(ValueError, match="SAFETY"):
        _llm(monkeypatch, lambda req, timeout=None: R(json.dumps({"promptFeedback": {"blockReason": "SAFETY"}}).encode())).generar_texto("x")


def test_gemini_cuerpo_que_no_es_json(monkeypatch):
    with pytest.raises(ValueError, match="no se puede leer"):
        _llm(monkeypatch, lambda req, timeout=None: R(b"<html>")).generar_texto("x")


def test_gemini_sin_conexion_y_tiempo_agotado(monkeypatch):
    def caso(exc):
        def abrir(req, timeout=None):
            raise exc
        return _llm(monkeypatch, abrir)
    with pytest.raises(ConnectionError, match="conexión a internet"):
        caso(urllib.error.URLError("sin red")).generar_texto("x")
    with pytest.raises(ConnectionError, match="conexión a internet"):
        caso(ConnectionResetError()).generar_texto("x")
    with pytest.raises(TimeoutError, match="tardó"):
        caso(TimeoutError()).generar_texto("x")
    with pytest.raises(TimeoutError, match="tardó"):
        caso(urllib.error.URLError(TimeoutError())).generar_texto("x")


def test_sintesis_con_gemini_caido_no_filtra_la_clave(tmp_path, monkeypatch):
    def abrir(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 401, "x", {}, None)
    m = _llm(monkeypatch, abrir)
    monkeypatch.setattr(redaccion, "llm", m)
    ruta = tmp_path / "hallazgos.json"
    ruta.write_text(json.dumps(_h(), ensure_ascii=False), encoding="utf-8")
    s = json.load(open(redaccion.redactar_sintesis(str(ruta), KB), encoding="utf-8"))
    assert s["estado"] == "error" and s["proveedor"] == "gemini"
    assert "SECRETA" not in json.dumps(s, ensure_ascii=False)


def test_proveedor_invalido_se_informa(monkeypatch):
    m = _llm(monkeypatch)
    monkeypatch.setenv("AIDA_PROVEEDOR", "chatgpt")
    with pytest.raises(ValueError, match="AIDA_PROVEEDOR"):
        m.generar_texto("x")


def test_gemini_usa_temperatura_cero(monkeypatch):
    visto = {}

    def abrir(req, timeout=None):
        visto.update(json.loads(req.data)["generationConfig"])
        return _ok()
    _llm(monkeypatch, abrir).generar_texto("x")
    assert visto["temperature"] == 0 and visto["seed"] == 42


# ─── .env ────────────────────────────────────────────────────────────────────

def test_env_variantes(tmp_path, monkeypatch):
    m = _llm(monkeypatch)
    nombres = ("A_K", "A_S", "A_E", "A_C", "A_X", "A_V", "A_B")
    for v in nombres:
        monkeypatch.setenv(v, "")      # monkeypatch las restaura al terminar
        os.environ.pop(v)
    monkeypatch.setenv("A_V", "")       # variable vacía en el entorno: vale la del archivo
    (tmp_path / "x.env").write_bytes(
        "﻿A_K='abc'\nlinea sin igual\n  A_S = \"x y\"  \nA_E=a=b\nA_C=valor # comentario\nexport A_X=exportada\nA_V=del_archivo\n#A_B=no\n".encode("utf-8"))
    m.cargar_env(str(tmp_path / "x.env"))
    assert [os.environ[v] for v in nombres[:6]] == ["abc", "x y", "a=b", "valor", "exportada", "del_archivo"]
    assert "A_B" not in os.environ


def test_aida_env_indica_otro_archivo(tmp_path, monkeypatch):
    m = _llm(monkeypatch)
    monkeypatch.delenv("AIDA_MODELO", raising=False)
    (tmp_path / "otro.env").write_text("AIDA_MODELO=gemini-otro\n", encoding="utf-8")
    monkeypatch.setenv("AIDA_ENV", str(tmp_path / "otro.env"))
    assert m.modelo_por_defecto() == "gemini-otro"
    monkeypatch.setenv("AIDA_MODELO", "gemini-otro")   # que monkeypatch la restaure


# ─── Base de conocimiento ────────────────────────────────────────────────────

def test_json_y_cypher_coinciden():
    kb = json.load(open(KB, encoding="utf-8"))
    cy = open(os.path.join(AIDA, "kb", "AIDA_frames_A10.cypher"), encoding="utf-8").read()
    textos = [p["texto"] for p in kb["plantillas"]]
    for a in kb["advertencias"].values():
        textos += [a["texto"]] + ([a["texto_novato"]] if "texto_novato" in a else [])
    for s in kb["secciones_sintesis"]:
        textos += [s["contenido"]] + ([s["contenido_novato"]] if "contenido_novato" in s else [])
    textos += [m["definicion"] for m in kb["magnitudes"].values()]
    for t in textos:
        assert t in cy, t
    for p in kb["plantillas"]:
        assert f"{{id: '{p['id']}'}}" in cy, p["id"]


def test_textos_del_novato_sin_jerga():
    kb = json.load(open(KB, encoding="utf-8"))
    novato = [p["texto"] for p in kb["plantillas"] if p["perfil"] == "novato"]
    novato += [a["texto_novato"] for a in kb["advertencias"].values() if "texto_novato" in a]
    for t in novato:
        assert not re.search(r"valor test|p-valor|\[V\]|\[p\]|\[regla\]|hipergeom", t, re.IGNORECASE), t
