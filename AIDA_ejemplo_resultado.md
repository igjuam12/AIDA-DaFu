# AIDA · Ejemplo de resultado

Resultado real de AIDA (base de conocimiento A10-1.5, Gemini `gemini-3.5-flash-lite`, 10/11/2026) para el caso del área, ejecutado desde la aplicación 03 de DaFu con `Area _Fuzzy.csv`, tabla escalada y agregación por **cepa y fecha** (9 clases, 5 categorías), en los tres perfiles. Los textos no fueron editados. De cada informe se muestran la síntesis completa y las primeras cinco de las 12 interpretaciones; el informe completo lo genera «Descargar resultado» o `aida_guardar()`.

---

## Perfil novato

### Descripción general

Este informe presenta un análisis de descripción de grupos sobre el archivo Area _Fuzzy.csv. El estudio examina 9 clases y 5 categorías.

### Resultados relevantes

Hallazgos para el conjunto Are1 (1,3 a 9,3): Este conjunto reúne los valores más bajos y se asocia con las clases con cepa FLO, fecha F1, cepa ECO, fecha F1 y cepa E47, fecha F1. El porcentaje es la parte de los valores de la clase que cae en el conjunto, comparada con la parte que ese conjunto representa en el total. En este conjunto, la clase cepa FLO, fecha F1 aparece mucho más de lo esperable, con el 89,3 % frente al 29,1 % del total. Algo parecido pasa con la clase cepa ECO, fecha F1, que llega al 81,3 % frente al 29,1 % del total. También se destaca la clase cepa E47, fecha F1, que alcanza el 74,3 % frente al 29,1 % del total: aparece mucho más de lo esperable.

Hallazgos para el conjunto Are5 (53): Este conjunto reúne los valores más altos y se asocia con clases que tienen fecha F3, abarcando las cepas E47 y ECO. La asociación que más lo distingue es la clase cepa E47, fecha F3: el 88,4 % de los valores de esta clase está en este conjunto, cuando en el total ese conjunto sólo reúne el 13,1 %; es decir, aparece mucho más de lo esperable. Algo parecido pasa, de forma menos marcada, con la clase cepa ECO, fecha F3, que llega al 18,4 % frente al 13,1 % del total: aparece algo más de lo esperable; esta clase también se asocia con el conjunto vecino Are4 (31,4 a 43,4).

Hallazgos para el conjunto Are4 (31,4 a 43,4): Este conjunto reúne los valores intermedios y se asocia con las clases con cepa ECO, fecha F3 y cepa FLO, fecha F3. En este conjunto, la clase cepa ECO, fecha F3 aparece mucho más de lo esperable, con el 52,9 % frente al 13,3 % del total. Algo parecido pasa con la clase cepa FLO, fecha F3, que llega al 39,1 % frente al 13,3 % del total. La misma clase cepa ECO, fecha F3 también se asocia con los conjuntos vecinos Are3 (20,9 a 31,4) y Are5 (53).

Hallazgos para el conjunto Are3 (20,9 a 31,4): Este conjunto reúne los valores intermedios y se asocia con las clases con cepa E47, fecha F2, cepa ECO, fecha F2 y cepa ECO, fecha F3. En este conjunto, la clase cepa E47, fecha F2 aparece mucho más de lo esperable, con el 65,1 % frente al 18,7 % del total. Algo parecido pasa con la clase cepa ECO, fecha F2, que llega al 30,5 % frente al 18,7 % del total. También se destaca la clase cepa ECO, fecha F3, que alcanza el 26,1 % frente al 18,7 % del total: aparece algo más de lo esperable. La misma clase cepa ECO, fecha F2 también se asocia con el conjunto vecino Are2 (9,3 a 20,9), y la clase cepa ECO, fecha F3 se asocia con el conjunto vecino Are4 (31,4 a 43,4).

Hallazgos para el conjunto Are2 (9,3 a 20,9): Este conjunto reúne los valores intermedios y se asocia con las clases con cepa FLO, fecha F2 y cepa ECO, fecha F2. En este conjunto, la clase cepa FLO, fecha F2 aparece mucho más de lo esperable, con el 67,7 % frente al 25,7 % del total. Algo parecido pasa con la clase cepa ECO, fecha F2, que llega al 57,7 % frente al 25,7 % del total. La misma clase cepa ECO, fecha F2 también se asocia con el conjunto vecino Are3 (20,9 a 31,4).

### Interpretación conclusiva

En la fecha F1, las 3 cepas E47, ECO y FLO se asocian sobre todo con el conjunto Are1 (1,3 a 9,3). En la fecha F2, la cepa E47 se asocia sobre todo con el conjunto Are3 (20,9 a 31,4), mientras que las cepas ECO y FLO se asocian sobre todo con el conjunto Are2 (9,3 a 20,9), siendo Are3 (20,9 a 31,4) un conjunto de valores más altos que Are2 (9,3 a 20,9). En la fecha F3, la cepa E47 se asocia sobre todo con el conjunto Are5 (53), mientras que las cepas ECO y FLO se asocian sobre todo con el conjunto Are4 (31,4 a 43,4), siendo Are5 (53) un conjunto de valores más altos que Are4 (31,4 a 43,4). En conjunto, en las clases con fecha F2 y F3, las de cepa E47 tienen siempre su asociación principal en un conjunto de valores más altos que las de cepa ECO y FLO. El archivo sólo contiene las asociaciones que superan el umbral de DaFu y las demás combinaciones no figuran en él.

### Limitaciones metodológicas

AIDA sólo informa las asociaciones claras en las que un valor aparece más de lo esperado; las demás no figuran en el archivo de DaFu.  
Los datos se reescalaron antes del análisis: los porcentajes son proporciones de la tabla reescalada y no de los datos originales.  
Los resultados dependen de cómo se definieron los conjuntos difusos (los grupos de valores): con otra cantidad de conjuntos o con otros límites podrían aparecer asociaciones distintas.  
Que una asociación sea clara no significa que el fenómeno sea más intenso.

### Interpretaciones (primeras 5 de 12)

- **GRU-P001** En E47_F1 (cepa E47, fecha F1), el 74,3 % de los valores corresponde a Are1 (1,3 a 9,3), mientras que en el total esa proporción es del 29,1 %. Esa concentración distingue a E47_F1 de los demás y es muy poco probable que se deba al azar. No indica que el fenómeno sea más intenso en E47_F1.
- **GRU-P002** En E47_F2 (cepa E47, fecha F2), el 65,1 % de los valores corresponde a Are3 (20,9 a 31,4), mientras que en el total esa proporción es del 18,7 %. Esa concentración distingue a E47_F2 de los demás y es muy poco probable que se deba al azar. No indica que el fenómeno sea más intenso en E47_F2.
- **GRU-P003** En E47_F3 (cepa E47, fecha F3), el 88,4 % de los valores corresponde a Are5 (53), mientras que en el total esa proporción es del 13,1 %. Esa concentración distingue a E47_F3 de los demás y es muy poco probable que se deba al azar. No indica que el fenómeno sea más intenso en E47_F3.
- **GRU-P004** En ECO_F1 (cepa ECO, fecha F1), el 81,3 % de los valores corresponde a Are1 (1,3 a 9,3), mientras que en el total esa proporción es del 29,1 %. Esa concentración distingue a ECO_F1 de los demás y es muy poco probable que se deba al azar. No indica que el fenómeno sea más intenso en ECO_F1.
- **GRU-P005** En ECO_F2 (cepa ECO, fecha F2), el 57,7 % de los valores corresponde a Are2 (9,3 a 20,9), mientras que en el total esa proporción es del 25,7 %. Esa concentración distingue a ECO_F2 de los demás y es muy poco probable que se deba al azar. No indica que el fenómeno sea más intenso en ECO_F2. ECO_F2 se asocia además con Are3 (20,9 a 31,4), al lado de Are2 (9,3 a 20,9) en la escala de valores.

---

## Perfil intermedio

### Descripción general

Este informe presenta una descripción de grupos basada en el análisis de datos estadísticos del archivo Area _Fuzzy.csv. El estudio comprende 9 clases y 5 categorías.

### Resultados relevantes

Hallazgos para el conjunto Are1 (1,3 a 9,3): Este conjunto reúne los valores más bajos y agrupa clases con cepa E47, ECO y FLO, todas con fecha F1. El valor test mide cuán improbable es que la asociación sea casual; no mide cuán intenso es el fenómeno. La parte de los valores de la clase que cae en el conjunto, comparada con la parte que ese conjunto representa en el total, se denomina porcentaje. La asociación fuerte con la clase cepa FLO, fecha F1 presenta un valor test de 13,353 y un 89,3 % frente al 29,1 % del total. La clase cepa ECO, fecha F1 muestra una sobre-representación fuerte con un valor test de 11,814 y un 81,3 % frente al 29,1 % del total. La clase cepa E47, fecha F1 se asocia fuertemente con un valor test de 10,867 y un 74,3 % frente al 29,1 % del total.

Hallazgos para el conjunto Are5 (53): Este conjunto reúne los valores más altos y agrupa clases con cepa E47 y ECO, todas con fecha F3. La clase cepa E47, fecha F3 presenta una sobre-representación fuerte con un valor test de 20,223 y un 88,4 % frente al 13,1 % del total. La clase cepa ECO, fecha F3 muestra una sobre-representación moderada con un valor test de 2,009 y un 18,4 % frente al 13,1 % del total. Existe una transición con Are4 (31,4 a 43,4). Una transición es la misma clase asociada con conjuntos vecinos.

Hallazgos para el conjunto Are4 (31,4 a 43,4): Este conjunto reúne valores intermedios y agrupa clases con cepa ECO y FLO, todas con fecha F3. La clase cepa ECO, fecha F3 se asocia fuertemente con un valor test de 11,883 y un 52,9 % frente al 13,3 % del total. La clase cepa FLO, fecha F3 presenta una sobre-representación fuerte con un valor test de 7,945 y un 39,1 % frente al 13,3 % del total. Existen transiciones con Are3 (20,9 a 31,4) y Are5 (53).

Hallazgos para el conjunto Are3 (20,9 a 31,4): Este conjunto reúne valores intermedios y agrupa clases con cepa ECO y E47, y fecha F2 y F3. La clase cepa E47, fecha F2 muestra una sobre-representación fuerte con un valor test de 13,403 y un 65,1 % frente al 18,7 % del total. La clase cepa ECO, fecha F2 presenta una sobre-representación fuerte con un valor test de 3,520 y un 30,5 % frente al 18,7 % del total. La clase cepa ECO, fecha F3 se asocia moderadamente con un valor test de 2,351 y un 26,1 % frente al 18,7 % del total. Existen transiciones con Are2 (9,3 a 20,9) y Are4 (31,4 a 43,4).

Hallazgos para el conjunto Are2 (9,3 a 20,9): Este conjunto reúne valores intermedios y agrupa clases con cepa ECO y FLO, todas con fecha F2. La clase cepa FLO, fecha F2 muestra una sobre-representación fuerte con un valor test de 10,448 y un 67,7 % frente al 25,7 % del total. La clase cepa ECO, fecha F2 se asocia fuertemente con un valor test de 8,042 y un 57,7 % frente al 25,7 % del total. Existe una transición con Are3 (20,9 a 31,4).

### Interpretación conclusiva

En el nivel de la fecha F1, las 3 cepas E47, ECO y FLO se asocian sobre todo con el conjunto Are1 (1,3 a 9,3). En la fecha F2, la cepa E47 se asocia sobre todo con el conjunto Are3 (20,9 a 31,4), mientras que las cepas ECO y FLO lo hacen sobre todo con el conjunto Are2 (9,3 a 20,9); el conjunto Are3 (20,9 a 31,4) es un conjunto de valores más altos que el conjunto Are2 (9,3 a 20,9). En la fecha F3, la cepa E47 se asocia sobre todo con el conjunto Are5 (53), y las cepas ECO y FLO se asocian sobre todo con el conjunto Are4 (31,4 a 43,4); el conjunto Are5 (53) es un conjunto de valores más altos que el conjunto Are4 (31,4 a 43,4). En conjunto, en las clases con fecha F2 y F3, las de cepa E47 tienen siempre su asociación principal en un conjunto de valores más altos que las de cepa ECO y FLO. El archivo sólo contiene las asociaciones que superan el umbral de DaFu y las demás combinaciones no figuran en él.

### Limitaciones metodológicas

La exportación de DaFu contiene sólo asociaciones positivas con valor test mayor o igual que 1,65; las asociaciones negativas y las no significativas no se informan.  
La tabla de contingencia fue escalada antes del análisis, por lo que los porcentajes son frecuencias relativas de la tabla escalada y no de los datos originales.  
Los resultados dependen de la elección de los conjuntos difusos: otra cantidad de conjuntos u otros límites pueden producir asociaciones distintas.  
El valor test mide la significación estadística de cada asociación y no la intensidad del fenómeno.

### Interpretaciones (primeras 5 de 12)

- **GRU-P001** (R-MI-1) Are1 (1,3 a 9,3) caracteriza a E47_F1 (cepa E47, fecha F1): valor test = 10,867 (altamente significativo). Su contribución a E47_F1 es del 74,3 %, frente al 29,1 % del total. El valor test indica significación de la asociación, no magnitud del fenómeno.
- **GRU-P002** (R-MI-1) Are3 (20,9 a 31,4) caracteriza a E47_F2 (cepa E47, fecha F2): valor test = 13,403 (altamente significativo). Su contribución a E47_F2 es del 65,1 %, frente al 18,7 % del total. El valor test indica significación de la asociación, no magnitud del fenómeno.
- **GRU-P003** (R-MI-1) Are5 (53) caracteriza a E47_F3 (cepa E47, fecha F3): valor test = 20,223 (altamente significativo). Su contribución a E47_F3 es del 88,4 %, frente al 13,1 % del total. El valor test indica significación de la asociación, no magnitud del fenómeno.
- **GRU-P004** (R-MI-1) Are1 (1,3 a 9,3) caracteriza a ECO_F1 (cepa ECO, fecha F1): valor test = 11,814 (altamente significativo). Su contribución a ECO_F1 es del 81,3 %, frente al 29,1 % del total. El valor test indica significación de la asociación, no magnitud del fenómeno.
- **GRU-P005** (R-MI-1) Are2 (9,3 a 20,9) caracteriza a ECO_F2 (cepa ECO, fecha F2): valor test = 8,042 (altamente significativo). Su contribución a ECO_F2 es del 57,7 %, frente al 25,7 % del total. El valor test indica significación de la asociación, no magnitud del fenómeno. En ECO_F2, Are2 (9,3 a 20,9) es contigua a Are3 (20,9 a 31,4); en conjunto describen una transición entre categorías contiguas.

---

## Perfil experto

### Descripción general

Análisis de descripción de grupos sobre el archivo Area _Fuzzy.csv, que comprende 9 clases y 5 categorías.

### Resultados relevantes

Hallazgos para el conjunto Are1 (1,3 a 9,3): Este conjunto reúne los valores más bajos, con los cuales se asocian las clases de fecha F1 correspondientes a las cepas FLO, ECO y E47. Se observa una sobre-representación fuerte de la cepa FLO, fecha F1 (valor test 13,353; p < 0,01; 89,3 % frente al 29,1 % del total; Class.Cat 28,7 %; razón de proporciones 3,07), otra fuerte de la cepa ECO, fecha F1 (valor test 11,814; p < 0,01; 81,3 % frente al 29,1 % del total; Class.Cat 27,4 %; razón de proporciones 2,79) y otra fuerte de la cepa E47, fecha F1 (valor test 10,867; p < 0,01; 74,3 % frente al 29,1 % del total; Class.Cat 28,2 %; razón de proporciones 2,55).

Hallazgos para el conjunto Are5 (53): Este conjunto reúne los valores más altos, con los cuales se asocian las clases con fecha F3 correspondientes a las cepas E47 y ECO. Se observa una sobre-representación fuerte de la cepa E47, fecha F3 (valor test 20,223; p < 0,01; 88,4 % frente al 13,1 % del total; Class.Cat 69,0 %; razón de proporciones 6,75) y otra moderada de la cepa ECO, fecha F3 (valor test 2,009; p = 0,045; 18,4 % frente al 13,1 % del total; Class.Cat 16,6 %; razón de proporciones 1,40). Presenta transición con Are4 (31,4 a 43,4).

Hallazgos para el conjunto Are4 (31,4 a 43,4): Este conjunto reúne valores intermedios, con los cuales se asocian las clases con fecha F3 correspondientes a las cepas ECO y FLO. Se observa una sobre-representación fuerte de la cepa ECO, fecha F3 (valor test 11,883; p < 0,01; 52,9 % frente al 13,3 % del total; Class.Cat 47,1 %; razón de proporciones 3,98) y otra fuerte de la cepa FLO, fecha F3 (valor test 7,945; p < 0,01; 39,1 % frente al 13,3 % del total; Class.Cat 34,2 %; razón de proporciones 2,94). Presenta transición con Are3 (20,9 a 31,4) y Are5 (53).

Hallazgos para el conjunto Are3 (20,9 a 31,4): Este conjunto reúne valores intermedios, con los cuales se asocian clases con fecha F2 y F3 correspondientes a las cepas E47 y ECO. Se observa una sobre-representación fuerte de la cepa E47, fecha F2 (valor test 13,403; p < 0,01; 65,1 % frente al 18,7 % del total; Class.Cat 45,1 %; razón de proporciones 3,48), otra fuerte de la cepa ECO, fecha F2 (valor test 3,520; p < 0,01; 30,5 % frente al 18,7 % del total; Class.Cat 18,9 %; razón de proporciones 1,63) y otra moderada de la cepa ECO, fecha F3 (valor test 2,351; p = 0,019; 26,1 % frente al 18,7 % del total; Class.Cat 16,5 %; razón de proporciones 1,40). Presenta transición con Are2 (9,3 a 20,9) y Are4 (31,4 a 43,4).

Hallazgos para el conjunto Are2 (9,3 a 20,9): Este conjunto reúne valores intermedios, con los cuales se asocian las clases con fecha F2 correspondientes a las cepas FLO y ECO. Se observa una sobre-representación fuerte de la cepa FLO, fecha F2 (valor test 10,448; p < 0,01; 67,7 % frente al 25,7 % del total; Class.Cat 30,2 %; razón de proporciones 2,63) y otra fuerte de la cepa ECO, fecha F2 (valor test 8,042; p < 0,01; 57,7 % frente al 25,7 % del total; Class.Cat 26,0 %; razón de proporciones 2,25). Presenta transición con Are3 (20,9 a 31,4).

### Interpretación conclusiva

En la fecha F1, las 3 cepas (E47, ECO y FLO) se asocian sobre todo con Are1 (1,3 a 9,3). En la fecha F2, la cepa E47 se asocia sobre todo con Are3 (20,9 a 31,4), mientras que las cepas ECO y FLO lo hacen sobre todo con Are2 (9,3 a 20,9), siendo Are3 (20,9 a 31,4) un conjunto de valores más altos que Are2 (9,3 a 20,9). En la fecha F3, la cepa E47 se asocia sobre todo con Are5 (53), y las cepas ECO y FLO se asocian sobre todo con Are4 (31,4 a 43,4), siendo Are5 (53) un conjunto de valores más altos que Are4 (31,4 a 43,4). En conjunto, en las clases con fecha F2 y F3, las de cepa E47 tienen siempre su asociación principal en un conjunto de valores más altos que las de cepa ECO y FLO. El archivo sólo contiene las asociaciones que superan el umbral de DaFu y las demás combinaciones no figuran en él.

### Limitaciones metodológicas

La exportación de DaFu contiene sólo asociaciones positivas con valor test mayor o igual que 1,65; las asociaciones negativas y las no significativas no se informan.  
La tabla de contingencia fue escalada antes del análisis, por lo que los porcentajes son frecuencias relativas de la tabla escalada y no de los datos originales.  
Los resultados dependen de la elección de los conjuntos difusos: otra cantidad de conjuntos u otros límites pueden producir asociaciones distintas.  
El valor test mide la significación estadística de cada asociación y no la intensidad del fenómeno.

### Interpretaciones (primeras 5 de 12)

- **GRU-P001** (R-MI-1) Are1 (1,3 a 9,3) en E47_F1 (cepa E47, fecha F1): V = 10,867; p < 0,01 (R-MI-1, sobre-representación). Cat.Class = 74,3 %; Global = 29,1 %; razón de proporciones = 2,55; Class.Cat = 28,2 %. El valor test expresa la improbabilidad de la asociación bajo independencia, no la intensidad del fenómeno.
- **GRU-P002** (R-MI-1) Are3 (20,9 a 31,4) en E47_F2 (cepa E47, fecha F2): V = 13,403; p < 0,01 (R-MI-1, sobre-representación). Cat.Class = 65,1 %; Global = 18,7 %; razón de proporciones = 3,48; Class.Cat = 45,1 %. El valor test expresa la improbabilidad de la asociación bajo independencia, no la intensidad del fenómeno.
- **GRU-P003** (R-MI-1) Are5 (53) en E47_F3 (cepa E47, fecha F3): V = 20,223; p < 0,01 (R-MI-1, sobre-representación). Cat.Class = 88,4 %; Global = 13,1 %; razón de proporciones = 6,75; Class.Cat = 69,0 %. El valor test expresa la improbabilidad de la asociación bajo independencia, no la intensidad del fenómeno.
- **GRU-P004** (R-MI-1) Are1 (1,3 a 9,3) en ECO_F1 (cepa ECO, fecha F1): V = 11,814; p < 0,01 (R-MI-1, sobre-representación). Cat.Class = 81,3 %; Global = 29,1 %; razón de proporciones = 2,79; Class.Cat = 27,4 %. El valor test expresa la improbabilidad de la asociación bajo independencia, no la intensidad del fenómeno.
- **GRU-P005** (R-MI-1) Are2 (9,3 a 20,9) en ECO_F2 (cepa ECO, fecha F2): V = 8,042; p < 0,01 (R-MI-1, sobre-representación). Cat.Class = 57,7 %; Global = 25,7 %; razón de proporciones = 2,25; Class.Cat = 26,0 %. El valor test expresa la improbabilidad de la asociación bajo independencia, no la intensidad del fenómeno. En ECO_F2, Are2 (9,3 a 20,9) es contigua a Are3 (20,9 a 31,4); en conjunto describen una transición entre categorías contiguas.
