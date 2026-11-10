import importlib, json, os, sys, types
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
import test_redaccion as T
redaccion, H, KB, escribir = T.redaccion, T.H, T.KB, T.escribir


def _h(**cambios):
    h = json.loads(json.dumps(H)); h.update(cambios); return h


def test_miles_y_signo_negativo_se_normalizan():
    h = _h(); h["grupos"][0]["fuerza"] = 1234.567; h["grupos"][0]["pares"][0]["valor_test"] = -5.5
    pd = redaccion.datos_prompt(h)
    assert redaccion.verificar(["Fuerza 1.234,567 y V de -5,500."], h, pd) == []


def test_los_umbrales_del_metodo_se_pueden_citar():
    pd = redaccion.datos_prompt(H)
    assert redaccion.verificar(["Umbrales 1,65, 1,96, 2,58 y 0,01."], H, pd) == []


def test_p_valor_solo_se_acepta_si_el_perfil_lo_ve():
    h = _h(visibles=dict(valor_test=True, p_valor=True, class_cat=False, razon=False))
    h["grupos"][0]["pares"][0]["p_texto"] = "p = 0,037"
    assert redaccion.verificar(["Con p = 0,037."], h, redaccion.datos_prompt(h)) == []
    h["visibles"]["p_valor"] = False
    assert redaccion.verificar(["Con p = 0,037."], h, redaccion.datos_prompt(h)) == ["0,037"]


def test_s3_solo_cita_los_conjuntos_mencionados(tmp_path):
    h = _h(); g2 = json.loads(json.dumps(h["grupos"][0])); g2["conjunto"] = "Otra1_2_"; g2["posicion"] = 2
    for i, p in enumerate(g2["pares"]): p["id"] = f"GRU-P9{i}"; p["caracteristica"] = "Otra1_2_"
    h["grupos"].append(g2)
    r = redaccion.redactar_sintesis(escribir(tmp_path, h), KB, generar=lambda p: json.dumps({"S1": "x", "S2": "y", "S3": "Destaca Otra1_2_."}))
    s = json.load(open(r, encoding="utf-8"))
    assert s["secciones"][2]["interpretaciones"] == ["GRU-P90", "GRU-P91"]


def test_s4_sale_de_la_base_y_faltan_secciones(tmp_path):
    ruta = redaccion.redactar_sintesis(escribir(tmp_path), KB, generar=lambda p: json.dumps({"S1": "a", "S2": "b"}))
    s = json.load(open(ruta, encoding="utf-8"))
    assert s["estado"] == "error" and "S3" in s["aviso"]
    assert s["secciones"][-1]["texto"] == H["limitaciones"][0]["texto"]


def test_mensaje_de_tiempo_agotado():
    assert "tardó" in redaccion._mensaje_error(TimeoutError("x"), "m")


def test_sin_campo_visibles_el_experto_ve_el_p_valor():
    h = _h(perfil="experto"); h.pop("visibles", None)
    h["grupos"][0]["pares"][0]["p_texto"] = "p = 0,037"
    assert redaccion.verificar(["Con p = 0,037."], h, redaccion.datos_prompt(h)) == []
    h["perfil"] = "intermedio"
    assert redaccion.verificar(["Con p = 0,037."], h, redaccion.datos_prompt(h)) == ["0,037"]


def test_reintento_si_el_modelo_entra_en_bucle(monkeypatch):
    monkeypatch.setenv("AIDA_PROVEEDOR", "ollama")
    ollama = pytest.importorskip("ollama")
    import importlib.util
    spec = importlib.util.spec_from_file_location("aida_llm_t", os.path.join(os.path.dirname(redaccion.__file__), "llm.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    llamadas = []

    def chat(self, **k):
        llamadas.append(k["options"])
        if len(llamadas) == 1:
            raise ollama.ResponseError("prediction aborted, token repeat limit reached", -1)
        yield {"message": {"content": '{"S1": "a"}'}, "done_reason": "stop"}
    monkeypatch.setattr(ollama.Client, "chat", chat)
    assert m.generar_texto("x") == '{"S1": "a"}'
    assert len(llamadas) == 2 and llamadas[0]["temperature"] == 0 and llamadas[1]["repeat_penalty"] > llamadas[0]["repeat_penalty"]


def test_una_sola_consulta_y_reintento_si_viene_incompleta(tmp_path):
    h = json.loads(json.dumps(H))
    ruta = escribir(tmp_path, h)
    prompts = []

    def generar(prompt):
        prompts.append(prompt)
        if len(prompts) == 1:                       # la primera respuesta no trae todas las secciones y se reintenta
            return json.dumps({"S1": "Texto de inicio"})
        return json.dumps({"S1": "Texto de inicio", "S2": "Hallazgos para el conjunto Are3_20.9a31.4_: E47_F2_D y ECO_F2_D.",
                           "S3": "Texto de cierre"})
    r = redaccion.redactar_sintesis(ruta, T.KB, generar=generar)
    s = json.load(open(r, encoding="utf-8"))
    assert s["estado"] == "redactada"
    assert len(prompts) == 2 and prompts[0] == prompts[1]
    s2 = s["secciones"][1]["texto"]                     # el primer párrafo del intermedio lleva además las explicaciones fijas
    assert [s["secciones"][0]["texto"], s["secciones"][2]["texto"]] == ["Texto de inicio", "Texto de cierre"]
    assert s2.startswith("Hallazgos para el conjunto Are3_20.9a31.4_: E47_F2_D y ECO_F2_D.") and "El valor test mide" in s2 and "El porcentaje es" in s2


def test_relaciones_y_conteos_se_verifican():
    h = json.loads(json.dumps(H))
    h["grupos"][0]["conjunto_legible"] = "Are3 (20,9 a 31,4)"
    g = h["grupos"][0]
    assert redaccion.verificar_relaciones(["Are3_20.9a31.4_ se asocia con E47_F2_D y ECO_F2_D."], h) == []
    assert redaccion.verificar_relaciones(["Are3 (20,9 a 31,4) caracteriza a E47_F2_D."], h) == []
    h2 = json.loads(json.dumps(h)); h2["grupos"].append(dict(g, conjunto="Zeta1_1_", conjunto_legible="Zeta1_1_",
        pares=[dict(g["pares"][0], id="X", clase="CLASE_Z")]))
    assert redaccion.verificar_relaciones(["Zeta1_1_ se asocia con E47_F2_D."], h2)          # clase de otro conjunto
    assert redaccion.verificar_relaciones(["Zeta1_1_ y Are3_20.9a31.4_ se asocian con E47_F2_D."], h2)   # Zeta no tiene ninguna
    assert redaccion.verificar_relaciones([f"Hay {h['n_clases'] + 5} clases."], h)
    assert redaccion.verificar_relaciones([f"Hay {h['n_categorias'] + 3} categorías."], h)


def _llm_nuevo():
    import importlib.util
    spec = importlib.util.spec_from_file_location("aida_llm_g", os.path.join(os.path.dirname(redaccion.__file__), "llm.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_env_se_lee_sin_pisar_el_entorno(tmp_path, monkeypatch):
    m = _llm_nuevo()
    (tmp_path / ".env").write_text('# c\nAIDA_PROVEEDOR=gemini\nGEMINI_API_KEY="abc"\nAIDA_MODELO=x\n', encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False); monkeypatch.delenv("AIDA_PROVEEDOR", raising=False)
    monkeypatch.setenv("AIDA_MODELO", "del-entorno")
    m.cargar_env(str(tmp_path / ".env"))
    assert os.environ["GEMINI_API_KEY"] == "abc" and os.environ["AIDA_MODELO"] == "del-entorno"


def test_proveedor_por_defecto(monkeypatch):
    m = _llm_nuevo()
    monkeypatch.setattr(m, "cargar_env", lambda ruta=None: None)
    monkeypatch.delenv("AIDA_PROVEEDOR", raising=False); monkeypatch.delenv("AIDA_MODELO", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert m.proveedor() == "ollama" and m.modelo_por_defecto() == "llama3.2:3b"
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    assert m.proveedor() == "gemini" and m.modelo_por_defecto().startswith("gemini")


def test_gemini_envia_la_clave_en_el_encabezado_y_no_en_la_url(monkeypatch):
    import io
    m = _llm_nuevo()
    monkeypatch.setattr(m, "cargar_env", lambda ruta=None: None)
    monkeypatch.setenv("AIDA_PROVEEDOR", "gemini"); monkeypatch.setenv("GEMINI_API_KEY", "SECRETA")
    vistos = {}

    class R(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def abrir(req, timeout=None):
        vistos["url"], vistos["h"], vistos["b"] = req.full_url, dict(req.header_items()), json.loads(req.data)
        return R(json.dumps({"candidates": [{"content": {"parts": [{"text": '{"S1": "a"}'}]}, "finishReason": "STOP"}]}).encode())
    monkeypatch.setattr(m.urllib.request, "urlopen", abrir)
    assert m.generar_texto("hola", "llama3.2:3b") == '{"S1": "a"}'
    assert "SECRETA" not in vistos["url"] and vistos["h"]["X-goog-api-key"] == "SECRETA"
    assert vistos["url"].split("models/")[1].startswith("gemini")      # un modelo de Ollama se reemplaza
    assert vistos["b"]["generationConfig"]["responseMimeType"] == "application/json"


def test_gemini_errores_en_espanol_sin_la_clave(monkeypatch):
    import urllib.error
    m = _llm_nuevo()
    monkeypatch.setattr(m, "cargar_env", lambda ruta=None: None)
    monkeypatch.setenv("AIDA_PROVEEDOR", "gemini"); monkeypatch.setenv("GEMINI_API_KEY", "SECRETA")

    def abrir(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 429, "x", {}, None)
    monkeypatch.setattr(m.urllib.request, "urlopen", abrir)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    with pytest.raises(ValueError) as e:
        m.generar_texto("x")
    assert "cuota" in str(e.value) and "SECRETA" not in str(e.value)
    monkeypatch.delenv("GEMINI_API_KEY")
    with pytest.raises(ValueError, match="falta GEMINI_API_KEY"):
        m.generar_texto("x")


def test_gemini_reintenta_si_esta_saturado(monkeypatch):
    import io, urllib.error
    m = _llm_nuevo()
    monkeypatch.setattr(m, "cargar_env", lambda ruta=None: None)
    monkeypatch.setenv("AIDA_PROVEEDOR", "gemini"); monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    n = []

    class R(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def abrir(req, timeout=None):
        n.append(1)
        if len(n) < 3:
            raise urllib.error.HTTPError(req.full_url, 503, "x", {}, None)
        return R(json.dumps({"candidates": [{"content": {"parts": [{"text": "{}"}]}, "finishReason": "STOP"}]}).encode())
    monkeypatch.setattr(m.urllib.request, "urlopen", abrir)
    assert m.generar_texto("x") == "{}" and len(n) == 3


def test_prompt_pide_sintesis_integradora_y_lista_clases_que_se_repiten():
    h = json.loads(json.dumps(T.H))
    rec = redaccion.clases_recurrentes(h, 99)
    assert all(len(cs) >= 2 for _, cs in rec)
    h["secciones"][2]["contenido"] = "Lectura de conjunto de los patrones, en términos estadísticos."     # el contenido sale de la base de conocimiento
    p = redaccion.armar_prompt(h)
    assert "Lectura de conjunto de los patrones" in p and p.count("Máximo 3 oraciones") == 1
    assert '"S1"' in p and '"S2"' in p and '"S3"' in p
