"""Pruebas de la auditoría del 09/11/2026: fallos encontrados al revisar todo el sistema. Ninguna usa la red ni una clave real."""
import copy
import json
import os
import re
import subprocess
import sys

import pytest

AIDA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(AIDA, "python"))
sys.path.insert(0, os.path.dirname(__file__))
import redaccion  # noqa: E402
from test_clases_numericas import _h, _h_cf  # noqa: E402

KB = os.path.join(AIDA, "kb", "base_conocimiento.json")
DAFU_APP = os.path.join(AIDA, "..", "DaFu", "03_AsociacionesDifusas", "app.R")


def _con_tipos_distintos():
    h = _h_cf(["Cepa", "Fecha"])
    h["grupos"][0]["tipo"] = "patrón constante"
    return h


# ─── El tipo de patrón sólo se informa cuando distingue a unos conjuntos de otros ─────────────────────────────

def test_si_todos_los_conjuntos_tienen_el_mismo_tipo_el_prompt_no_lo_nombra():
    p = redaccion.armar_prompt(_h_cf(["Cepa", "Fecha"]))
    datos = p.split("DATOS VALIDADOS")[1].split("EJEMPLO DE ESTILO")[0]
    assert "Conjuntos por tipo de patrón" not in p and "singularidad" not in datos
    assert "No hables del tipo de patrón" in p


def test_si_los_tipos_difieren_el_prompt_los_da_y_pide_decirlos():
    p = redaccion.armar_prompt(_con_tipos_distintos())
    assert "Conjuntos por tipo de patrón" in p and "- patrón constante: 1 conjunto" in p and "- singularidad: 4 conjuntos" in p
    assert "asociaciones; patrón constante" in p and "qué conjuntos se asocian con muchas clases y cuáles con pocas" in p


def test_la_poda_respeta_el_tipo_de_patron_cuando_informa():
    frase = "Todos los conjuntos son singularidades."
    resto = "E47_F1 tiene el 50,9 %."
    assert "singularidades" not in redaccion._podar(resto + " " + frase)
    assert "singularidades" in redaccion._podar(resto + " " + frase, con_tipos=True)


# ─── La poda no confunde nombres propios con cifras ni con jerga ─────────────────────────────────────────────

def test_la_poda_no_toma_el_numero_de_un_nombre_como_cifra():
    t = "La cepa E47 en la fecha F3 tiene el 60,2 %. Esto muestra la mayor expansión del área en la fecha F3."
    assert "expansión" in redaccion._podar(t)                                   # sin nombres, «F3» parecía una cifra
    assert "expansión" not in redaccion._podar(t, {"E47", "F3", "E47_F3"})


def test_la_poda_no_quita_una_oracion_por_el_nombre_de_una_clase():
    t = "Crecimiento_Alto tiene el 60,2 %. El conjunto reúne a Crecimiento_Alto y a Evolucion_Baja."
    assert redaccion._podar(t, {"Crecimiento_Alto", "Evolucion_Baja"}) == t


# ─── «El de valores más altos» sólo se afirma si se sabe ─────────────────────────────────────────────────────

def test_sin_la_lista_de_conjuntos_el_mas_alto_se_dice_entre_los_que_figuran():
    h = _h_cf()
    pos = {g["conjunto"].split("_")[0]: redaccion._posicion(g, h) for g in h["grupos"]}
    assert pos["Are1"] == "el de valores más bajos" and pos["Are3"] == "de valores intermedios"
    assert pos["Are5"] == "el de valores más altos entre los conjuntos que figuran en el archivo"


def test_con_la_lista_de_conjuntos_de_la_tabla_se_sabe_cual_es_el_mas_alto():
    h = _h_cf()
    h["conjuntos_tabla"] = [g["conjunto"] for g in h["grupos"]]
    assert redaccion._posicion(h["grupos"][-1], h) == "el de valores más altos"
    h["conjuntos_tabla"].append("Are6_60a70_")                                # un conjunto sin asociaciones: Are5 ya no es el más alto
    assert redaccion._posicion(h["grupos"][-1], h) == "de valores intermedios"


def test_la_posicion_se_calcula_dentro_de_cada_variable_difusa():
    h = _h_cf()
    h["conjuntos_tabla"] = [g["conjunto"] for g in h["grupos"]] + ["Per1_0a1_", "Per2_1a2_", "Per3_2a3_", "Per4_3a4_", "Per5_4a5_", "Per6_5a6_"]
    assert redaccion._posicion(h["grupos"][-1], h) == "el de valores más altos"   # Are5 es el último de «Are», aunque haya 11 conjuntos


def test_no_se_comparan_valores_entre_variables_difusas_distintas():
    h = _h_cf()
    for g in h["grupos"]:
        if g["conjunto"].startswith("Are3"):
            g["conjunto"], g["conjunto_legible"] = "Per3_20.9a31.4_", "Per3 (20,9 a 31,4)"
    comp = redaccion._comparacion(h)
    f2 = next(l for l in comp if l.startswith("F2"))
    assert "Per3 (20,9 a 31,4)" in f2 and "más altos" not in f2                 # Per3 y Are2 no se pueden ordenar
    assert "más altos" in next(l for l in comp if l.startswith("F3"))           # Are5 y Are4, sí


def test_los_niveles_se_ordenan_con_orden_natural():
    assert sorted(["F10", "F2", "F1"], key=redaccion._orden_natural) == ["F1", "F2", "F10"]


def test_si_las_variables_no_coinciden_con_las_partes_no_hay_lectura_cruzada():
    h = _h_cf(["Cepa", "Fecha", "Lado"])                                       # las clases tienen dos partes, no tres
    assert redaccion._clases_compuestas(h) is None and redaccion._comunes(h, 5) == ([], set())
    assert redaccion._comparacion(h) == []


# ─── Controles del texto ────────────────────────────────────────────────────────────────────────────────────

def test_una_clase_ajena_nombrada_con_palabras_tambien_se_detecta():
    h = _h_cf(["Cepa", "Fecha"])
    are5 = next(i for i, g in enumerate(h["grupos"]) if g["conjunto"].startswith("Are5"))
    ok = "Este conjunto reúne a la cepa E47 en la fecha F3 y a la cepa ECO, fecha F3."
    assert redaccion._citas_ajenas_al_conjunto(ok, h, are5) == []
    mal = "Este conjunto reúne a la cepa E47 en la fecha F3 y a la cepa FLO en la fecha F3."
    assert redaccion._citas_ajenas_al_conjunto(mal, h, are5) == ["la clase FLO_F3 no pertenece al conjunto"]


def test_el_alias_de_una_clase_respeta_los_limites_de_palabra():
    rx = re.compile(redaccion._alias_clase("E47_F1", ["Cepa", "Fecha"]), re.IGNORECASE)
    assert rx.search("la cepa E47 en la fecha F1 tiene") and rx.search("E47_F1 tiene") and rx.search("cepa E47, fecha F1")
    assert not rx.search("la cepa E47 en la fecha F10 tiene") and not rx.search("E47_F10 tiene")


def test_las_palabras_del_ejemplo_no_son_copia_si_estan_en_los_propios_datos():
    h = _h_cf()
    assert redaccion.verificar_afirmaciones(["El uso del transporte es alto."], h) == ["copia datos del ejemplo de estilo del prompt"]
    propio = copy.deepcopy(h)
    propio["grupos"][0]["pares"][0]["clase"] = "Transporte_F1"                  # un análisis que sí trata de transporte
    assert redaccion.verificar_afirmaciones(["El uso del transporte es alto."], propio) == []
    con_contexto = dict(h, contexto="Encuesta de movilidad e ingresos de los hogares.")
    assert redaccion.verificar_afirmaciones(["Los ingresos altos se concentran aquí."], con_contexto) == []


def test_el_mismo_total_se_reemplaza_por_su_cifra():
    h = _h_cf()
    g = h["grupos"][0]                                                          # todas sus asociaciones: 20,0 % del total
    p = "ECO_F1 llega al 51,8 % frente al mismo total de 20,0 %. FLO_F1 alcanza el 53,4 % frente al mismo total. E47_F1, el 50,9 % frente al total mencionado."
    assert redaccion._total_explicito(p, g) == ("ECO_F1 llega al 51,8 % frente al 20,0 % del total. FLO_F1 alcanza el 53,4 % frente al 20,0 % del total. "
                                                "E47_F1, el 50,9 % frente al 20,0 % del total.")
    g["pares"][0]["global"] = 35.0                                              # si no comparten el total, no se toca
    assert redaccion._total_explicito(p, g) == p


# ─── Base de conocimiento A10-1.5: la guía de redacción de cada perfil sale de ella (RNF-3) ──────────────────

def test_la_guia_y_el_ejemplo_de_cada_perfil_estan_en_la_base_y_en_el_cypher():
    kb = json.load(open(KB, encoding="utf-8"))
    cy = open(os.path.join(AIDA, "kb", "AIDA_frames_A10.cypher"), encoding="utf-8").read()
    assert kb["metadatos"]["version"] == "A10-1.5"
    for nombre, marco in (("novato", "PerfilNovato"), ("intermedio", "PerfilIntermedio"), ("experto", "PerfilExperto")):
        perfil = kb["perfiles"][nombre]
        assert len(perfil["guia_redaccion"]) >= 3 and perfil["ejemplo_estilo"].startswith("Hallazgos para el grupo")
        for texto in perfil["guia_redaccion"] + [perfil["ejemplo_estilo"]]:
            assert texto in cy, texto
        assert kb["marcos"][marco]["slots"]["guia_redaccion"]["default"] == perfil["guia_redaccion"]
        assert kb["marcos"][marco]["slots"]["ejemplo_estilo"]["default"] == perfil["ejemplo_estilo"]
    novato = " ".join(kb["perfiles"]["novato"]["guia_redaccion"] + [kb["perfiles"]["novato"]["ejemplo_estilo"]])
    assert not re.search(r"valor test|p-valor|V-test|Class\.Cat", novato, re.IGNORECASE)


def test_el_prompt_usa_la_guia_que_traen_los_hallazgos_y_si_no_la_de_la_base():
    kb = json.load(open(KB, encoding="utf-8"))
    h = _h_cf()
    assert kb["perfiles"]["intermedio"]["guia_redaccion"][0] in redaccion.armar_prompt(h)          # sin guía en los hallazgos: la de la base
    h.update(guia_redaccion=["Guía de prueba."], ejemplo_estilo="Hallazgos para el grupo de prueba: texto.")
    p = redaccion.armar_prompt(h)
    assert "- Guía de prueba." in p and "Hallazgos para el grupo de prueba: texto." in p
    assert kb["perfiles"]["intermedio"]["guia_redaccion"][0] not in p


def test_el_prompt_no_dice_que_solo_hay_sobre_representaciones_si_hay_de_las_otras():
    h = _h_cf()
    assert "sólo hay sobre-representaciones" in redaccion.armar_prompt(h)
    h["grupos"][0]["pares"][0]["direccion"] = "sub-representación"
    assert "sólo hay sobre-representaciones" not in redaccion.armar_prompt(h)


# ─── Integración con la aplicación 03 ───────────────────────────────────────────────────────────────────────

def _generado(tmp_path):
    salida = tmp_path / "app.R"
    subprocess.run([sys.executable, os.path.join(AIDA, "tools", "integrar_app03.py"), DAFU_APP, str(salida)], check=True, capture_output=True)
    return salida.read_bytes().decode("utf-8").replace("\r\n", "\n")


@pytest.mark.skipif(not os.path.isfile(DAFU_APP), reason="la carpeta de DaFu no está junto a la de AIDA")
def test_la_app_integrada_es_la_que_genera_el_script(tmp_path):
    gen = _generado(tmp_path)
    for copia in ("integracion", "app03_AIDA"):
        actual = open(os.path.join(AIDA, copia, "app.R"), "rb").read().decode("utf-8").replace("\r\n", "\n")
        assert actual == gen, f"{copia}/app.R no coincide con lo que genera tools/integrar_app03.py"


def test_aida_server_recibe_por_parametro_todo_lo_que_usa_del_server_de_dafu():
    """aida_server se define fuera de server(): una variable de server() que no llegue por parámetro no existe al ejecutarse
    (pasó con factores(): la pestaña de AIDA daba error al pulsar el botón)."""
    sys.path.insert(0, os.path.join(AIDA, "tools"))
    import integrar_app03
    firma = re.search(r"aida_server <- function\(([^)]*)\)", integrar_app03.SERVER).group(1)
    parametros = {p.strip() for p in firma.split(",")}
    llamada = re.search(r"aida_server\(([^)]*)\)", integrar_app03.LLAMADA).group(1)
    assert [p.strip() for p in llamada.split(",")] == [p.strip() for p in firma.split(",")]
    for reactivo in ("resultados", "aida_res", "factores", "tc", "datos", "df", "ttc", "last_freq"):   # los reactiveVal de server()
        if re.search(r"(?<![\w$.])" + reactivo + r"\(", integrar_app03.SERVER):
            assert reactivo in parametros, f"aida_server usa {reactivo}() y no lo recibe"
    assert "aida_origen" not in integrar_app03.PESTANA and "fileInput" not in integrar_app03.PESTANA   # sólo el resultado de «Describir»


# ─── Atribución de cifras cuando la cifra va delante de su clase ─────────────────────────────────────────────

def test_una_cifra_delante_de_su_clase_no_es_un_falso_rechazo():
    h = _h_cf()
    pd = redaccion.datos_prompt(h)
    t = "Este conjunto reúne a ECO_F1 entre otras. Destaca el 53,4 % de los valores de FLO_F1, frente al 20,0 % del total."
    assert redaccion.verificar_atribuciones([t], h, pd) == []


def test_una_cifra_delante_de_una_clase_que_no_es_la_suya_se_rechaza():
    h = _h_cf()
    pd = redaccion.datos_prompt(h)
    t = "Destaca el 53,4 % de los valores de ECO_F1, frente al 20,0 % del total."
    assert redaccion.verificar_atribuciones([t], h, pd) == ["atribuye 53,4 a ECO_F1, pero ese valor es de FLO_F1"]


# ─── La intensidad de cada asociación: en palabras llanas para el novato, y sin cambiársela a otra ───────────

def _novato():
    h = _h_cf(["Cepa", "Fecha"])
    h.update(perfil="novato", visibles=dict(valor_test=False, p_valor=False, class_cat=False, razon=False))
    h["grupos"][-1]["pares"][1].update(intensidad="moderada")
    return h


def test_el_novato_recibe_la_intensidad_ya_dicha_en_palabras_comunes():
    kb = json.load(open(KB, encoding="utf-8"))
    cy = open(os.path.join(AIDA, "kb", "AIDA_frames_A10.cypher"), encoding="utf-8").read()
    llana = kb["perfiles"]["novato"]["intensidad_llana"]
    assert llana["sobre-representación"]["fuerte"] == "mucho más de lo esperable" and json.dumps(llana, ensure_ascii=False) in cy
    assert "intensidad_llana" not in kb["perfiles"]["experto"]
    p = redaccion.armar_prompt(_novato())
    datos = p.split("Patrones detectados")[1].split("Qué tienen en común")[0]
    assert "* Aparece mucho más de lo esperable: E47_F3 (cepa E47, fecha F3)" in datos
    assert "* Aparece algo más de lo esperable: ECO_F3 (cepa ECO, fecha F3)" in datos
    assert "representación" not in datos
    h = _novato(); h["perfil"] = "experto"; h["visibles"] = dict(valor_test=True, p_valor=True, class_cat=True, razon=True)
    assert "* Sobre-representación moderada: ECO_F3" in redaccion.armar_prompt(h)


def test_no_se_le_cambia_la_intensidad_a_una_asociacion():
    h = _novato()
    are5, are1 = h["grupos"][-1], h["grupos"][0]
    bien = ("La cepa E47 en la fecha F3 aparece mucho más de lo esperable. De forma menos marcada, la cepa ECO en la fecha F3 "
            "llega al 42,0 %: algo más de lo esperable. La asociación más fuerte es la de E47_F3.")
    assert redaccion.verificar_intensidad(bien, h, are5) == []
    mal = "Algo parecido pasa con la cepa ECO en la fecha F1, que llega al 51,8 % frente al 20,0 % del total: algo más de lo esperable."
    assert redaccion.verificar_intensidad(mal, h, are1) == ["dice que una asociación es moderada, y la de ECO_F1 es fuerte"]
    assert redaccion.verificar_intensidad("Presenta tres asociaciones moderadas.", h, are1) != []      # sin nombrar clases: las del conjunto
    assert redaccion.verificar_intensidad("ECO_F3 se asocia moderadamente y E47_F3, fuertemente.", h, are5) == []


# ─── Revisión de las redacciones (base de conocimiento A10-1.5) ──────────────────────────────────────────────

def _h_una_variable():
    """Tres clases que son los valores de una sola variable (no hay familias ni niveles), en cinco conjuntos."""
    def par(c, cat, v):
        return {"id": f"{c}-{cat}", "clase": c, "caracteristica": cat, "caracteristica_legible": cat, "valor_test": v, "p_texto": "p < 0,01",
                "class_cat": 10.0, "cat_class": round(40.0 + v, 1), "global": 20.0, "razon": 2.0, "significacion": "altamente significativo",
                "direccion": "sobre-representación", "intensidad": "fuerte", "peso_bajo": False, "transicion": ""}
    sets = {"ent1": [("ECOBIS", 9.0), ("E47BIS", 8.0)], "ent3": [("E47BIS", 7.0), ("ECOBIS", 6.0)],
            "ent2": [("FLOBIS", 5.0)], "ent4": [("FLOBIS", 4.0)], "ent5": [("FLOBIS", 3.0)]}
    grupos = [{"conjunto": c, "fuerza": 20.0 - i, "n_pares": len(v), "n_clases": len(v), "tipo": "singularidad", "posicion": i + 1,
               "pares": [par(cl, c, val) for cl, val in v]} for i, (c, v) in enumerate(sets.items())]
    h = _h_cf()
    h.update(n_clases=3, n_pares=7, n_significativas=7, grupos=grupos, variables=["Tratamiento"])
    return h


def test_con_una_sola_variable_la_clase_no_se_desglosa_y_hay_lectura_cruzada():
    h = _h_una_variable()
    pd = redaccion.datos_prompt(h)
    assert all(p["desglose"] == "" for g in pd["grupos"] for p in g["pares"])
    assert pd["variable_unica"] == "Tratamiento" and not pd["comparacion"]
    assert pd["afines"] == ["E47BIS y ECOBIS se asocian con los mismos conjuntos: ent1 y ent3; en el archivo, ninguna otra clase figura asociada con esos conjuntos",
                            "FLOBIS se asocia con ent2, ent4 y ent5; en el archivo, ninguna otra clase figura asociada con esos conjuntos"]
    p = redaccion.armar_prompt(h, pd)
    assert "Lectura cruzada de las clases" in p and "Cada clase es un valor de la variable Tratamiento" in p
    assert "Clases que más se repiten" not in p and "no alcanza para distinguir" not in p


def test_con_familias_y_niveles_no_se_agrega_la_lectura_por_clase():
    pd = redaccion.datos_prompt(_h_cf(["Cepa", "Fecha"]))
    assert pd["comparacion"] and not pd["afines"] and pd["variable_unica"] == ""


def test_un_rango_que_no_va_con_su_conjunto_se_quita():
    h = _h_cf(["Cepa", "Fecha"])
    t = "En las clases con fecha F1 (1,3 a 9,3), las 3 cepas se asocian con Are1 (1,3 a 9,3) y con el conjunto Are2 (9,3 a 20,9)."
    assert redaccion._rangos_en_su_lugar(t, h) == "En las clases con fecha F1, las 3 cepas se asocian con Are1 (1,3 a 9,3) y con el conjunto Are2 (9,3 a 20,9)."
    assert redaccion._rangos_en_su_lugar("Are1 (9,3 a 20,9) reúne a E47_F1.", h) == "Are1 reúne a E47_F1."     # el rango es de Are2


def test_las_cantidades_con_palabras_pasan_a_cifras():
    assert redaccion._cifras("Hay tres conjuntos con un total de cuatro asociaciones; el segundo es Are2.") == \
        "Hay 3 conjuntos con un total de 4 asociaciones; el segundo es Are2."
    assert redaccion._cifras("Las dos. Dos puntos.") == "Las dos. Dos puntos."
    assert redaccion._cifras("Se asocia con pocas clases, abarcando tres. Son dos, y hay cuatro.") == "Se asocia con pocas clases, abarcando 3. Son 2, y hay 4."
    assert redaccion._cifras("La clase Tres reúne dos conjuntos.", {"Tres"}) == "La clase Tres reúne 2 conjuntos."


def test_las_muletillas_se_corrigen_sin_cambiar_los_datos():
    assert redaccion._muletillas("Se asocia con una fuerza fuerte (valor test de 5,2).") == "Se asocia de forma fuerte (valor test de 5,2)."
    assert redaccion._muletillas("En conjunto, este conjunto reúne a E47.") == "En resumen, este conjunto reúne a E47."
    assert redaccion._muletillas("Este conjunto de valores es el de valores más bajos.") == "Este conjunto es el de valores más bajos."
    assert redaccion._muletillas("En conjunto, las 3 cepas coinciden.") == "En conjunto, las 3 cepas coinciden."


def test_menos_marcada_solo_se_quita_si_las_intensidades_son_iguales():
    g = _h_cf()["grupos"][0]
    t = "FLO_F1 aparece mucho más de lo esperable. Algo parecido pasa, de forma menos marcada, con ECO_F1: mucho más de lo esperable."
    assert "menos marcada" not in redaccion._sin_comparativo_falso(t, g)
    assert "pasa con ECO_F1" in redaccion._sin_comparativo_falso(t, g)
    g2 = copy.deepcopy(g); g2["pares"][1]["intensidad"] = "moderada"
    assert redaccion._sin_comparativo_falso(t, g2) == t


def test_el_cierre_que_repite_el_comienzo_se_quita():
    t = ("Hallazgos para el conjunto Are1 (1,3 a 9,3): Este conjunto reúne los valores más bajos y se asocia con las 3 cepas en la fecha F1. "
         "FLO_F1 tiene el 53,4 % frente al 20,0 % del total. En resumen, este conjunto de valores bajos reúne a las 3 cepas en la fecha F1.")
    r = redaccion._sin_cierre_repetido(t)
    assert r.endswith("del total.") and r.startswith("Hallazgos para el conjunto Are1 (1,3 a 9,3): Este conjunto")
    otro = t.replace("En resumen, este conjunto de valores bajos reúne a las 3 cepas en la fecha F1.", "E47_F1 también se asocia con el conjunto vecino, Are2.")
    assert redaccion._sin_cierre_repetido(otro) == otro


def test_la_descripcion_general_no_lleva_relleno():
    h = _h_cf()
    t = "Descripción de grupos del archivo area.txt, con 9 clases y 5 categorías."
    assert redaccion._podar_s1(t + " La descripción general detalla los patrones estadísticos. El enfoque es puramente exploratorio.", h) == t
    assert "exploratorio" in redaccion._podar_s1(t + " El enfoque es exploratorio.", dict(h, contexto="Área foliar de 3 cepas."))


def test_el_comienzo_de_un_nombre_de_tres_partes_no_deja_cifras_sueltas():
    h = _h_cf(["Cepa", "Fecha", "Lado"])
    for g in h["grupos"]:
        for p in g["pares"]:
            p["clase"] += "_D"
    pd = redaccion.datos_prompt(h)
    assert redaccion.verificar(["En el lado D, E47_F3 se asocia con Are5 (53) y E47_F2 con Are3 (20,9 a 31,4)."], h, pd) == []


def test_al_novato_se_le_pide_la_transicion_sin_esa_palabra():
    h = _h_cf(["Cepa", "Fecha"])
    h.update(perfil="novato", visibles=dict(valor_test=False, p_valor=False, class_cat=False, razon=False))
    assert "no hay transiciones" in redaccion.armar_prompt(h)                  # sin transiciones, no se habla de vecinos
    h["grupos"][0]["pares"][0]["transicion"] = "Are2_9.3a20.9_"; h["grupos"][1]["pares"][0]["transicion"] = "Are1_1.3a9.3_"
    assert "sin usar la palabra «transición»" in redaccion.armar_prompt(h)
    assert "sin usar la palabra «transición»" not in redaccion.armar_prompt(_h_cf(["Cepa", "Fecha"]))


def test_frente_al_total_sin_cifra_recupera_la_cifra_y_el_cierre_con_plurales_se_reconoce():
    g = _h_cf()["grupos"][0]
    assert redaccion._total_explicito("ECO_F1 llega al 51,8 % frente al total.", g) == "ECO_F1 llega al 51,8 % frente al 20,0 % del total."
    assert redaccion._total_explicito("ECO_F1 llega al 51,8 % frente al 20,0 % del total.", g) == "ECO_F1 llega al 51,8 % frente al 20,0 % del total."
    t = ("Hallazgos para el conjunto Are4 (31,4 a 43,4): Este conjunto reúne valores intermedios, y se asocia con clases con cepa ECO y FLO que tienen fecha F3. "
         "La cepa ECO en la fecha F3 llega al 52,9 % frente al 13,3 % del total. Este conjunto reúne valores intermedios y concentra a las cepas ECO y FLO en la fecha F3.")
    assert redaccion._sin_cierre_repetido(t).endswith("del total.")


# ─── A10-1.5: respaldo llano, reintento, p-valor del experto y relleno de la conclusión ───────────────────────

def _escribir(tmp_path, h):
    ruta = tmp_path / "hallazgos.json"
    ruta.write_text(json.dumps(h, ensure_ascii=False), encoding="utf-8")
    return str(ruta)


def _s2_bueno(h, malo=None):
    partes = []
    for g in h["grupos"]:
        n = g["conjunto_legible"]
        partes.append(malo if (malo and n.startswith("Are2")) else f"Hallazgos para el conjunto {n}: se asocia de forma fuerte con {g['pares'][0]['clase']}.")
    return "\n\n".join(partes)


def test_el_respaldo_del_novato_es_un_parrafo_llano_sin_jerga(tmp_path):
    h = _h_cf(["Cepa", "Fecha"])
    h.update(perfil="novato", visibles=dict(valor_test=False, p_valor=False, class_cat=False, razon=False), texto_s2="")
    malo = "Hallazgos para el conjunto Are2 (9,3 a 20,9): ECO_F2 llega al 99,9 %."
    falso = lambda prompt: json.dumps({"S1": "Hay 9 clases.", "S2": _s2_bueno(h, malo), "S3": "E47_F3 se asocia con Are5 (53)."})
    s = json.load(open(redaccion.redactar_sintesis(_escribir(tmp_path, h), KB, "simulado", falso), encoding="utf-8"))
    t = s["secciones"][1]["texto"]
    assert s["estado"] == "parcialmente redactada" and "99,9" not in t
    assert "Hallazgos para el conjunto Are2 (9,3 a 20,9): Este conjunto se asocia con 2 clases." in t
    assert "ECO_F2 (cepa ECO, fecha F2) aparece mucho más de lo esperable: el 48,0 % de sus valores está en este conjunto, frente al 20,0 % del total." in t
    assert "singularidad" not in t and "valor test" not in t.lower()


def test_un_parrafo_rechazado_se_pide_de_nuevo_y_si_verifica_se_usa(tmp_path):
    h = _h_cf(["Cepa", "Fecha"])
    malo = "Hallazgos para el conjunto Are2 (9,3 a 20,9): ECO_F2 llega al 99,9 %."
    pedidos = []

    def falso(prompt):
        pedidos.append(prompt)
        return json.dumps({"S1": "Hay 9 clases.", "S2": _s2_bueno(h, malo if len(pedidos) == 1 else None), "S3": "E47_F3 se asocia con Are5 (53)."})
    s = json.load(open(redaccion.redactar_sintesis(_escribir(tmp_path, h), KB, "simulado", falso), encoding="utf-8"))
    assert len(pedidos) == 2 and "CORRECCIÓN" in pedidos[1] and "Conjunto Are2 (9,3 a 20,9)" in pedidos[1] and "area.txt" not in pedidos[1]
    assert s["estado"] == "redactada" and "99,9" not in s["secciones"][1]["texto"]
    assert "Hallazgos para el conjunto Are2 (9,3 a 20,9): se asocia de forma fuerte con ECO_F2." in s["secciones"][1]["texto"]
    assert [r["texto"] for r in s["rechazados"]] == [malo]


def test_al_experto_se_le_marca_el_p_valor_que_no_alcanza_el_5_por_ciento():
    h = _h_cf(["Cepa", "Fecha"])
    h.update(perfil="experto", visibles=dict(valor_test=True, p_valor=True, class_cat=True, razon=True))
    g = h["grupos"][4]
    g["pares"][1].update(p_valor=0.071, p_texto="p = 0,071", intensidad="débil", class_cat=16.5)
    g["pares"][0].update(p_valor=0.0)
    pd = redaccion.datos_prompt(h)
    t = "E47_F3 (valor test: 20,200; p < 0,01) y ECO_F3 (valor test: 2,000; p = 0,071; 42,0 % frente al 20,0 % del total; Class.Cat 16,5 %)."
    r = redaccion._pulir(t, h, pd, g)
    assert "p = 0,071, no significativa al 5 %; 42,0 %" in r and r.count("no significativa") == 1
    assert redaccion._pulir(r, h, pd, g) == r
    assert redaccion.verificar([r], h, pd) == []
    h["perfil"] = "intermedio"; h["visibles"]["p_valor"] = False
    assert "no significativa" not in redaccion._pulir(t, h, redaccion.datos_prompt(h), g)


def test_la_explicacion_del_valor_test_pasa_a_ser_oracion_propia():
    h = _h_cf(["Cepa", "Fecha"])
    pd = redaccion.datos_prompt(h)
    t = "ECO_F2 se asocia con este conjunto (valor test 8,000); el valor test mide cuán improbable es que la asociación sea casual, no cuán intensa es."
    r = redaccion._pulir(t, h, pd, h["grupos"][1])
    assert r == "ECO_F2 se asocia con este conjunto (valor test 8,000). El valor test mide cuán improbable es que la asociación sea casual, no cuán intensa es."
    assert redaccion._pulir(r, h, pd, h["grupos"][1]) == r
    enc = "Hallazgos para el conjunto Are2 (9,3 a 20,9): el valor test indica la significación de la asociación."
    assert redaccion._explicacion_aparte(enc) == enc                            # el encabezado del conjunto no se parte


def test_el_novato_debe_decir_la_intensidad_de_cada_nivel():
    h = _h_cf(["Cepa", "Fecha"])
    h["perfil"] = "novato"
    g = h["grupos"][1]
    g["pares"][1].update(intensidad="moderada")
    h["intensidad_llana"] = {"sobre-representación": {"fuerte": "mucho más de lo esperable", "moderada": "algo más de lo esperable"}}
    gp = redaccion.datos_prompt(h)["grupos"][1]
    sin = "ECO_F2 está en este conjunto el 48,0 % frente al 20,0 % del total. FLO_F2 llega al 50,4 % frente al 20,0 % del total."
    assert len(redaccion.verificar_intensidad_dicha(sin, g, gp)) == 2
    con = "ECO_F2 aparece mucho más de lo esperable: 48,0 % frente al 20,0 % del total. FLO_F2 aparece algo más de lo esperable: 50,4 % frente al 20,0 % del total."
    assert redaccion.verificar_intensidad_dicha(con, g, gp) == []


def test_el_limite_del_nombre_de_un_conjunto_no_se_atribuye_a_una_clase():
    h = _h_cf(["Cepa", "Fecha"])
    h.update(perfil="experto", visibles=dict(valor_test=True, p_valor=True, class_cat=True, razon=True))
    h["grupos"][0]["pares"][0]["class_cat"] = 1.3                   # coincide con el límite de «Are1 (1,3 a 9,3)»
    pd = redaccion.datos_prompt(h)
    t = "Hallazgos para el conjunto Are1 (1,3 a 9,3): ECO_F1 (valor test: 11,800; 51,8 % frente al 20,0 % del total)."
    assert redaccion.verificar_atribuciones([t], h, pd) == []
    mal = "ECO_F1 tiene Class.Cat 1,3 %."                           # fuera de un nombre de conjunto, la atribución sigue controlándose
    assert redaccion.verificar_atribuciones([mal], h, pd) != []


def test_las_transiciones_repetidas_se_juntan_en_una_oracion():
    t = ("Este conjunto reúne valores intermedios. La misma clase cepa FLO, lado F también se asocia con el conjunto vecino Are1 (1,3 a 9,3). "
         "La misma clase cepa FLO, lado D también se asocia con el conjunto vecino Are1 (1,3 a 9,3). En resumen, se concentra en FLO.")
    assert redaccion._transiciones_juntas(t) == (
        "Este conjunto reúne valores intermedios. Las clases cepa FLO, lado F y cepa FLO, lado D también se asocian con el conjunto vecino "
        "Are1 (1,3 a 9,3). En resumen, se concentra en FLO.")
    distintos = "La clase 7 también se asocia con el conjunto vecino ent1. La clase 12 también se asocia con el conjunto vecino ent3."
    assert redaccion._transiciones_juntas(distintos) == distintos               # vecinos distintos: no se juntan
    assert redaccion._transiciones_juntas("La clase 7 también se asocia con el conjunto vecino ent1.") == "La clase 7 también se asocia con el conjunto vecino ent1."


def test_el_novato_debe_nombrar_el_conjunto_vecino():
    h = _h_cf(["Cepa", "Fecha"])
    g = h["grupos"][1]
    g["pares"][0]["transicion"] = "Are1_1.3a9.3_"
    assert redaccion._vecinos_sin_nombrar("ECO_F2 está en este conjunto; la misma clase también se asocia con el conjunto vecino.", h, g) == [
        "no nombra el conjunto vecino Are1 (1,3 a 9,3) de ECO_F2"]
    assert redaccion._vecinos_sin_nombrar("ECO_F2 también se asocia con el conjunto vecino Are1 (1,3 a 9,3).", h, g) == []


def test_el_primer_parrafo_del_intermedio_trae_las_explicaciones_en_oraciones_propias():
    h = _h_cf(["Cepa", "Fecha"])
    h["perfil"] = "intermedio"
    pd = redaccion.datos_prompt(h)
    t = "Hallazgos para el conjunto Are1 (1,3 a 9,3): Este conjunto reúne los valores más bajos. ECO_F1 se asocia con un valor test de 11,800."
    r = redaccion._con_explicaciones(t, h, pd, h["grupos"][0])
    assert r.startswith("Hallazgos para el conjunto Are1 (1,3 a 9,3): Este conjunto reúne los valores más bajos. El valor test mide cuán improbable")
    assert "El porcentaje es la parte de los valores de la clase" in r and r.endswith("ECO_F1 se asocia con un valor test de 11,800.")
    assert redaccion._con_explicaciones(r, h, pd, h["grupos"][0]) == r
    assert redaccion._con_explicaciones(t, h, pd, h["grupos"][1]) == t
    assert redaccion.verificar([r], h, pd) == []


def test_el_novato_solo_lleva_la_explicacion_del_porcentaje_y_el_experto_ninguna():
    h = _h_cf(["Cepa", "Fecha"])
    t = "Este conjunto reúne los valores más bajos. ECO_F1 llega al 81,3 % frente al 20,0 % del total."
    h["perfil"] = "novato"
    r = redaccion._con_explicaciones(t, h, redaccion.datos_prompt(h), h["grupos"][0])
    assert "El porcentaje es la parte" in r and "valor test" not in r
    h["perfil"] = "experto"
    assert redaccion._con_explicaciones(t, h, redaccion.datos_prompt(h), h["grupos"][0]) == t
    h["perfil"] = "novato"
    propia = "Este conjunto reúne valores bajos. La relación porcentual indica la parte de los valores de la clase que cae en el conjunto."
    assert redaccion._con_explicaciones(propia, h, redaccion.datos_prompt(h), h["grupos"][0]) == propia


def test_el_intermedio_debe_decir_la_intensidad_de_cada_asociacion():
    h = _h_cf(["Cepa", "Fecha"])
    h["perfil"] = "intermedio"
    g = h["grupos"][0]
    gp = redaccion.datos_prompt(h)["grupos"][0]
    sin = ("La asociación más fuerte es con la clase cepa E47, fecha F1, con un valor test de 10,900. "
           "También se asocia con la clase cepa ECO, fecha F1, con un valor test de 11,800. "
           "También se asocia con la clase cepa FLO, fecha F1, de forma fuerte, con un valor test de 13,400.")
    assert redaccion.verificar_intensidad_por_asociacion(sin, h, g, gp) == ["no dice si la asociación de ECO_F1 es fuerte, moderada o débil"]
    con = sin.replace("fecha F1, con un valor test de 11,800", "fecha F1, de forma fuerte, con un valor test de 11,800")
    assert redaccion.verificar_intensidad_por_asociacion(con, h, g, gp) == []
    lista = ("La asociación es fuerte para E47_F1 (valor test: 10,9; 74,3 % frente al 20,0 % del total), para ECO_F1 (valor test: 11,8; "
             "81,3 % frente al 20,0 % del total) y para FLO_F1 (valor test: 13,4; 89,3 % frente al 20,0 % del total).")
    assert redaccion.verificar_intensidad_por_asociacion(lista, h, g, gp) == []       # un «;» dentro de un paréntesis no parte la oración


def test_la_clase_vuelve_a_nombrarse_completa_si_el_modelo_junta_el_desglose_con_y():
    h = _h_cf(["Cepa", "Fecha"])
    t = ("Por último, la cepa ECO y fecha F3 llega al 26,1 %. La cepa E47 y fecha F2 aparece mucho más. "
         "Las clases con cepa E47, ECO y FLO, y fecha F1 no cambian. También se asocia la clase cepa ECO, fecha F2.")
    assert redaccion._clase_con_nombre_completo(t, h) == (
        "Por último, la clase cepa ECO, fecha F3 llega al 26,1 %. La clase cepa E47, fecha F2 aparece mucho más. "
        "Las clases con cepa E47, ECO y FLO, y fecha F1 no cambian. También se asocia la clase cepa ECO, fecha F2.")
    assert redaccion._clase_con_nombre_completo(t, _h_cf()) == t                    # sin nombres de variables no hay desglose que rehacer
    assert redaccion._clase_con_nombre_completo(redaccion._clase_con_nombre_completo(t, h), h) == redaccion._clase_con_nombre_completo(t, h)


def test_la_clase_sin_articulo_ni_clase_se_completa_y_la_lista_de_clases_no_se_toca():
    h = _h_cf(["Cepa", "Fecha"])
    t = ("La asociación que más lo distingue es cepa E47, fecha F2: el 65,1 %. Algo parecido pasa, de forma menos marcada, con cepa ECO, fecha F3, "
         "que llega al 26,1 %. Se asocia con las clases con cepa FLO, fecha F2 y cepa ECO, fecha F2.")
    assert redaccion._clase_con_nombre_completo(t, h) == (
        "La asociación que más lo distingue es la clase cepa E47, fecha F2: el 65,1 %. Algo parecido pasa, de forma menos marcada, con la clase cepa ECO, "
        "fecha F3, que llega al 26,1 %. Se asocia con las clases con cepa FLO, fecha F2 y cepa ECO, fecha F2.")
    ya = "Es la clase cepa E47, fecha F2 la que más destaca."
    assert redaccion._clase_con_nombre_completo(ya, h) == ya


def test_porcentaje_es_lleva_su_articulo():
    t = "Este conjunto reúne valores bajos. Porcentaje es la parte de los valores de la clase. El porcentaje es otra cosa."
    assert redaccion._porcentaje_con_articulo(t) == "Este conjunto reúne valores bajos. El porcentaje es la parte de los valores de la clase. El porcentaje es otra cosa."
    assert redaccion._porcentaje_con_articulo("Porcentaje es la parte.") == "El porcentaje es la parte."


def _h_numerico():
    def par(c, cat, v):
        return {"id": f"{c}-{cat}", "clase": c, "caracteristica": cat, "caracteristica_legible": cat, "valor_test": v, "valor_test_txt": f"{v:.3f}".replace(".", ","),
                "p_texto": "p < 0,01", "class_cat": 10.0, "cat_class": round(40.0 + v, 1), "global": 20.0, "razon": 2.0, "significacion": "altamente significativo",
                "direccion": "sobre-representación", "intensidad": "fuerte", "peso_bajo": False, "transicion": ""}
    sets = {"ent1_4.6a4.9_": [("11", 19.0), ("7", 3.3), ("12", 3.9)], "ent2_4.9a5.4_": [("4", 13.4), ("7", 11.9), ("12", 11.3)]}
    grupos = [{"conjunto": c, "conjunto_legible": c.split("_")[0], "fuerza": 50.0 - i, "fuerza_txt": f"{50 - i},000", "n_pares": len(v), "n_clases": len(v), "tipo": "singularidad",
               "posicion": i + 1, "pares": [par(cl, c, val) for cl, val in v]} for i, (c, v) in enumerate(sets.items())]
    return dict(_h(), n_clases=4, n_pares=6, n_significativas=6, grupos=grupos, descripcion="filas")


def test_una_lista_de_clases_numericas_con_como_se_reconoce_como_clases():
    assert redaccion._clases_numericas_citadas("mientras que otras clases como 9005, 9008 y 9012 se vinculan con otros") == {"9005", "9008", "9012"}
    assert redaccion._clases_numericas_citadas("las clases tales como 7 y 12") == {"7", "12"}
    assert redaccion._clases_numericas_citadas("la clase 9005 y el 12,5 % de 40 asociaciones") == {"9005"}


def test_se_quita_la_oracion_que_no_verifica_y_se_conserva_el_resto():
    h = _h_numerico()
    pd = redaccion.datos_prompt(h)
    buena = "La clase 4 se asocia con ent2 (4,9 a 5,4)."
    mala = "La clase 4 se asocia con ent1 (4,6 a 4,9)."                         # la clase 4 no está en ent1
    cierre = "El archivo sólo contiene las asociaciones que superan el umbral de DaFu."
    texto, quitadas = redaccion._sin_oraciones_que_no_verifican(f"{buena} {mala} {cierre}", h, pd)
    assert texto == f"{buena} {cierre}" and [f for f, _ in quitadas] == [mala] and quitadas[0][1]
    assert redaccion._sin_oraciones_que_no_verifican(f"{buena} {cierre}", h, pd) == (f"{buena} {cierre}", [])
    solo_mala = redaccion._sin_oraciones_que_no_verifican(f"{mala} {mala}", h, pd)
    assert solo_mala == (f"{mala} {mala}", [])                                    # ninguna oración válida: se deja entero


def test_el_nivel_de_intensidad_tambien_se_controla_en_clases_de_nombre_numerico():
    h = _h_numerico()
    g = h["grupos"][0]
    g["pares"][1]["intensidad"] = "débil"                                          # la clase 7 es débil en ent1
    mal = "La clase 11 aparece mucho más de lo esperable. La clase 7 aparece algo más de lo esperable."
    problemas = redaccion.verificar_intensidad(mal, h, g)
    assert len(problemas) == 1 and "moderada" in problemas[0] and "débil" in problemas[0]
    assert redaccion.verificar_intensidad("La clase 11 aparece mucho más de lo esperable. La clase 7 aparece apenas más de lo esperable.", h, g) == []


def test_la_lectura_cruzada_dice_que_clases_se_asocian_con_mas_de_un_conjunto():
    lineas = redaccion._afines(_h_numerico())[0]
    assert any("clase 7 y clase 12 se asocian con los mismos conjuntos: ent1 y ent2" in l and l.endswith("a diferencia de las demás clases, que se asocian con un solo conjunto") for l in lineas)
    assert sum("a diferencia de las demás" in l for l in lineas) == 1                 # sólo en la línea de las clases con varios conjuntos


def test_se_quita_la_oracion_que_dice_conjuntos_distintos_si_las_clases_comparten_los_mismos():
    h = _h_numerico()
    mal = "Como contraste, la clase 7 y la clase 12 se asocian con conjuntos distintos al relacionarse con ent1 y ent2."
    t = "La clase 4 y la clase 11 se asocian con ent2 y ent1. " + mal + " El archivo sólo contiene las asociaciones."
    assert redaccion._sin_conjuntos_distintos_falsos(t, h) == "La clase 4 y la clase 11 se asocian con ent2 y ent1. El archivo sólo contiene las asociaciones."
    cierto = "La clase 4 y la clase 11 se asocian con conjuntos distintos."                # 4 sólo está en ent2 y 11 sólo en ent1
    assert redaccion._sin_conjuntos_distintos_falsos(cierto, h) == cierto
    una = "La clase 7 se asocia con conjuntos distintos."                                  # una sola clase nombrada: no se compara
    assert redaccion._sin_conjuntos_distintos_falsos(una, h) == una
    assert redaccion._sin_conjuntos_distintos_falsos(mal, h) == mal


def test_el_novato_completa_la_intensidad_tambien_con_clases_de_nombre_numerico():
    h = _h_numerico()
    h["perfil"] = "novato"
    h["intensidad_llana"] = {"sobre-representación": {"fuerte": "mucho más de lo esperable"}}
    g, gp = h["grupos"][1], redaccion.datos_prompt(h)["grupos"][1]
    sin = ("En la clase 4 el 81,3 % de los valores está en este conjunto, frente al 25,2 % del total: aparece mucho más de lo esperable. "
           "La clase 7, con el 73,4 % frente al 25,2 % del total. "
           "Algo parecido pasa con la clase 12 con el 71,7 %.")
    assert redaccion.verificar_intensidad_por_asociacion(sin, h, g, gp, llano=True) == ["no dice la intensidad de 7: debe decir «aparece mucho más de lo esperable»"]
    r = redaccion._completar_para_novato(sin, h, g, gp)
    assert "La clase 7, con el 73,4 % frente al 25,2 % del total: aparece mucho más de lo esperable." in r
    assert redaccion.verificar_intensidad_por_asociacion(r, h, g, gp, llano=True) == []


def test_por_un_lado_sin_por_otro_lado_se_quita():
    assert redaccion._sin_por_un_lado("Por un lado, la clase X aparece mucho más. Algo parecido pasa con Y.") == "La clase X aparece mucho más. Algo parecido pasa con Y."
    assert redaccion._sin_por_un_lado("Esto pasa, por un lado, con X.") == "Esto pasa, con X."
    con = "Por un lado, la clase X aparece más. Por otro lado, la clase Y aparece menos."
    assert redaccion._sin_por_un_lado(con) == con
    assert redaccion._sin_por_un_lado("Sin nada que quitar.") == "Sin nada que quitar."


def test_el_novato_debe_decir_la_intensidad_de_cada_asociacion():
    h = _h_cf(["Cepa", "Fecha"])
    h["perfil"] = "novato"
    h["intensidad_llana"] = {"sobre-representación": {"fuerte": "mucho más de lo esperable", "moderada": "algo más de lo esperable"}}
    g, gp = h["grupos"][0], redaccion.datos_prompt(h)["grupos"][0]
    sin = ("La clase cepa FLO, fecha F1 aparece mucho más de lo esperable, con el 89,3 %. "
           "Algo parecido pasa con la clase cepa ECO, fecha F1, que llega al 81,3 %. "
           "También se destaca la clase cepa E47, fecha F1, que alcanza el 74,3 %.")
    r = redaccion.verificar_intensidad_por_asociacion(sin, h, g, gp, llano=True)
    assert r == ["no dice la intensidad de E47_F1: debe decir «aparece mucho más de lo esperable»"]     # «algo parecido» cuenta; E47 no dice nada
    con = sin.replace("que alcanza el 74,3 %", "que alcanza el 74,3 % y aparece mucho más de lo esperable")
    assert redaccion.verificar_intensidad_por_asociacion(con, h, g, gp, llano=True) == []
    general = ("Se asocia con 3 clases que aparecen mucho más de lo esperable. La primera es la clase cepa FLO, fecha F1, con el 89,3 %. "
               "La segunda es la clase cepa ECO, fecha F1, con el 81,3 %. La tercera es la clase cepa E47, fecha F1, con el 74,3 %.")
    assert redaccion.verificar_intensidad_por_asociacion(general, h, g, gp, llano=True) == []          # una oración general las cubre
    lista = "Las clases cepa FLO, fecha F1 y cepa ECO, fecha F1 aparecen mucho más de lo esperable; la clase cepa E47, fecha F1 llega al 74,3 %."
    assert len(redaccion.verificar_intensidad_por_asociacion(lista, h, g, gp, llano=True)) == 0         # una misma oración nombra varias clases


def _novato_con_llana():
    h = _h_cf(["Cepa", "Fecha"])
    h["perfil"] = "novato"
    h["intensidad_llana"] = {"sobre-representación": {"fuerte": "mucho más de lo esperable", "moderada": "algo más de lo esperable"}}
    return h, h["grupos"][0], redaccion.datos_prompt(h)["grupos"][0]


def test_el_novato_completa_por_codigo_la_intensidad_que_el_modelo_dejo_sin_decir():
    h, g, gp = _novato_con_llana()
    t = ("La clase cepa FLO, fecha F1 aparece mucho más de lo esperable: el 89,3 % frente al 29,1 % del total. "
         "La clase cepa ECO, fecha F1, con el 81,3 % frente al 29,1 % del total. "
         "La clase cepa E47, fecha F1, con el 74,3 % frente al 29,1 % del total.")
    r = redaccion._completar_para_novato(t, h, g, gp)
    assert r == ("La clase cepa FLO, fecha F1 aparece mucho más de lo esperable: el 89,3 % frente al 29,1 % del total. "
                 "La clase cepa ECO, fecha F1, con el 81,3 % frente al 29,1 % del total: aparece mucho más de lo esperable. "
                 "La clase cepa E47, fecha F1, con el 74,3 % frente al 29,1 % del total: aparece mucho más de lo esperable.")
    assert redaccion.verificar_intensidad_por_asociacion(r, h, g, gp, llano=True) == []
    assert redaccion._completar_para_novato(r, h, g, gp) == r
    dos = ("La clase cepa FLO, fecha F1 aparece mucho más de lo esperable: el 89,3 % frente al 29,1 % del total. "
           "Asimismo, se asocian la clase cepa ECO, fecha F1 con el 81,3 % frente al 29,1 % del total y la clase cepa E47, fecha F1 con el 74,3 % frente al 29,1 % del total.")
    assert redaccion._completar_para_novato(dos, h, g, gp).endswith("frente al 29,1 % del total: en ambos casos aparece mucho más de lo esperable.")


def test_el_novato_no_se_completa_si_las_intensidades_de_una_oracion_difieren():
    h, g, gp = _novato_con_llana()
    g["pares"][1]["intensidad"] = "moderada"
    gp = redaccion.datos_prompt(h)["grupos"][0]
    t = ("La clase cepa FLO, fecha F1 aparece mucho más de lo esperable: el 89,3 % frente al 29,1 % del total. "
         "Asimismo, se asocian la clase cepa ECO, fecha F1 con el 81,3 % frente al 29,1 % del total y la clase cepa E47, fecha F1 con el 74,3 % frente al 29,1 % del total.")
    assert redaccion._completar_para_novato(t, h, g, gp) == t                        # ECO es moderada y E47 fuerte: no se inventa una sola frase


def test_el_novato_recibe_el_conjunto_vecino_que_el_modelo_no_nombro():
    h, g, gp = _novato_con_llana()
    g["pares"][0]["transicion"] = "Are2_9.3a20.9_"
    t = ("La clase cepa E47, fecha F1 aparece mucho más de lo esperable: el 74,3 % frente al 29,1 % del total. "
         "La clase cepa ECO, fecha F1 aparece mucho más de lo esperable: el 81,3 % frente al 29,1 % del total.")
    r = redaccion._completar_para_novato(t, h, g, gp)
    assert r == ("La clase cepa E47, fecha F1 aparece mucho más de lo esperable: el 74,3 % frente al 29,1 % del total. "
                 "La misma clase también se asocia con el conjunto vecino Are2 (9,3 a 20,9). "
                 "La clase cepa ECO, fecha F1 aparece mucho más de lo esperable: el 81,3 % frente al 29,1 % del total.")
    assert redaccion._vecinos_sin_nombrar(r, h, g) == []


def test_el_intermedio_aclara_la_primera_transicion_una_sola_vez():
    h = _h_cf(["Cepa", "Fecha"])
    h["perfil"] = "intermedio"
    textos = ["Hallazgos para el conjunto Are1 (1,3 a 9,3): Este conjunto reúne valores bajos.",
              "Hallazgos para el conjunto Are5 (53): Este conjunto reúne valores altos. Existe una transición con Are4 (31,4 a 43,4). Otra oración.",
              "Hallazgos para el conjunto Are4 (31,4 a 43,4): Hay transiciones con Are3 (20,9 a 31,4) y Are5 (53)."]
    r = redaccion._con_transicion_aclarada(textos, h)
    assert r[1] == ("Hallazgos para el conjunto Are5 (53): Este conjunto reúne valores altos. Existe una transición con Are4 (31,4 a 43,4). "
                    "Una transición es la misma clase asociada con conjuntos vecinos. Otra oración.")
    assert r[0] == textos[0] and r[2] == textos[2]
    assert redaccion._con_transicion_aclarada(r, h) == r
    ya = [textos[0], "Hay una transición, siendo la misma clase asociada con 2 conjuntos vecinos."]
    assert redaccion._con_transicion_aclarada(ya, h) == ya
    h["perfil"] = "novato"
    assert redaccion._con_transicion_aclarada(textos, h) == textos


def test_le_sigue_se_reescribe_sin_cambiar_lo_que_dice():
    assert redaccion._muletillas("Le sigue la asociación con la clase X, con un valor test de 1,700.") == "También se asocia con la clase X, con un valor test de 1,700."
    assert redaccion._muletillas("Le sigue la clase X, con el 50,0 %.") == "La clase X, con el 50,0 %."


def test_los_perfiles_que_no_son_experto_reciben_el_tipo_de_patron_sin_jerga():
    h = _h_cf(["Cepa", "Fecha"])
    h["tipo_novato"] = {"singularidad": "se asocia con pocas clases (singularidad)", "patrón constante": "se asocia con muchas clases (patrón constante)"}
    h["grupos"][0]["tipo"], h["grupos"][1]["tipo"] = "singularidad", "patrón constante"
    for perfil, esperado in (("novato", "se asocia con pocas clases"), ("intermedio", "se asocia con pocas clases"), ("experto", "singularidad")):
        h["perfil"] = perfil
        assert redaccion.datos_prompt(h)["grupos"][0]["tipo"] == esperado


def test_la_conclusion_no_lleva_oraciones_que_no_nombran_nada():
    h = _h_cf(["Cepa", "Fecha"])
    t = ("En la fecha F1, las 3 cepas se asocian con Are1 (1,3 a 9,3). Las asociaciones varían según la combinación analizada en cada conjunto difuso. "
         "El archivo sólo contiene las asociaciones que superan el umbral de DaFu.")
    assert redaccion._podar_s3(t, h) == t.replace("Las asociaciones varían según la combinación analizada en cada conjunto difuso. ", "")


def test_otro_conjunto_se_puede_nombrar_si_la_misma_clase_tambien_esta_en_el():
    h = _h_cf(["Cepa", "Fecha"])                      # ECO_F2 está en Are2 y en Are3; no figuran como transición
    bien = "Hallazgos para el conjunto Are2 (9,3 a 20,9): la cepa ECO en la fecha F2 también se asocia con Are3 (20,9 a 31,4)."
    assert redaccion._citas_ajenas_al_conjunto(bien, h, 1) == []
    assert redaccion._citas_ajenas_al_conjunto(bien.replace("también se asocia con", "tiene de vecino a"), h, 1) != []
    assert redaccion._citas_ajenas_al_conjunto("Hallazgos para el conjunto Are2 (9,3 a 20,9): FLO_F2 también se asocia con Are3 (20,9 a 31,4).", h, 1) != []
    assert redaccion._citas_ajenas_al_conjunto("Hallazgos para el conjunto Are2 (9,3 a 20,9): ECO_F2 se parece a Are5 (53).", h, 1) != []


def test_vecino_solo_se_dice_de_un_conjunto_contiguo():
    h = _h_cf(["Cepa", "Fecha"])
    t = "Hallazgos para el conjunto Are2 (9,3 a 20,9): la cepa ECO en la fecha F2 también se asocia con el conjunto vecino Are3 (20,9 a 31,4)."
    r = redaccion._sin_vecino_falso(t, h, h["grupos"][1])
    assert "con el conjunto Are3 (20,9 a 31,4)." in r and redaccion._citas_ajenas_al_conjunto(r, h, 1) == []
    h["grupos"][1]["pares"][0]["transicion"] = "Are3_20.9a31.4_"
    assert redaccion._sin_vecino_falso(t, h, h["grupos"][1]) == t


def test_las_demas_combinaciones_posibles_no_es_una_afirmacion_sin_respaldo():
    h = _h_cf()
    assert redaccion.verificar_afirmaciones(["El resto de las combinaciones posibles no figuran en él, sólo las asociaciones que superan el umbral."], h) == []
    assert redaccion.verificar_afirmaciones(["De las asociaciones posibles, 12 son relevantes."], h) != []


def test_las_clases_de_un_conjunto_se_pueden_contar_en_su_propio_parrafo():
    h = _h_cf(["Cepa", "Fecha"])
    g = h["grupos"][0]                                    # Are1: 3 clases de las 9 del análisis
    frase = "Hallazgos para el conjunto Are1 (1,3 a 9,3): Este conjunto reúne los valores asociados con 3 clases."
    assert redaccion.verificar_relaciones([frase], h, g) == []
    assert redaccion.verificar_relaciones([frase.replace("3 clases", "4 clases")], h, g) != []   # una cantidad inventada sigue rechazándose


def test_una_clase_numerica_citada_como_la_n_no_es_una_cifra_inventada():
    from test_revision_noviembre import _h
    h = _h(); pd = redaccion.datos_prompt(h)
    assert redaccion.verificar(["Otras clases como la 9003 se asocian con Oact."], h, pd) == []
    assert redaccion.verificar(["Otras clases como la 9777 se asocian con Oact."], h, pd) == ["9777"]
    assert redaccion.verificar(["La clase 9003 llega al 40,0 %, no al 41,0 %."], h, pd) == ["41,0"]


# ─── Nombres de conjunto con puntos («CO4.9.5a10.5.») y nombres de variable basura ──────────────────────────

def test_un_conjunto_con_puntos_se_lee_como_un_conjunto_difuso():
    assert redaccion._indice_conjunto("CO4.9.5a10.5.") == 4 and redaccion._variable_conjunto("CO4.9.5a10.5.") == "CO"
    assert redaccion._indice_conjunto("tem5.40a40.") == 5 and redaccion._nombre_corto("tem5.40a40.") == "tem5"
    assert redaccion._nombre_corto("Are3_20.9a31.4_") == "Are3" and redaccion._nombre_corto("Hpre") == "Hpre"
    assert redaccion._indice_conjunto("V1.5") is None and redaccion._indice_conjunto("C5") is None     # sin rango completo, no es un conjunto difuso


def test_los_limites_de_un_conjunto_con_puntos_no_son_cifras_inventadas():
    h = _h_cf()
    g = h["grupos"][0]
    g["conjunto"], g["conjunto_legible"] = "CO1.4.2a6.5.", "CO1 (4,2 a 6,5)"
    for p in g["pares"]:
        p["caracteristica"], p["caracteristica_legible"] = g["conjunto"], g["conjunto_legible"]
    pd = redaccion.datos_prompt(h)
    assert redaccion.verificar(["Hallazgos para el conjunto CO1 (4,2 a 6,5): E47_F1 llega al 50,9 %."], h, pd) == []
    assert redaccion.verificar(["Hallazgos para el conjunto CO1 (4,2 a 6,6): E47_F1 llega al 50,9 %."], h, pd) == ["6,6"]


# ─── Nada del prompt ni del código depende de los datos de los ejemplos ──────────────────────────────────────

def _h_otro_tema(nombres_conjuntos=True):
    """Un análisis de otro tema, con otros nombres: regiones y niveles de ingreso, conjuntos «Edad1_18a25_», etc."""
    h = _h_cf(["Región", "Nivel"])
    cl = {"E47_F1": "Norte_Alto", "ECO_F1": "Sur_Alto", "FLO_F1": "Este_Alto", "ECO_F2": "Sur_Medio", "FLO_F2": "Este_Medio",
          "E47_F2": "Norte_Medio", "E47_F3": "Norte_Bajo", "ECO_F3": "Sur_Bajo", "FLO_F3": "Este_Bajo"}
    cj = {"Are1_1.3a9.3_": "Edad1_18a25_", "Are2_9.3a20.9_": "Edad2_25a40_", "Are3_20.9a31.4_": "Edad3_40a60_",
          "Are4_31.4a43.4_": "Edad4_60a75_", "Are5_53a53_": "Edad5_80a80_"}
    cl_leg = {"Edad1_18a25_": "Edad1 (18 a 25)", "Edad2_25a40_": "Edad2 (25 a 40)", "Edad3_40a60_": "Edad3 (40 a 60)",
              "Edad4_60a75_": "Edad4 (60 a 75)", "Edad5_80a80_": "Edad5 (80)"}
    for g in h["grupos"]:
        g["conjunto"] = cj[g["conjunto"]]; g["conjunto_legible"] = cl_leg[g["conjunto"]]
        for p in g["pares"]:
            p["clase"] = cl[p["clase"]]; p["caracteristica"] = g["conjunto"]; p["caracteristica_legible"] = g["conjunto_legible"]
    return h


def test_el_prompt_de_otro_tema_no_trae_nada_de_los_ejemplos():
    h = _h_otro_tema()
    p = redaccion.armar_prompt(h)
    cuerpo = p.split("EJEMPLO DE ESTILO")[0] + p.split("FORMATO DE LA RESPUESTA")[1]       # sin el ejemplo de estilo, que es de otro análisis a propósito
    for ajeno in ("cepa", "E47", "Are1", "F1", "F3", "fecha", "FLO"):
        assert ajeno not in cuerpo, ajeno
    assert "«región Este, nivel Alto»" in p and "«Edad1 (18 a 25)»" in p                    # ejemplos sacados de los datos
    sin_nombres = redaccion.armar_prompt(_h_otro_tema() | {"variables": []})
    assert "cepa" not in sin_nombres and "«las clases que terminan en Alto»" in sin_nombres


def test_un_analisis_de_otro_tema_se_redacta_y_verifica_igual(tmp_path):
    h = _h_otro_tema(); h["texto_s2"] = ""
    paragrafos = "\n\n".join(f"Hallazgos para el conjunto {g['conjunto_legible']}: {g['pares'][0]['clase']} se asocia con este conjunto de forma fuerte." for g in h["grupos"])
    falso = lambda prompt: json.dumps({"S1": "Hay 9 clases y 5 categorías.", "S2": paragrafos, "S3": "En el nivel Alto, las 3 regiones se asocian con Edad1 (18 a 25)."})
    ruta = tmp_path / "hallazgos.json"; ruta.write_text(json.dumps(h, ensure_ascii=False), encoding="utf-8")
    s = json.load(open(redaccion.redactar_sintesis(str(ruta), KB, "simulado", falso), encoding="utf-8"))
    assert s["estado"] == "redactada", s["aviso"]


@pytest.mark.parametrize("clases", [
    ["A+B (x)", "C.D [y]", "ñandú %", "x{2}", "Z|W"],                       # símbolos que son especiales en una expresión regular
    ["Región Norte", "Región Sur", "Zona 5", "Zona 6", "ÁÉÍ"],              # espacios, tildes y números dentro del nombre
    ["a" * 60, "b" * 60, "c" * 60, "d" * 60, "e" * 60],                     # nombres largos
    ["1", "2", "3", "10", "11"],                                            # sólo números
])
def test_nombres_de_clase_cualesquiera_no_rompen_los_controles(tmp_path, clases):
    h = _h_cf()
    pares = [p for g in h["grupos"] for p in g["pares"]]
    for i, p in enumerate(pares):
        p["clase"] = clases[i % len(clases)]; p["id"] = f"GRU-P{i:03d}"
    for g in h["grupos"]:
        g["n_clases"] = len({p["clase"] for p in g["pares"]})
    h["n_clases"] = len(set(clases)); h["texto_s2"] = ""
    h["perfil"] = "experto"; h["visibles"] = dict(valor_test=True, p_valor=True, class_cat=True, razon=True)
    s2 = "\n\n".join(f"Hallazgos para el conjunto {g['conjunto_legible']}: {_clase_txt(g['pares'][0]['clase'])} llega al {redaccion.num(g['pares'][0]['cat_class'], 1)} %."
                     for g in h["grupos"])
    ruta = tmp_path / "hallazgos.json"; ruta.write_text(json.dumps(h, ensure_ascii=False), encoding="utf-8")
    s = json.load(open(redaccion.redactar_sintesis(str(ruta), KB, "simulado", lambda p: json.dumps({"S1": "Hay 9 clases.", "S2": s2, "S3": "Fin."})), encoding="utf-8"))
    assert s["estado"] != "error", s["aviso"]


def _clase_txt(c):
    return redaccion._clase_txt(c)


def test_dos_medidas_con_la_misma_cifra_no_se_toman_por_una_atribucion_falsa():
    h = _h_otro_tema()
    h.update(perfil="experto", visibles=dict(valor_test=True, p_valor=True, class_cat=True, razon=True))
    a, b = h["grupos"][0]["pares"][0], h["grupos"][1]["pares"][0]
    a.update(clase="Norte_Bajo", cat_class=29.0, class_cat=10.0); b.update(clase="Este_Bajo", cat_class=33.3, class_cat=29.0)
    pd = redaccion.datos_prompt(h)
    ok = f"Este_Bajo (valor test {pd['grupos'][1]['pares'][0]['valor_test']}; 33,3 % frente al 20,0 % del total; Class.Cat 29,0 %)."
    assert redaccion.verificar_atribuciones([ok], h, pd) == []                               # 29,0 es el Class.Cat de Este_Bajo
    mal = "Norte_Bajo llega al 33,3 % frente al 20,0 % del total."
    assert redaccion.verificar_atribuciones([mal], h, pd) != []                              # 33,3 sigue siendo de Este_Bajo
