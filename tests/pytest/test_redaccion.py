"""Pruebas de la parte en Python de MS. Ejecutar desde la carpeta aida:  pytest tests/pytest"""
import json
import os
import sys

AIDA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(AIDA, "python"))
import redaccion  # noqa: E402

KB = os.path.join(AIDA, "kb", "base_conocimiento.json")

H = {
    "perfil": "intermedio", "instruccion_registro": "Terminología estadística básica.", "escalado": True,
    "descripcion": "grupos", "archivo": "Area.txt", "n_pares": 2, "n_clases": 2, "n_categorias": 1,
    "n_significativas": 2, "n_no_significativas": 0, "n_transiciones": 0, "minimo_clases": 4,
    "secciones": [{"id": f"S{k}", "nombre": f"Sección {k}", "contenido": "", "debe_incluir": []} for k in range(1, 5)],
    "limitaciones": [{"id": "AD3", "texto": "Sólo asociaciones con valor test mayor o igual que 1,65."}],
    "grupos": [{"conjunto": "Are3_20.9a31.4_", "fuerza": 20.867, "n_pares": 2, "n_clases": 2, "tipo": "sin clasificar",
                "posicion": 1, "pares": [
                    {"id": "GRU-P001", "clase": "E47_F2_D", "caracteristica": "Are3_20.9a31.4_", "valor_test": 13.202,
                     "p_valor": 0.0, "p_texto": "p < 0,01", "class_cat": 23.2, "cat_class": 67.4, "global": 18.9,
                     "razon": 3.566, "regla": "R-MI-1", "significacion": "altamente significativo", "peso_bajo": False,
                     "transicion": "", "texto": "En E47_F2_D, el 67,4 % de los valores corresponde a Are3_20.9a31.4_, "
                                                "frente al 18,9 % del total (valor test 13,202)."},
                    {"id": "GRU-P002", "clase": "ECO_F2_D", "caracteristica": "Are3_20.9a31.4_", "valor_test": 7.665,
                     "p_valor": 0.0, "p_texto": "p < 0,01", "class_cat": 14.9, "cat_class": 47.9, "global": 18.9,
                     "razon": 2.534, "regla": "R-MI-1", "significacion": "altamente significativo", "peso_bajo": False,
                     "transicion": ""}]}],
}


def escribir(tmp_path, h=H):
    ruta = tmp_path / "hallazgos.json"
    ruta.write_text(json.dumps(h, ensure_ascii=False), encoding="utf-8")
    return str(ruta)


def test_los_nombres_no_cuentan_como_numeros():
    n = redaccion.numeros_del_texto("En E47_F2_D, Are3_20.9a31.4_ tiene 67,4 %.", {"E47_F2_D", "Are3_20.9a31.4_"})
    assert n == ["67,4"]


def test_sintesis_verificada(tmp_path):
    consultas = []

    def falso(prompt):
        consultas.append(prompt)
        assert "Terminología estadística básica." in prompt and "13,202" in prompt     # una sola consulta, con los datos
        return json.dumps({"S1": "Se analizaron 2 clases y 1 categoría.",
                           "S2": "Hallazgos para el conjunto Are3_20.9a31.4_: E47_F2_D tiene valor test 13,202, "
                                 "con 67,4 % frente al 18,9 % del total.",
                           "S3": "Las diferencias superan el umbral de 1,65."})
    s = json.load(open(redaccion.redactar_sintesis(escribir(tmp_path), KB, "simulado", falso), encoding="utf-8"))
    assert len(consultas) == 1
    assert s["estado"] == "redactada" and s["aviso"] == ""
    assert [x["id"] for x in s["secciones"]] == ["S1", "S2", "S3", "S4"]
    assert s["secciones"][1]["texto"].startswith("Hallazgos para el conjunto")      # texto corrido redactado por el modelo
    assert s["secciones"][2]["interpretaciones"] == ["GRU-P001", "GRU-P002"]


def test_valor_inventado_se_rechaza(tmp_path):
    falso = lambda p: json.dumps({"S1": "Hay 2 clases.", "S2": "Hallazgos para el conjunto Are3_20.9a31.4_: E47_F2_D.",
                                  "S3": "El valor test es 14,5."})
    s = json.load(open(redaccion.redactar_sintesis(escribir(tmp_path), KB, "simulado", falso), encoding="utf-8"))
    assert s["estado"] == "no verificada" and "14,5" in s["aviso"]


def test_valor_inventado_en_un_conjunto_usa_la_version_estructurada(tmp_path):
    h = dict(H, texto_s2="1. Are3_20.9a31.4_: 2 asociaciones. E47_F2_D, ECO_F2_D.")

    def falso(prompt):
        return json.dumps({"S1": "Hay 2 clases.", "S2": "Hallazgos para el conjunto Are3_20.9a31.4_: E47_F2_D alcanza 99,9 %.",
                           "S3": "Fin."})
    s = json.load(open(redaccion.redactar_sintesis(escribir(tmp_path, h), KB, "simulado", falso), encoding="utf-8"))
    assert "99,9" not in s["secciones"][1]["texto"]
    assert s["secciones"][1]["texto"].startswith("Hallazgos para el conjunto Are3_20.9a31.4_: Este conjunto se asocia con 2 clases. El valor test mide")   # párrafo armado por código, con las explicaciones del primer párrafo
    assert s["estado"] == "parcialmente redactada" and "1 de 1 conjuntos" in s["aviso"]
    assert s["rechazados"][0]["texto"].endswith("99,9 %.") and "99,9" in s["rechazados"][0]["motivos"][0]


def test_novato_no_recibe_valor_test(tmp_path):
    h = dict(H, perfil="novato")
    prompt = redaccion.armar_prompt(h)
    assert "13,202" not in prompt and "67,4" in prompt


def test_el_prompt_del_novato_no_trae_valor_test_ni_fuerza_y_el_del_intermedio_si():
    h = dict(H, perfil="novato", visibles=dict(valor_test=False, p_valor=False, class_cat=False, razon=False))
    p = redaccion.armar_prompt(h)
    assert "Conjunto Are3_20.9a31.4_" in p and "E47_F2_D" in p and "ECO_F2_D" in p
    assert "20,867" not in p and "fuerza" not in p.lower() and "V-test" not in p
    assert "(fuerza 20,867)" in redaccion.armar_prompt(H) and "V-test: 13,202" in redaccion.armar_prompt(H)


def test_un_parrafo_que_atribuye_una_clase_ajena_usa_la_version_estructurada(tmp_path):
    h = json.loads(json.dumps(H)); g2 = json.loads(json.dumps(h["grupos"][0]))
    g2["conjunto"] = "Otra1_2_"; g2["posicion"] = 2
    for i, p in enumerate(g2["pares"]): p["id"] = f"GRU-P9{i}"; p["clase"] = f"Z{i}"; p["caracteristica"] = "Otra1_2_"
    h["grupos"].append(g2); h["texto_s2"] = "1. Are3_20.9a31.4_: 2 asociaciones.\n2. Otra1_2_: 2 asociaciones."

    def falso(prompt):                # al conjunto Are3 se le atribuye la clase Z0, que es de Otra1_2_
        return json.dumps({"S1": "Hay 2 clases.", "S3": "Fin.",
                           "S2": "Hallazgos para el conjunto Are3_20.9a31.4_: Z0 se asocia con el conjunto.\n\n"
                                 "Hallazgos para el conjunto Otra1_2_: Z0 y Z1 caracterizan al conjunto."})
    s = json.load(open(redaccion.redactar_sintesis(escribir(tmp_path, h), KB, "simulado", falso), encoding="utf-8"))
    t = s["secciones"][1]["texto"]
    assert "Z0 se asocia" not in t and "Are3_20.9a31.4_: Este conjunto se asocia con 2 clases." in t          # sólo el grupo con la clase ajena pasa al respaldo
    assert "Z0 y Z1 caracterizan" in t and s["estado"] == "parcialmente redactada"


def test_modelo_no_disponible(tmp_path):
    def caido(prompt):
        raise ConnectionError("Ollama no responde")
    s = json.load(open(redaccion.redactar_sintesis(escribir(tmp_path), KB, "simulado", caido), encoding="utf-8"))
    assert s["estado"] == "error"


# ─── Correcciones de la revisión del 26/10/2026 ──────────────────────────────

def _estado(tmp_path, respuesta):
    ruta = redaccion.redactar_sintesis(escribir(tmp_path), KB, generar=lambda p: respuesta)
    return json.load(open(ruta, encoding="utf-8"))


def test_un_numero_con_punto_decimal_o_de_miles_se_controla():
    h = H
    pd = redaccion.datos_prompt(h)
    assert redaccion.verificar(["Hay 22.5 casos y 1.777,5 más."], h, pd) == ["22.5", "1.777,5"]
    assert redaccion.verificar(["El 67.4 %."], h, pd) == []          # mismo valor con punto decimal


def test_los_numeros_de_un_nombre_de_conjunto_son_datos():
    h = H
    assert redaccion.verificar(["Are3 (entre 20,9 y 31,4) concentra la mayor fuerza."], h, redaccion.datos_prompt(h)) == []


def test_el_signo_negativo_cuenta():
    h = H
    assert redaccion.verificar(["V de -13,202."], h, redaccion.datos_prompt(h)) == ["-13,202"]


def test_respuestas_con_valores_no_texto_son_error(tmp_path):
    for resp in ['{"S1": null, "S2": "a", "S3": "b"}', '{"S1": 5, "S2": "a", "S3": "b"}', '[1, 2]', "no es json", ""]:
        s = _estado(tmp_path, resp)
        assert s["estado"] == "error" and s["aviso"], resp


def test_bloque_json_con_vallas_se_acepta(tmp_path):
    s = _estado(tmp_path, '```json\n{"S1": "Primera.", "S2": "Otra.", "S3": "Final."}\n```')
    # S1 y S3 se aceptan; S2 se pide por conjunto con la clave «texto», que esta respuesta no trae: queda con el respaldo.
    assert s["estado"] == "parcialmente redactada" and s["secciones"][0]["texto"] == "Primera."


def test_los_valores_nulos_no_rompen_el_prompt():
    h = json.loads(json.dumps(H))
    h["grupos"][0]["pares"][0]["razon"] = None
    h["grupos"][0]["fuerza"] = None
    assert "no calculable" in redaccion.armar_prompt(h)


def test_el_novato_no_ve_el_valor_test_ni_en_las_instrucciones():
    h = json.loads(json.dumps(H)); h["perfil"] = "novato"
    h["secciones"][1]["contenido"] = "Patrones ordenados por fuerza, con sus pares ordenados por valor test absoluto."
    prompt = redaccion.armar_prompt(h)
    assert "valor test" not in prompt.lower() and "fuerza" not in prompt.lower()


def test_los_permisos_del_perfil_salen_de_la_base_de_conocimiento():
    h = json.loads(json.dumps(H))
    h["visibles"] = dict(valor_test=True, p_valor=True, class_cat=False, razon=False)
    pd = redaccion.datos_prompt(h)
    assert pd["mostrar_p"] and not pd["mostrar_class_cat"]


def test_mensajes_de_error_en_espanol(monkeypatch):
    monkeypatch.setenv("AIDA_PROVEEDOR", "ollama")
    assert "Ollama" in redaccion._mensaje_error(ConnectionError("Failed to connect to Ollama"), "m")
    assert "descargado" in redaccion._mensaje_error(type("ResponseError", (Exception,), {"status_code": 404})("x"), "llama3.2:3b")


def test_el_modulo_llm_propio_no_choca_con_otro(monkeypatch):
    import types
    import importlib
    monkeypatch.setitem(sys.modules, "llm", types.ModuleType("llm"))
    nuevo = importlib.reload(redaccion)          # se vuelve a cargar con el «llm» ajeno ya presente
    assert hasattr(nuevo.llm, "generar_texto")


def test_decimal_con_letras_pegadas_no_pasa():
    h = json.loads(json.dumps(H))
    pd = redaccion.datos_prompt(h)
    assert redaccion.verificar(["una razón de 3,5x"], h, pd) == ["3,5"]


def test_json_con_salto_de_linea_literal():
    assert redaccion._leer_respuesta('{"S1": "a\nb"}')["S1"] == "a\nb"
