"""Pruebas de la revisión del 06/11/2026 sobre la corrida del área sin agrupar (186 clases con nombre numérico).
Ninguna usa la red ni una clave real."""
import json
import os
import sys

import pytest

AIDA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(AIDA, "python"))
import redaccion  # noqa: E402

KB = os.path.join(AIDA, "kb", "base_conocimiento.json")

# Las clases de los dos conjuntos que provocaron los falsos rechazos, más las que hacen falta para las pruebas.
ARE1 = ("Are1_1.3a9.3_", "Are1 (1,3 a 9,3)", ["76", "86", "1", "3", "9"])
ARE4 = ("Are4_31.4a43.4_", "Are4 (31,4 a 43,4)", ["109", "49", "51"])
ARE5 = ("Are5_53a53_", "Are5 (53)", ["56", "53", "51", "49"])
ARE3 = ("Are3_20.9a31.4_", "Are3 (20,9 a 31,4)", ["35", "39", "31", "43", "4"])


def _h(**cambios):
    def par(i, c, cat, legible):
        return {"id": i, "clase": c, "caracteristica": cat, "caracteristica_legible": legible, "valor_test": 14.213, "valor_test_txt": "14,213",
                "p_valor": 0.0, "p_texto": "p < 0,01", "class_cat": 94.3, "cat_class": 1.5, "global": 0.5, "razon": 3.0, "regla": "R-MI-1",
                "significacion": "altamente significativo", "peso_bajo": False, "transicion": "", "transicion_legible": "", "texto": "Texto."}
    grupos, k = [], 0
    for pos, (cat, leg, clases) in enumerate((ARE1, ARE5, ARE3, ARE4), start=1):
        pares = []
        for c in clases:
            k += 1
            pares.append(par(f"COL-P{k:03d}", c, cat, leg))
        grupos.append({"conjunto": cat, "conjunto_legible": leg, "fuerza": 100.0 - pos, "fuerza_txt": f"{100 - pos},000", "n_pares": 65 if cat == ARE1[0] else 39 if cat == ARE5[0] else len(clases),
                       "n_clases": len(clases), "tipo": "singularidad", "posicion": pos, "pares": pares})
    h = {"perfil": "intermedio", "instruccion_registro": "Registro.", "escalado": True, "descripcion": "columnas", "archivo": "area.txt",
         "n_pares": 244, "n_clases": 186, "n_categorias": 5, "n_significativas": 244, "n_no_significativas": 0, "n_transiciones": 0, "minimo_clases": 4,
         "secciones": [{"id": f"S{k}", "nombre": f"Sección {k}", "contenido": "", "debe_incluir": []} for k in range(1, 5)],
         "limitaciones": [{"id": "AD3", "texto": "Limitación."}], "grupos": grupos}
    h.update(cambios)
    return h


# ─── Los falsos rechazos de la corrida real ──────────────────────────────────

def test_el_intervalo_de_un_conjunto_no_cita_clases():
    t = "Los conjuntos son Are1 (1,3 a 9,3), Are5 (53), Are3 (20,9 a 31,4) y Are4 (31,4 a 43,4)."
    assert redaccion.verificar_relaciones([t], _h()) == []


def test_un_conteo_no_cita_una_clase():
    t = "Los conjuntos de mayor relevancia son Are1 (1,3 a 9,3) con 65 asociaciones y Are5 (53) con 39 asociaciones."
    assert redaccion.verificar_relaciones([t], _h()) == []


def test_un_parrafo_correcto_pasa_el_control_por_conjunto():
    t = "Are5 (53) reúne 39 asociaciones; la de mayor valor test es la clase 56."
    assert redaccion.verificar_relaciones([t], _h()) == []
    assert redaccion._citas_ajenas_al_conjunto(t, _h(), 1) == []


def _h_transiciones():
    """Are2 es contiguo a Are1 y a Are3; Are1 y Are3 no son contiguos entre sí."""
    def par(c, cat, contigua):
        return {"clase": c, "caracteristica": cat, "transicion": contigua, "transicion_legible": ""}
    a1, a2, a3 = "Are1_1.3a9.3_", "Are2_9.3a20.9_", "Are3_20.9a31.4_"
    grupos = [{"conjunto": a1, "conjunto_legible": "Are1 (1,3 a 9,3)", "tipo": "singularidad", "n_pares": 1, "n_clases": 1, "pares": [par("1", a1, a2)]},
              {"conjunto": a2, "conjunto_legible": "Are2 (9,3 a 20,9)", "tipo": "singularidad", "n_pares": 2, "n_clases": 2, "pares": [par("1", a2, a1), par("30", a2, a3)]},
              {"conjunto": a3, "conjunto_legible": "Are3 (20,9 a 31,4)", "tipo": "singularidad", "n_pares": 1, "n_clases": 1, "pares": [par("30", a3, a2)]}]
    return dict(_h(), grupos=grupos)


def test_las_transiciones_de_un_parrafo_se_refieren_a_su_conjunto():
    t = "Describen transiciones con los conjuntos contiguos Are1 (1,3 a 9,3) y Are3 (20,9 a 31,4)."
    h = _h_transiciones()
    assert redaccion.verificar_relaciones([t], h, h["grupos"][1]) == []     # la frase real que se rechazaba en el párrafo de Are2
    assert redaccion.verificar_relaciones([t], h)                           # sin saber de qué conjunto habla, Are1 y Are3 no son contiguos


def test_una_transicion_que_no_existe_en_el_parrafo_se_sigue_rechazando():
    h = _h_transiciones()
    assert redaccion.verificar_relaciones(["Hay una transición con Are3 (20,9 a 31,4)."], h, h["grupos"][0])


# ─── La cita con la forma «clase N» se sigue controlando ─────────────────────

def test_una_clase_ajena_citada_se_rechaza():
    t = "En Are1 (1,3 a 9,3) se destaca la clase 39."
    assert redaccion.verificar_relaciones([t], _h()) == ["el conjunto Are1 (1,3 a 9,3) no se asocia con ninguna de las clases citadas junto a él",
                                                          "la clase 39 no se asocia con Are1 (1,3 a 9,3)"]
    assert redaccion._citas_ajenas_al_conjunto(t, _h(), 0) == ["la clase 39 no pertenece al conjunto"]


@pytest.mark.parametrize("texto, esperadas", [
    ("las clases 1, 76, 86 y 9 aparecen", {"1", "76", "86", "9"}),
    ("La clase 76 tiene 1,5 %", {"76"}),
    ("la clase 76 y 3 asociaciones", {"76"}),
    ("clase 76, 14,213 de valor test", {"76"}),
    ("clase 76, 2 % del total", {"76"}),
    ("hay 186 clases y 5 categorías", set()),
    ("clase 1,5", set()),
])
def test_lista_de_clases_citadas(texto, esperadas):
    assert redaccion._clases_numericas_citadas(texto) == esperadas


# ─── Un número inventado ya no se esconde detrás del nombre de una clase ─────

def _ajenos(texto, h=None):
    h = h or _h()
    return redaccion.verificar([texto], h, redaccion.datos_prompt(h))


def test_un_numero_que_coincide_con_una_clase_no_pasa_por_clase():
    assert _ajenos("En Are1 (1,3 a 9,3), el 76 % de los valores corresponde a la clase 86.") == ["76"]


def test_la_clase_citada_correctamente_no_es_un_valor_ajeno():
    assert _ajenos("En la clase 76 y en las clases 1, 3 y 86, Are1 (1,3 a 9,3) aparece.") == []


def test_una_clase_inexistente_si_es_un_valor_ajeno():
    assert _ajenos("Se destaca la clase 977.") == ["977"]


def test_un_nombre_no_numerico_se_cita_como_siempre():
    h = _h()
    h["grupos"][0]["pares"][0]["clase"] = "E47_F1"
    assert _ajenos("En E47_F1 se concentra.", h) == []
    assert redaccion.verificar_relaciones(["En Are1 (1,3 a 9,3) se destaca E47_F1."], h) == []


def test_el_prompt_escribe_clase_n_solo_si_es_numerica():
    h = _h()
    h["grupos"][0]["pares"][0]["clase"] = "E47_F1"
    p = redaccion.armar_prompt(h)
    assert ": clase 86 (" in p and ": E47_F1 (" in p and "clase E47_F1" not in p
    assert "- clase 1: 2 conjuntos" not in p and "nunca el número solo" in p


# ─── Lo que el archivo no permite afirmar ────────────────────────────────────

@pytest.mark.parametrize("texto", [
    "Se identificaron 12 asociaciones significativas de 12 posibles.",
    "Todas las asociaciones son significativas.",
    "Todas las asociaciones obtenidas son significativas, sin registrarse asociaciones que no lo sean.",
    "Sin registrarse asociaciones que no lo sean.",
    "Se identificaron 12 asociaciones significativas de un total de 12.",
    "Contabilizándose doce asociaciones significativas de un total de doce.",
    "Se distingue entre las diferencias relevantes y las que no lo son.",
    "No hay asociaciones no significativas.",
])
def test_afirmaciones_sin_respaldo_se_rechazan(texto):
    assert redaccion.verificar_afirmaciones([texto], _h())


@pytest.mark.parametrize("texto", [
    "El archivo informa 12 asociaciones significativas; las demás combinaciones no figuran en él.",
    "Sólo las asociaciones listadas superan el umbral de DaFu.",
    "Esa concentración es poco probable por azar.",
])
def test_afirmaciones_validas_se_aceptan(texto):
    assert redaccion.verificar_afirmaciones([texto], _h()) == []


def test_con_no_significativas_declaradas_se_puede_hablar_de_ellas():
    assert redaccion.verificar_afirmaciones(["Hay asociaciones que no lo son."], _h(n_no_significativas=3)) == []


def test_el_prompt_no_pide_afirmar_lo_que_no_se_sabe():
    p = redaccion.armar_prompt(_h())
    assert "244 de 244" not in p and "No llames «posibles»" in p and "superan el umbral de DaFu" in p
    assert "Indica cuántas asociaciones no son significativas" not in p
    con = redaccion.armar_prompt(_h(n_pares=250, n_no_significativas=6))
    assert "244 de 250" in con and "No llames «posibles»" not in con and "Indica cuántas asociaciones no son significativas" in con


# ─── Estado parcial y registro de los textos rechazados ──────────────────────

def _redactar(tmp_path, generar, **cambios):
    ruta = tmp_path / "hallazgos.json"
    ruta.write_text(json.dumps(_h(texto_s2="1. a\n2. b\n3. c\n4. d", **cambios), ensure_ascii=False), encoding="utf-8")
    return json.load(open(redaccion.redactar_sintesis(str(ruta), KB, generar=generar), encoding="utf-8"))


def _generar(parrafo_are4="Hallazgos para el conjunto Are4 (31,4 a 43,4): la clase 109.", s3="Sólo las asociaciones listadas superan el umbral."):
    """Respuesta del modelo: una sola, con las tres secciones y un párrafo por conjunto (en el orden de `_h()`)."""
    s2 = "\n\n".join([f"Hallazgos para el conjunto {ARE1[1]}: la clase 76.", f"Hallazgos para el conjunto {ARE5[1]}: la clase 56.",
                      f"Hallazgos para el conjunto {ARE3[1]}: la clase 35.", parrafo_are4])
    return lambda prompt: json.dumps({"S1": "Se analizaron 186 clases.", "S2": s2, "S3": s3})


def test_todo_verificado_queda_redactada_sin_rechazos(tmp_path):
    s = _redactar(tmp_path, _generar())
    assert s["estado"] == "redactada" and s["aviso"] == "" and s["rechazados"] == []


def test_un_parrafo_rechazado_deja_parcial_y_registra_texto_y_motivo(tmp_path):
    malo = "Hallazgos para el conjunto Are4 (31,4 a 43,4): el 99,9 % corresponde a la clase 109."
    s = _redactar(tmp_path, _generar(parrafo_are4=malo))
    assert s["estado"] == "parcialmente redactada"
    assert "1 de 4 conjuntos" in s["aviso"] and "Are4 (31,4 a 43,4) (" in s["aviso"] and "99,9" in s["aviso"]
    assert len(s["rechazados"]) == 1
    r = s["rechazados"][0]
    assert r["seccion"] == "S2" and r["conjunto"] == ARE4[1] and r["texto"] == malo and "99,9" in r["motivos"][0]


def test_una_conclusion_con_una_afirmacion_sin_respaldo_no_se_verifica(tmp_path):
    s3 = "Todas las asociaciones son significativas."
    s = _redactar(tmp_path, _generar(s3=s3))
    assert s["estado"] == "no verificada" and "no permite saber" in s["aviso"]
    assert [r["seccion"] for r in s["rechazados"]] == ["S3"] and s["rechazados"][0]["texto"] == s3


def test_las_interpretaciones_citadas_en_s3_no_salen_de_un_conteo(tmp_path):
    s = _redactar(tmp_path, _generar(s3="Se informan 39 asociaciones y la clase 86."))
    s3 = next(x for x in s["secciones"] if x["id"] == "S3")
    assert s3["interpretaciones"] == ["COL-P002"]                 # la clase 86; no la 39 del conteo


# ─── Una sola respuesta: separación de S2 por grupo ──────────────────────────

def _por_grupo(texto, h=None):
    h = h or _h(texto_s2="1. a\n2. b\n3. c\n4. d")
    return redaccion._hallazgos_por_grupo(texto, h, redaccion.datos_prompt(h))


def test_un_grupo_que_el_modelo_no_redacto_pasa_al_respaldo():
    t = "\n\n".join(f"Hallazgos para el conjunto {x[1]}: la clase {x[2][0]}." for x in (ARE1, ARE5, ARE4))     # falta Are3
    texto, respaldo, rechazados = _por_grupo(t)
    assert respaldo == [ARE3[1]] and rechazados[0]["conjunto"] == ARE3[1] and "no redactó" in rechazados[0]["motivos"][0]
    assert texto.count("Hallazgos para el conjunto") == 4 and f"Hallazgos para el conjunto {ARE3[1]}: Este conjunto se asocia con" in texto      # el respaldo ocupa su lugar


def test_una_continuacion_que_nombra_a_un_vecino_sigue_siendo_del_grupo():
    h = _h(texto_s2="1. a\n2. b\n3. c\n4. d")
    h["grupos"][2]["pares"][0]["transicion"] = ARE4[0]; h["grupos"][3]["pares"][0]["transicion"] = ARE3[0]
    t = ("Hallazgos para el conjunto Are1 (1,3 a 9,3): la clase 76.\n\nHallazgos para el conjunto Are5 (53): la clase 56.\n\n"
         "Hallazgos para el conjunto Are3 (20,9 a 31,4): la clase 35.\n\nHay una transición con Are4 (31,4 a 43,4).\n\n"
         "Hallazgos para el conjunto Are4 (31,4 a 43,4): la clase 109.")
    texto, respaldo, rechazados = _por_grupo(t, h)
    assert respaldo == [] and rechazados == [] and "transición con Are4 (31,4 a 43,4)" in texto


def test_un_parrafo_en_el_orden_equivocado_igual_se_asigna_por_su_encabezado():
    t = "\n\n".join(f"Hallazgos para el conjunto {x[1]}: la clase {x[2][0]}." for x in (ARE4, ARE3, ARE5, ARE1))
    assert _por_grupo(t)[1:] == ([], [])


def test_un_texto_introductorio_se_verifica_como_cualquier_otro():
    cuerpo = "\n\n".join(f"Hallazgos para el conjunto {x[1]}: la clase {x[2][0]}." for x in (ARE1, ARE5, ARE3, ARE4))
    assert _por_grupo("Resumen del análisis.\n\n" + cuerpo)[2] == []
    rechazado = _por_grupo("Resumen: 55,5 % del total.\n\n" + cuerpo)[2]
    assert rechazado[0]["conjunto"] == "" and "55,5" in rechazado[0]["motivos"][0]


def test_el_inicio_del_parrafo_acepta_grupo_o_conjunto():
    t = "\n\n".join(f"Hallazgos para el grupo {x[1]}: la clase {x[2][0]}." for x in (ARE1, ARE5, ARE3, ARE4))
    assert _por_grupo(t)[1:] == ([], [])


# ─── Lectura cruzada y ejemplo de estilo ─────────────────────────────────────

def _h_familias():
    """Tres clases de la familia E47 y dos de ECO, cada una con su conjunto principal."""
    def par(c, cat, leg, v):
        return {"id": "X", "clase": c, "caracteristica": cat, "caracteristica_legible": leg, "valor_test": v, "valor_test_txt": str(v), "p_texto": "p < 0,01",
                "class_cat": 10.0, "cat_class": 40.0, "global": 20.0, "razon": 2.0, "significacion": "altamente significativo", "transicion": ""}
    a1, a3, a5 = ("Are1_1.3a9.3_", "Are1 (1,3 a 9,3)"), ("Are3_20.9a31.4_", "Are3 (20,9 a 31,4)"), ("Are5_53a53_", "Are5 (53)")
    datos = {a1: [("E47_F1", 10.0), ("ECO_F1", 9.0), ("E47_F2", 2.1)], a3: [("E47_F2", 13.0), ("ECO_F2", 8.0)], a5: [("E47_F3", 20.0)]}
    grupos = [{"conjunto": c, "conjunto_legible": l, "fuerza": 1.0, "n_pares": len(v), "n_clases": len(v), "tipo": "singularidad", "posicion": i,
               "pares": [par(cl, c, l, val) for cl, val in v]} for i, ((c, l), v) in enumerate(datos.items(), 1)]
    return dict(_h(), n_clases=5, grupos=grupos)


def test_familias_de_clases_con_su_conjunto_principal():
    f = {x["base"]: [(p["clase"], p["conjunto"]) for p in x["pasos"]] for x in redaccion._familias(_h_familias())}
    assert f["E47"] == [("E47_F1", "Are1 (1,3 a 9,3)"), ("E47_F2", "Are3 (20,9 a 31,4)"), ("E47_F3", "Are5 (53)")]   # E47_F2: gana Are3 (13,0 > 2,1)
    assert f["ECO"] == [("ECO_F1", "Are1 (1,3 a 9,3)"), ("ECO_F2", "Are3 (20,9 a 31,4)")]


def test_no_hay_familias_si_las_clases_son_numericas_o_simples():
    assert redaccion._familias(_h()) == []
    h = _h_familias(); h["grupos"][0]["pares"][0]["clase"] = "76"
    assert redaccion._familias(h) == []


def test_el_prompt_trae_las_familias_y_el_ejemplo_de_estilo():
    p = redaccion.armar_prompt(_h_familias())
    assert "Comparación entre grupos de clases en cada nivel" in p and "Recorrido de cada familia" not in p
    assert "EJEMPLO DE ESTILO" in p and "Hallazgos para el grupo de Ingresos Altos" in p and "valor test de 4,50" in p
    assert "Lectura por familias" not in redaccion.armar_prompt(_h())


def test_el_ejemplo_de_estilo_del_novato_no_trae_valor_test():
    h = _h_familias(); h.update(perfil="novato", visibles=dict(valor_test=False, p_valor=False, class_cat=False, razon=False))
    p = redaccion.armar_prompt(h)
    assert "Ingresos Altos" in p and "V-test" not in p and "4,50" not in p


def test_los_componentes_de_un_nombre_compuesto_no_son_valores_ajenos():
    h = _h_familias()
    t = "E47 pasa de E47_F1 en Are1 (1,3 a 9,3) a E47_F2 en Are3 (20,9 a 31,4) y a E47_F3 en Are5 (53); en F2 y F3 sigue."
    assert redaccion.verificar([t], h, redaccion.datos_prompt(h)) == []
    assert redaccion.verificar(["En F7 se concentra."], h, redaccion.datos_prompt(h)) == ["7"]


@pytest.mark.parametrize("texto", ["Predomina el uso del automóvil.", "Se prefiere la bicicleta.", "Es el transporte motorizado.", "Los ingresos altos."])
def test_copiar_el_ejemplo_se_rechaza(texto):
    assert redaccion.verificar_afirmaciones([texto], _h(n_no_significativas=3))   # también con no significativas declaradas


def test_gemini_recibe_un_limite_de_salida_mayor_que_el_de_ollama():
    assert redaccion.llm.MAX_RESPUESTA_GEMINI >= 8192 > redaccion.llm.MAX_RESPUESTA >= 4096


# ─── Falsos rechazos de la corrida con el ejemplo de estilo ──────────────────

def test_una_oracion_de_transicion_puede_nombrar_al_vecino_junto_a_clases_ajenas():
    h = _h_familias()
    t = "El conjunto concentra a las clases E47_F2 y ECO_F2, con una transición con Are1 (1,3 a 9,3)."
    h["grupos"][1]["pares"][0]["transicion"] = "Are1_1.3a9.3_"; h["grupos"][0]["pares"][0]["transicion"] = "Are3_20.9a31.4_"
    assert redaccion.verificar_relaciones([t], h, h["grupos"][1]) == []


def test_los_demas_conjuntos_pueden_tener_otro_conteo_que_los_citados():
    h = _h_familias()          # Are1 tiene 3 asociaciones; Are3 y Are5, 2 y 1
    assert redaccion.verificar_relaciones(["Are1 (1,3 a 9,3) tiene 3 asociaciones y los demás conjuntos presentan 2 asociaciones."], h) == []
    assert redaccion.verificar_relaciones(["Are1 (1,3 a 9,3) tiene 7 asociaciones."], h)       # un conteo inventado se sigue rechazando


# ─── Escala: el prompt tiene un tope que no depende de la cantidad de datos ──

def _h_grande(grupos=300, pares=200):
    def par(i, g, k):
        return {"id": f"P{g}-{k}", "clase": f"{k + 1}", "caracteristica": f"Set{g}_1a2_", "caracteristica_legible": f"Set{g} (1 a 2)",
                "valor_test": 50.0 - k * 0.01, "valor_test_txt": f"{50.0 - k * 0.01:.3f}".replace(".", ","), "p_texto": "p < 0,01", "class_cat": 1.0,
                "cat_class": 2.0, "global": 0.5, "razon": 4.0, "significacion": "altamente significativo", "direccion": "sobre-representación",
                "intensidad": "fuerte", "peso_bajo": True, "transicion": ""}
    gs = [{"conjunto": f"Set{g}_1a2_", "conjunto_legible": f"Set{g} (1 a 2)", "fuerza": 1000.0 - g, "fuerza_txt": f"{1000 - g},000", "n_pares": pares,
           "n_clases": pares, "tipo": "singularidad", "posicion": g + 1, "pares": [par(0, g, k) for k in range(pares)]} for g in range(grupos)]
    return dict(_h(), grupos=gs, n_pares=grupos * pares, n_significativas=grupos * pares, n_clases=pares)


@pytest.mark.parametrize("grupos, pares", [(3, 5), (50, 50), (300, 200)])
def test_el_prompt_no_crece_con_los_datos(grupos, pares):
    pd = redaccion.datos_prompt(_h_grande(grupos, pares))
    assert pd["n_grupos"] == grupos and pd["n_grupos_detallados"] == min(grupos, redaccion.MAX_GRUPOS)
    assert pd["n_detalladas"] <= max(redaccion.MAX_DETALLE, redaccion.MAX_GRUPOS * redaccion.MIN_POR_GRUPO)
    assert len(redaccion.armar_prompt(_h_grande(grupos, pares), pd)) < 16000


def test_el_prompt_dice_que_hay_mas_conjuntos_y_asociaciones_sin_detallar():
    h = _h_grande(30, 100)
    p = redaccion.armar_prompt(h)
    assert "Hay 30 conjuntos en total; arriba se detallan los 8" in p and "asociaciones más de menor relevancia" in p
    assert "Set29" not in p and "Set20" not in p                # el modelo no recibe los conjuntos que no se detallan, ni como lista de repetidas
    assert "Set0 (1 a 2)" in p and "Hay 30 conjuntos" not in redaccion.armar_prompt(_h_grande(5, 100))


def test_los_conjuntos_que_no_se_detallan_los_resume_el_codigo():
    h = _h_grande(12, 30)
    t = "\n\n".join(f"Hallazgos para el conjunto Set{g} (1 a 2): la clase 1 se asocia de forma fuerte." for g in range(8))
    texto, respaldo, rechazados = redaccion._hallazgos_por_grupo(t, h, redaccion.datos_prompt(h))
    assert respaldo == [] and rechazados == []                # los 4 conjuntos restantes no cuentan como rechazo
    assert texto.endswith("Otros 4 conjuntos, con 120 asociaciones en total, no se detallan en esta síntesis: "
                          "Set8 (1 a 2), Set9 (1 a 2), Set10 (1 a 2), Set11 (1 a 2).")


def test_los_numeros_del_recorte_son_datos_permitidos_y_otros_no():
    h = _h_grande(30, 100)
    pd = redaccion.datos_prompt(h)
    assert redaccion.verificar(["Hay 30 conjuntos; se detallan 8 y 3000 asociaciones."], h, pd) == []
    assert redaccion.verificar(["Set0 (1 a 2) tiene 77 asociaciones más."], h, pd) == ["77"]


def test_resto_de_asociaciones_viaja_como_vectores_y_se_reexpande():
    h = {"grupos": [{"conjunto": "A_1a2_", "pares": [{"id": "a", "clase": "c1"}],
                     "resto": {"id": ["b", "c"], "clase": ["c2", "c3"], "valor_test": [3.5, 2.7], "transicion": ["", "X"]}},
                    {"conjunto": "B_1a2_", "pares": [], "resto": {"id": "z", "clase": "c9", "valor_test": 1.7, "transicion": ""}}]}
    r = redaccion._expandir_resto(h)["grupos"]
    assert [p["clase"] for p in r[0]["pares"]] == ["c1", "c2", "c3"] and r[0]["pares"][2]["transicion"] == "X"
    assert [p["id"] for p in r[1]["pares"]] == ["z"] and "resto" not in r[0]       # un vector de un elemento llega como escalar


def test_las_familias_tienen_tope():
    h = _h_grande(3, 5)
    for g in h["grupos"]:
        for k, p in enumerate(g["pares"]):
            p["clase"] = f"X{k // 2}_T{k % 2}"
    assert len(redaccion._familias(h)) <= redaccion.MAX_FAMILIAS


# ─── Lectura cruzada: qué tienen en común las clases, comparación entre familias, desglose en variables ──

def _h_cf(variables=None):
    """Los 12 pares del caso Cepa × Fecha: 9 clases «cepa_fecha» y 5 conjuntos."""
    def par(c, cat, leg, v):
        return {"id": f"{c}-{cat}", "clase": c, "caracteristica": cat, "caracteristica_legible": leg, "valor_test": v, "valor_test_txt": f"{v:.3f}".replace(".", ","),
                "p_texto": "p < 0,01", "class_cat": 10.0, "cat_class": round(40.0 + v, 1), "global": 20.0, "razon": 2.0, "significacion": "altamente significativo",
                "direccion": "sobre-representación", "intensidad": "fuerte", "peso_bajo": False, "transicion": ""}
    sets = {("Are1_1.3a9.3_", "Are1 (1,3 a 9,3)"): [("E47_F1", 10.9), ("ECO_F1", 11.8), ("FLO_F1", 13.4)],
            ("Are2_9.3a20.9_", "Are2 (9,3 a 20,9)"): [("ECO_F2", 8.0), ("FLO_F2", 10.4)],
            ("Are3_20.9a31.4_", "Are3 (20,9 a 31,4)"): [("E47_F2", 13.6), ("ECO_F2", 3.5), ("ECO_F3", 2.4)],
            ("Are4_31.4a43.4_", "Are4 (31,4 a 43,4)"): [("ECO_F3", 11.9), ("FLO_F3", 7.9)],
            ("Are5_53a53_", "Are5 (53)"): [("E47_F3", 20.2), ("ECO_F3", 2.0)]}
    grupos = [{"conjunto": c, "conjunto_legible": l, "fuerza": 50.0 - i, "fuerza_txt": f"{50 - i},000", "n_pares": len(v), "n_clases": len(v), "tipo": "singularidad",
               "posicion": i + 1, "pares": [par(cl, c, l, val) for cl, val in v]} for i, ((c, l), v) in enumerate(sets.items())]
    h = dict(_h(), n_clases=9, n_pares=12, n_significativas=12, grupos=grupos, descripcion="grupos")
    if variables:
        h["variables"] = variables
    return h


def test_que_tienen_en_comun_las_clases_de_cada_conjunto():
    c, numeros = redaccion._comunes(_h_cf(["Cepa", "Fecha"]), 5)
    por = {x["conjunto"]: x["lineas"] for x in c}
    assert por["Are1 (1,3 a 9,3)"] == ["Cepa: hay clases con cepa E47 (1), ECO (1), FLO (1)",
                                      "Fecha: todas las clases tienen fecha F1 (son las 3 que hay con F1 en el análisis)"]
    assert "todas las clases tienen fecha" not in por["Are3 (20,9 a 31,4)"][1] and "F2 (2), F3 (1)" in por["Are3 (20,9 a 31,4)"][1]
    assert {"3", "1", "2"} <= numeros


def test_sin_nombres_de_variables_los_componentes_se_numeran():
    c, _ = redaccion._comunes(_h_cf(), 5)
    assert c[0]["lineas"][0] == "las clases empiezan con E47 (1), ECO (1), FLO (1)"
    assert c[0]["lineas"][1].startswith("todas las clases terminan en F1 (son las 3 que hay con F1")
    assert not any("parte del nombre" in l or "componente" in l for l in c[0]["lineas"])


def test_comparacion_entre_familias_en_cada_nivel():
    comp = redaccion._comparacion(_h_cf())
    assert comp[0] == "F1: las 3 familias (E47, ECO, FLO) se asocian sobre todo con Are1 (1,3 a 9,3)"
    assert comp[1] == ("F2: E47 se asocia sobre todo con Are3 (20,9 a 31,4); ECO y FLO se asocian sobre todo con Are2 (9,3 a 20,9). "
                       "Are3 (20,9 a 31,4) es un conjunto de valores más altos que Are2 (9,3 a 20,9)")
    assert comp[2].startswith("F3: E47 se asocia sobre todo con Are5 (53); ECO y FLO se asocian sobre todo con Are4 (31,4 a 43,4)")


def test_no_hay_lectura_cruzada_con_clases_simples_o_numericas():
    h = _h()
    assert redaccion._comunes(h, 4) == ([], set()) and redaccion._comparacion(h) == []


def test_desglose_de_la_clase_en_variables():
    assert redaccion._desglose("E47_F3", ["Cepa", "Fecha"]) == "cepa E47, fecha F3"
    assert redaccion._desglose("E47_F3", ["Cepa"]) == "" and redaccion._desglose("E47_F3", []) == "" and redaccion._desglose("76", ["Cepa"]) == ""


def test_el_prompt_lleva_la_lectura_cruzada_y_el_desglose():
    p = redaccion.armar_prompt(_h_cf(["Cepa", "Fecha"]))
    assert "Qué tienen en común las clases de cada conjunto" in p and "Fecha: todas las clases tienen fecha F1" in p
    assert "Comparación entre grupos de clases en cada nivel" in p and "Fecha F1: las 3 cepas (E47, ECO, FLO)" in p
    assert "E47_F1 (cepa E47, fecha F1)" in p and "«E47_F1» es cepa E47, fecha F1" in p and "es el de valores más bajos" in p
    assert "En conjunto: en las clases con fecha F2 y F3, las de cepa E47 tienen siempre su asociación principal en un conjunto de valores más altos que las de cepa ECO y FLO" in p
    sin = redaccion.armar_prompt(_h_cf())
    assert "E47_F1 (cepa" not in sin and "todas las clases terminan en F1" in sin and "No se conocen los nombres de las variables" in sin
    h = _h_cf(["Cepa", "Fecha"]); h["contexto"] = "Área de colonias de tres cepas."
    assert "CONTEXTO DEL ESTUDIO (lo escribió quien hizo el análisis): Área de colonias de tres cepas." in redaccion.armar_prompt(h)
    assert "CONTEXTO DEL ESTUDIO" not in p


def test_las_cantidades_de_la_lectura_cruzada_son_datos_permitidos():
    h = _h_cf(["Cepa", "Fecha"])
    pd = redaccion.datos_prompt(h)
    t = "Las 3 clases comparten F1 y en total hay 3 clases con F1; en F2 se separan: la cepa E47 va a Are3 (20,9 a 31,4)."
    assert redaccion.verificar([t], h, pd) == []
    assert redaccion.verificar(["Las 7 clases comparten F1."], h, pd) == ["7"]


def test_un_texto_con_cepa_y_fecha_en_palabras_pasa_los_controles():
    h = _h_cf(["Cepa", "Fecha"])
    pd = redaccion.datos_prompt(h)
    t = "Hallazgos para el conjunto Are1 (1,3 a 9,3): la cepa E47 en la fecha F1, la cepa ECO en la fecha F1 y la cepa FLO en la fecha F1."
    assert redaccion.verificar([t], h, pd) == [] and redaccion.verificar_relaciones([t], h, h["grupos"][0]) == []


def test_las_cantidades_de_clases_de_la_lectura_cruzada_no_son_falsos_rechazos():
    h = _h_cf(["Cepa", "Fecha"])
    for t in ("Las 3 clases comparten F1.", "Las 3 clases comparten la fecha F1, y en total hay 3 clases con F1.", "Las 2 clases comparten F2."):
        assert redaccion.verificar_relaciones([t], h) == [], t
    assert redaccion.verificar_relaciones(["Las 8 clases comparten F1."], h)                # un conteo inventado se sigue rechazando
    assert redaccion.verificar_relaciones(["Se analizaron 3 clases."], h) == []             # 3 es la cantidad de un conjunto; 9 es el total
    assert redaccion.verificar_relaciones(["Se analizaron 8 clases."], h)


def test_un_nombre_de_clase_inventado_se_rechaza():
    h = _h_cf(["Cepa", "Fecha"])
    assert redaccion.verificar_relaciones(["FLO transita de FLO_F1 a FLO_F2 y a FLO_F4."], h) == ["«FLO_F4» no es una clase ni un conjunto del análisis"]
    assert redaccion.verificar_relaciones(["FLO transita de FLO_F1 a FLO_F2 y a FLO_F3."], h) == []
    assert redaccion.verificar_relaciones(["Are1_1.3a9.3_ concentra E47_F1."], h) == []      # el nombre del conjunto tal como figura en DaFu


def test_pocos_datos_sin_peso_bajo_se_rechaza_y_con_peso_bajo_se_acepta():
    h = _h_cf()
    assert redaccion.verificar_afirmaciones(["Este conjunto se apoya en pocos datos."], h) == ["dice que una asociación se apoya en pocos datos, y ninguna figura así"]
    h["grupos"][0]["pares"][0]["peso_bajo"] = True
    assert redaccion.verificar_afirmaciones(["Esta asociación se apoya en pocos datos."], h) == []


# ─── Atribución: cada cifra junto a su clase (el error de la corrida del experto) ──

def _atr(texto, variables=None):
    h = _h_cf(variables)
    return redaccion.verificar_atribuciones([texto], h, redaccion.datos_prompt(h))


def test_un_valor_test_atribuido_a_otra_clase_se_rechaza():
    # el caso real: «la cepa E47 en la fecha F1 (V-test: 13,400 …)», cuando 13,400 es de FLO_F1
    mal = "Presenta una sobre-representación fuerte para la clase E47_F1 (V-test: 13,400; 53,4 % frente al 20,0 % del total)."
    assert _atr(mal) == ["atribuye 13,400 a E47_F1, pero ese valor es de FLO_F1", "atribuye 53,4 a E47_F1, pero ese valor es de FLO_F1"]
    con_vars = "Hay una sobre-representación fuerte para la cepa E47 en la fecha F1 (V-test: 13,400)."
    assert _atr(con_vars, ["Cepa", "Fecha"]) == ["atribuye 13,400 a E47_F1, pero ese valor es de FLO_F1"]


def test_cada_valor_junto_a_su_clase_pasa():
    bien = ("FLO_F1 (V-test: 13,400; 53,4 % frente al 20,0 % del total), ECO_F1 (V-test: 11,800; 51,8 %) y "
            "E47_F1 (V-test: 10,900; 50,9 %).")
    assert _atr(bien) == []
    assert _atr("La cepa FLO en la fecha F1 tiene V-test 13,400.", ["Cepa", "Fecha"]) == []


def test_una_lista_de_clases_seguida_de_sus_valores_no_es_un_falso_rechazo():
    assert _atr("Las clases ECO_F1 y FLO_F1 tienen valores test de 11,800 y 13,400.") == []


def test_los_porcentajes_del_total_no_se_toman_como_atribuciones():
    assert _atr("E47_F1 muestra un 50,9 % frente al 20,0 % del total.") == []          # 20,0 es el Global, no el de otra clase


def test_un_texto_atribuido_mal_pasa_al_respaldo_con_su_motivo(tmp_path):
    mal = "Hallazgos para el conjunto Are1 (1,3 a 9,3): E47_F1 tiene un V-test de 13,400."
    h = _h_cf()
    h["texto_s2"] = "1. a\n2. b\n3. c\n4. d\n5. e"
    ok = [f"Hallazgos para el conjunto {l}: {c}." for l, c in (("Are2 (9,3 a 20,9)", "FLO_F2"), ("Are3 (20,9 a 31,4)", "E47_F2"),
                                                           ("Are4 (31,4 a 43,4)", "FLO_F3"), ("Are5 (53)", "E47_F3"))]
    ruta = tmp_path / "hallazgos.json"
    ruta.write_text(json.dumps(h, ensure_ascii=False), encoding="utf-8")
    gen = lambda prompt: json.dumps({"S1": "Se analizaron 9 clases.", "S2": "\n\n".join([mal] + ok), "S3": "Sólo las asociaciones listadas superan el umbral."})
    s = json.load(open(redaccion.redactar_sintesis(str(ruta), KB, generar=gen), encoding="utf-8"))
    assert s["estado"] == "parcialmente redactada"
    assert any("atribuye 13,400 a E47_F1" in m for r in s["rechazados"] for m in r["motivos"])


def test_el_prompt_no_pide_decir_pocos_datos_si_ninguna_asociacion_lo_tiene():
    h = _h_cf()
    sin = redaccion.armar_prompt(h)
    assert "no digas que ninguna asociación se apoya en pocos datos" in sin and "figura como «se apoya en pocos datos»" not in sin
    h["grupos"][0]["pares"][0]["peso_bajo"] = True
    con = redaccion.armar_prompt(h)
    assert "figura como «se apoya en pocos datos»" in con


def test_la_descripcion_general_no_pide_tecnicas_ni_metodos():
    p = redaccion.armar_prompt(_h_cf())
    assert "no menciones técnicas, métodos ni objetivos del estudio" in p


def test_el_recorrido_de_una_familia_solo_cita_sus_conjuntos():
    import redaccion as r
    h = {"archivo": "x", "n_clases": 4, "n_categorias": 3, "n_significativas": 4, "n_pares": 4, "grupos": [
        {"conjunto": "Are1", "tipo": "t", "n_pares": 2, "pares": [{"clase": "E_F1", "valor_test": 9, "transicion": "Are2"}, {"clase": "C_F1", "valor_test": 8}]},
        {"conjunto": "Are2", "tipo": "t", "n_pares": 1, "pares": [{"clase": "E_F2", "valor_test": 9, "transicion": "Are1"}]},
        {"conjunto": "Are3", "tipo": "t", "n_pares": 1, "pares": [{"clase": "C_F2", "valor_test": 9}]}]}
    assert r.verificar_relaciones(["La familia C transita de Are1 a Are3."], h) == []
    assert any("no recorre Are3" in p for p in r.verificar_relaciones(["La familia E transita de Are1 a Are3."], h))


def test_se_quitan_las_oraciones_sin_cifras_repetidas_entre_parrafos():
    import redaccion as r
    h = {"grupos": [{"conjunto": "Are1", "pares": [{"clase": "E_F1"}]}, {"conjunto": "Are2", "pares": [{"clase": "E_F2"}]}]}
    a, b = r._quitar_repetidas([
        "Hallazgos para el conjunto Are1: Este conjunto se asocia con pocas clases y es singular. E_F1 tiene 5,2 %.",
        "Hallazgos para el conjunto Are2: Este conjunto se asocia con pocas clases y es singular. E_F2 tiene 6,1 %."], h)
    assert "pocas clases" in a and "pocas clases" not in b and "6,1 %" in b and b.startswith("Hallazgos para el conjunto Are2:")


def test_la_comparacion_cierra_con_la_conclusion_de_conjunto():
    comp = redaccion._comparacion(_h_cf())
    assert comp[-1] == "En conjunto: en F2 y F3, E47 tiene siempre su asociación principal en un conjunto de valores más altos que ECO y FLO"


def test_se_podan_las_oraciones_sin_cifras_que_los_datos_no_respaldan():
    import redaccion as r
    t = ("La cepa FLO [cepa FLO, fecha F1] tiene el 89,3 % en la primera fecha. Esto muestra una fuerte expansión inicial. "
         "Todos los patrones son singularidades.")
    out = r._podar(t)
    assert "(cepa FLO, fecha F1)" in out and "[" not in out and "89,3 %" in out
    assert "expansión" not in out and "singularidades" not in out
    assert r._podar("Todo es singularidad.") == "Todo es singularidad."      # nunca vacía el texto


def test_cada_nivel_tiene_su_guia_y_su_ejemplo():
    def prompt(perfil, visibles):
        h = _h_cf(["Cepa", "Fecha"]); h.update(perfil=perfil, visibles=visibles)
        return redaccion.armar_prompt(h)
    nov = prompt("novato", dict(valor_test=False, p_valor=False, class_cat=False, razon=False))
    inter = prompt("intermedio", dict(valor_test=True, p_valor=False, class_cat=False, razon=False))
    exp = prompt("experto", dict(valor_test=True, p_valor=True, class_cat=True, razon=True))
    assert "GUÍA DE REDACCIÓN PARA EL LECTOR NOVATO" in nov and "frases cortas" in nov and "mucho más de lo esperable" in nov
    assert "valor test" not in nov and "V-test" not in nov and "Class.Cat" not in nov                   # nada de jerga para el novato
    assert "GUÍA DE REDACCIÓN PARA EL LECTOR INTERMEDIO" in inter and "valor test de 4,50" in inter and "Class.Cat 31,2" not in inter
    assert "GUÍA DE REDACCIÓN PARA EL LECTOR EXPERTO" in exp and "Class.Cat 31,2 %" in exp and "razón de proporciones 1,78" in exp
    assert "Explica qué es el porcentaje" in nov and "Explica qué es el porcentaje" in inter and "No expliques qué es el porcentaje" in exp
    assert len({nov.split("EJEMPLO DE ESTILO")[1], inter.split("EJEMPLO DE ESTILO")[1], exp.split("EJEMPLO DE ESTILO")[1]}) == 3
