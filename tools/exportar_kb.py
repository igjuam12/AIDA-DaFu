"""Exporta la red de marcos de AIDA desde Neo4j a un JSON (marcos e instancias).

Uso:  python exportar_kb.py bolt://localhost:7687 neo4j marcos_neo4j.json
La clave de Neo4j se toma de la variable de entorno NEO4J_CLAVE o se pide por consola (no se pasa como
argumento, para que no quede en el historial de comandos).
Requiere:  pip install neo4j
El JSON generado contiene, por cada FrameClass, su padre, sus slots propios con sus facetas y
demonios, y sus slots efectivos (con herencia). Las instancias se exportan con sus valores.
Sirve para revisar el modelo: no tiene el formato de kb/base_conocimiento.json, que es el archivo que carga el
asistente y se mantiene junto con kb/AIDA_frames_A10.cypher (tests/pytest controla que coincidan).
"""
import getpass, json, os, sys

Q_CLASES = "MATCH (c:FrameClass) OPTIONAL MATCH (c)-[:IS_A]->(p:FrameClass) RETURN c.name AS nombre, p.name AS padre"
Q_SLOTS = ("MATCH (c:FrameClass)-[h:HAS_SLOT]->(s:Slot) "
           "RETURN c.name AS marco, s.name AS slot, properties(h) AS facetas")
Q_INST = ("MATCH (i:FrameInst)-[:INSTANCE_OF]->(c:FrameClass) "
          "OPTIONAL MATCH (i)-[v:HAS_VALUE]->(s:Slot) "
          "RETURN i.id AS id, c.name AS marco, s.name AS slot, v.value AS valor")
Q_REFS = ("MATCH (i:FrameInst)-[r]->(j:FrameInst) "
          "RETURN i.id AS id, type(r) AS slot, j.id AS destino")


def construir(clases, slots, instancias, refs=()):
    """clases: [(nombre, padre)], slots: [(marco, slot, facetas)], instancias: [(id, marco, slot, valor)]."""
    padre = {n: p for n, p in clases}
    propios = {n: {} for n in padre}
    for marco, slot, fac in slots:
        propios[marco][slot] = {k: v for k, v in fac.items() if v is not None}

    def efectivos(n):
        cadena, x = [], n
        while x is not None:
            cadena.append(x); x = padre[x]
        res = {}
        for m in reversed(cadena):            # del ancestro al marco: el hijo redefine
            for s, f in propios[m].items():
                res[s] = dict(f, definido_en=m)
        return res

    marcos = {n: {"padre": padre[n], "slots_propios": propios[n], "slots": efectivos(n)} for n in padre}
    inst = {}
    for id_, marco, slot, valor in instancias:
        d = inst.setdefault(id_, {"marco": marco, "valores": {}, "referencias": {}})
        if slot is not None:
            d["valores"][slot] = valor
    for id_, slot, destino in refs:
        inst[id_]["referencias"].setdefault(slot, []).append(destino)
    return {"marcos": marcos, "instancias": inst}


def exportar(uri, usuario, clave, salida):
    from neo4j import GraphDatabase
    with GraphDatabase.driver(uri, auth=(usuario, clave)) as drv, drv.session() as s:
        clases = [(r["nombre"], r["padre"]) for r in s.run(Q_CLASES)]
        slots = [(r["marco"], r["slot"], r["facetas"]) for r in s.run(Q_SLOTS)]
        inst = [(r["id"], r["marco"], r["slot"], r["valor"]) for r in s.run(Q_INST)]
        refs = [(r["id"], r["slot"], r["destino"]) for r in s.run(Q_REFS)]
    kb = construir(clases, slots, inst, refs)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    print(f"{len(kb['marcos'])} marcos, {len(kb['instancias'])} instancias -> {salida}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    uri, usuario, salida = sys.argv[1:4]
    exportar(uri, usuario, os.environ.get("NEO4J_CLAVE") or getpass.getpass("Clave de Neo4j: "), salida)
