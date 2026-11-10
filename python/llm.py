"""AIDA · Única llamada al modelo de lenguaje (RF-MS-7).

Si cambia el modelo o el proveedor, se modifica sólo este archivo. Dos proveedores:
  · gemini  API de Google (rápido; los datos de la síntesis viajan a Google).
  · ollama  modelo local (RNF-5; más lento en equipos sin placa de video).

La configuración sale de variables de entorno o del archivo «.env» de la carpeta aida (no se sube a git):
  AIDA_PROVEEDOR   «gemini» u «ollama» (por defecto, «gemini» si hay GEMINI_API_KEY; si no, «ollama»)
  GEMINI_API_KEY   clave de la API de Gemini
  AIDA_MODELO      modelo del proveedor elegido (opcional)
  AIDA_MODELO_RESPALDO  otro modelo de Gemini para cuando el principal sigue saturado (error 5xx) tras los reintentos (opcional)
  AIDA_ENV         ruta de otro archivo .env, por ejemplo fuera de una carpeta sincronizada con la nube (opcional)
La clave nunca se escribe en mensajes de error ni en la URL.
"""
import http.client
import json
import os
import time
import urllib.error
import urllib.request

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
MODELO_GEMINI = "gemini-3.5-flash-lite"      # sólo de respaldo: el modelo se define con AIDA_MODELO en .env
MODELO_OLLAMA = "llama3.2:3b"
TIEMPO_LIMITE = 120      # segundos de espera por la respuesta de Gemini
TIEMPO_OLLAMA = 600      # segundos sin recibir nada del modelo local
ESPERA_MAXIMA = 30       # segundos que se acepta esperar cuando Gemini pide reintentar más tarde
CONTEXTO = 8192          # tokens de contexto para Ollama
MAX_RESPUESTA = 4096     # tokens de salida con Ollama (el contexto de 8.192 también aloja el prompt)
MAX_RESPUESTA_GEMINI = 8192   # la síntesis se pide en una sola respuesta: con muchas clases ocupa más que 2.048 tokens
URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"


def cargar_env(ruta=None):
    """Lee KEY=valor de .env sin pisar variables con valor en el entorno. Acepta «export», comillas y comentarios al final."""
    ruta = ruta or os.environ.get("AIDA_ENV") or os.path.join(RAIZ, ".env")
    if not os.path.isfile(ruta):
        return
    with open(ruta, encoding="utf-8-sig") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            k, v = linea.split("=", 1)
            k, v = k.strip(), v.strip()
            if k.startswith("export "):
                k = k[len("export "):].strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            else:
                v = v.split(" #", 1)[0].strip()
            if not os.environ.get(k):
                os.environ[k] = v


def proveedor():
    cargar_env()
    p = os.environ.get("AIDA_PROVEEDOR", "").strip().lower()
    if p in ("gemini", "ollama"):
        return p
    return "gemini" if os.environ.get("GEMINI_API_KEY") else "ollama"


def modelo_por_defecto():
    cargar_env()
    return os.environ.get("AIDA_MODELO", "").strip() or (MODELO_GEMINI if proveedor() == "gemini" else MODELO_OLLAMA)


# ── Gemini ───────────────────────────────────────────────────────────────────
_ERRORES_HTTP = {
    400: "la solicitud a Gemini no es válida (revise el nombre del modelo en AIDA_MODELO o la clave)",
    401: "Gemini rechazó la clave de API (revise GEMINI_API_KEY en el archivo .env)",
    403: "Gemini rechazó la clave de API o no tiene permiso para el modelo (revise GEMINI_API_KEY)",
    404: "el modelo de Gemini no existe (revise AIDA_MODELO)",
    429: "se superó la cuota de Gemini; espere un momento y vuelva a intentar",
}


def _gemini(prompt, modelo):
    """Llama a Gemini; si el servicio está saturado (500/502/503/504) o hay límite de ritmo (429), reintenta con espera."""
    esperas = [3, 8, 20, 40]       # un 503 pasajero no debería dejar la síntesis sin redactar
    while True:
        try:
            return _gemini_una_vez(prompt, modelo)
        except _Transitorio as e:
            # Si Google pide esperar mucho (por ejemplo, se agotó la cuota del día), no tiene sentido reintentar.
            if not esperas or e.espera > ESPERA_MAXIMA:
                raise (_Saturado if e.saturado else ValueError)(str(e)) from None
            time.sleep(max(esperas.pop(0), e.espera))


class _Saturado(ValueError):
    """El servicio de Gemini sigue caído o saturado después de los reintentos (error 5xx)."""


class _Transitorio(Exception):
    def __init__(self, mensaje, espera=0, saturado=False):
        super().__init__(mensaje)
        self.espera = espera
        self.saturado = saturado


def _detalle(e, clave):
    """Mensaje que Google agrega al error HTTP (por ejemplo «The model is overloaded»), acotado y sin la clave."""
    try:
        m = str(json.loads(e.read().decode("utf-8", "replace")).get("error", {}).get("message", ""))
    except Exception:
        return ""
    return " ".join(m.replace(clave, "***").split())[:160]


def _segundos_de_espera(cabeceras):
    """Valor de Retry-After en segundos; 0 si no vino o tiene formato de fecha."""
    try:
        return max(0, int((cabeceras or {}).get("Retry-After", 0)))
    except (TypeError, ValueError):
        return 0


def _gemini_una_vez(prompt, modelo):
    clave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not clave:
        raise ValueError("falta GEMINI_API_KEY: cree el archivo .env a partir de .env.example y complete GEMINI_API_KEY (ver README.md)")
    cuerpo = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "seed": 42, "maxOutputTokens": MAX_RESPUESTA_GEMINI,
                             "responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        URL_GEMINI.format(modelo=modelo), data=json.dumps(cuerpo).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": clave})
    try:
        with urllib.request.urlopen(req, timeout=TIEMPO_LIMITE) as r:
            datos = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (500, 502, 503, 504):
            d = _detalle(e, clave)
            raise _Transitorio(f"el servicio de Gemini no está disponible (error {e.code}{': ' + d if d else ''}); reintente más tarde",
                               saturado=True) from None
        if e.code == 429:
            raise _Transitorio(_ERRORES_HTTP[429], _segundos_de_espera(e.headers)) from None
        raise ValueError(_ERRORES_HTTP.get(e.code, f"Gemini respondió con el error {e.code}")) from None
    except TimeoutError:
        raise TimeoutError("el modelo tardó demasiado en responder") from None
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError):
            raise TimeoutError("el modelo tardó demasiado en responder") from None
        raise ConnectionError("no se pudo conectar con Gemini; revise la conexión a internet") from None
    except (OSError, http.client.HTTPException):
        raise ConnectionError("se cortó la conexión con Gemini; revise la conexión a internet") from None
    except ValueError:                 # el cuerpo no es JSON (json.JSONDecodeError y UnicodeDecodeError son ValueError)
        raise ValueError("Gemini devolvió una respuesta que no se puede leer") from None
    cand = (datos.get("candidates") or [{}])[0]
    if cand.get("finishReason") == "MAX_TOKENS":
        raise ValueError("la respuesta del modelo se cortó por el límite de tokens")
    if cand.get("finishReason") not in (None, "STOP"):   # SAFETY, RECITATION, OTHER: un texto parcial no sirve
        raise ValueError(f"Gemini cortó la respuesta ({cand['finishReason']})")
    partes = (cand.get("content") or {}).get("parts") or []
    texto = "".join(p.get("text", "") for p in partes)
    if not texto:
        motivo = cand.get("finishReason") or (datos.get("promptFeedback") or {}).get("blockReason") or "sin texto"
        raise ValueError(f"Gemini no devolvió texto ({motivo})")
    return texto


# ── Ollama ───────────────────────────────────────────────────────────────────
OPCIONES = {"temperature": 0, "seed": 42, "top_k": 1, "num_ctx": CONTEXTO, "num_predict": MAX_RESPUESTA,
            "repeat_penalty": 1.15}
# Si el modelo cae en un bucle de repeticiones (pasa con modelos chicos), se reintenta una vez con más variación.
OPCIONES_REINTENTO = {"temperature": 0.3, "seed": 42, "top_k": 40, "top_p": 0.9, "num_ctx": CONTEXTO,
                      "num_predict": MAX_RESPUESTA, "repeat_penalty": 1.3}


class _Cortada(ValueError):
    pass


def _una_vez(cliente, prompt, modelo, opciones):
    texto, motivo = "", None
    # La respuesta se recibe por partes: el tiempo límite corre entre una parte y la siguiente.
    for parte in cliente.chat(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        format="json",
        options=opciones,
        keep_alive="10m",
        stream=True,
    ):
        texto += parte["message"]["content"]
        motivo = parte.get("done_reason") or motivo
    if motivo == "length":
        raise _Cortada("la respuesta del modelo se cortó por el límite de tokens")
    return texto


def _ollama(prompt, modelo):
    import ollama  # se importa aquí para que el resto del módulo funcione sin la biblioteca

    cliente = ollama.Client(timeout=TIEMPO_OLLAMA)
    try:
        return _una_vez(cliente, prompt, modelo, OPCIONES)
    except ollama.ResponseError as e:
        if "repeat" not in str(e).lower():
            raise
    except _Cortada:                   # un bucle de repeticiones también puede terminar agotando los tokens
        pass
    return _una_vez(cliente, prompt, modelo, OPCIONES_REINTENTO)


def generar_texto(prompt: str, modelo: str = None) -> str:
    """Envía el prompt al modelo del proveedor configurado y devuelve el texto generado (se pide JSON)."""
    prov = proveedor()
    pedido = os.environ.get("AIDA_PROVEEDOR", "").strip().lower()
    if pedido and pedido not in ("gemini", "ollama"):
        raise ValueError(f"AIDA_PROVEEDOR debe ser «gemini» u «ollama», no «{pedido}»")
    if not modelo or (prov == "gemini" and not modelo.startswith("gemini")):   # un nombre de Ollama no sirve en Gemini
        modelo = modelo_por_defecto()
    if prov != "gemini":
        return _ollama(prompt, modelo)
    try:
        return _gemini(prompt, modelo)
    except _Saturado:
        respaldo = os.environ.get("AIDA_MODELO_RESPALDO", "").strip()     # otro modelo de Gemini, si el principal sigue saturado
        if not respaldo or respaldo == modelo:
            raise
        return _gemini(prompt, respaldo)
