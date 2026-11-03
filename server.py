"""API web (FastAPI) que usa rag.py y sirve la interfaz de chat.

Uso (desde la carpeta del proyecto):
    python server.py
y abre http://127.0.0.1:8000 en el navegador.
"""
import hashlib
import json
import logging
import threading
import time
import traceback
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import rag

BASE = Path(__file__).parent
LIMITE_PETICIONES = 10   # preguntas permitidas por IP...
VENTANA_SEGUNDOS = 60    # ...en esta ventana de tiempo
MAX_IPS = 5000           # poda del límite de peticiones para que la memoria no crezca sin fin

ARCHIVO_LOG = BASE / "preguntas.log"   # además de la consola, se guarda aquí

# Registro propio: consola + archivo, con fecha y hora
registro = logging.getLogger("preguntas")
registro.setLevel(logging.INFO)
registro.propagate = False
_formato = logging.Formatter("%(asctime)s | %(message)s", "%Y-%m-%d %H:%M:%S")
for _handler in (logging.StreamHandler(), logging.FileHandler(ARCHIVO_LOG, encoding="utf-8")):
    _handler.setFormatter(_formato)
    registro.addHandler(_handler)

estado = {}
candado = threading.Lock()   # una respuesta a la vez: Ollama local no da para más
visitas = defaultdict(deque)


@asynccontextmanager
async def lifespan(app):
    # Falla pronto y con un mensaje claro si falta el modelo de embeddings
    rag.embeber(["prueba"])
    coleccion = rag.abrir_coleccion()
    nuevos, total = rag.indexar(coleccion)
    print(f"{total} fragmentos en '{rag.DOCS_DIR}/' ({nuevos} nuevos indexados).")
    estado["coleccion"] = coleccion
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


class Pregunta(BaseModel):
    pregunta: str = Field(min_length=1, max_length=1000)


def huella(ip):
    """Resumen de la IP para el log: SHA-256 truncado con sal del día.

    No conviene guardar la IP en crudo: el log lleva datos de visitantes y
    así lo que se almacena no es identificable (y rota cada día, RGPD mediante).
    """
    sal = date.today().strftime("%Y%m%d")
    return hashlib.sha256((sal + ip).encode()).hexdigest()[:12]


def poda_visitas():
    """Descarta IPs viejas si el registro del límite se hace grande."""
    if len(visitas) <= MAX_IPS:
        return
    ahora = time.time()
    for ip in list(visitas):
        cola = visitas[ip]
        while cola and ahora - cola[0] > VENTANA_SEGUNDOS:
            cola.popleft()
        if not cola:
            del visitas[ip]
    # Si aún sobran (ataque con muchas IPs vivas), suelta las más antiguas
    while len(visitas) > MAX_IPS:
        vieja = min(visitas, key=lambda ip: visitas[ip][-1])
        del visitas[vieja]


def demasiadas_peticiones(ip):
    poda_visitas()
    ahora = time.time()
    cola = visitas[ip]
    while cola and ahora - cola[0] > VENTANA_SEGUNDOS:
        cola.popleft()
    if len(cola) >= LIMITE_PETICIONES:
        return True
    cola.append(ahora)
    return False


def linea(objeto):
    """Cada mensaje del stream es una línea JSON (formato NDJSON)."""
    return json.dumps(objeto, ensure_ascii=False) + "\n"


@app.get("/")
def inicio():
    return FileResponse(BASE / "static" / "index.html")


@app.post("/api/chat")
def chat(cuerpo: Pregunta, peticion: Request):
    # Detrás de Cloudflare Tunnel la IP real llega en esta cabecera
    ip = peticion.headers.get("cf-connecting-ip") or (peticion.client.host if peticion.client else "?")
    pregunta = cuerpo.pregunta.strip()
    # Una sola línea por pregunta (sin saltos que puedan falsear el log)
    en_una_linea = " ".join(pregunta.split())

    if demasiadas_peticiones(ip):
        registro.info("%s | BLOQUEADA (límite) | %s", huella(ip), en_una_linea)
        return JSONResponse({"error": "Demasiadas preguntas seguidas."}, status_code=429)

    registro.info("%s | %s", huella(ip), en_una_linea)

    def flujo():
        with candado:
            try:
                fragmentos, metas, _ = rag.recuperar(estado["coleccion"], pregunta)
                if rag.sin_contexto(fragmentos):
                    yield linea({"t": "No lo sé, eso no aparece en la documentación."})
                else:
                    for trozo in rag.generar(pregunta, fragmentos, metas):
                        if trozo:
                            yield linea({"t": trozo})
                yield linea({"fuentes": rag.fuentes_de(metas)})
            except Exception:
                traceback.print_exc()
                yield linea({"error": "No se pudo generar la respuesta. ¿Está Ollama en marcha?"})

    return StreamingResponse(
        flujo(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
