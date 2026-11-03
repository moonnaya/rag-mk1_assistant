"""RAG local: Chroma (búsqueda) + Ollama (embeddings y generación).

Uso:
    python rag.py                   # chat interactivo
    python rag.py --debug           # además muestra los fragmentos recuperados
    python rag.py --reindex         # borra la base y vuelve a indexar docs/
    python rag.py --reindex --debug

Antes de usarlo por primera vez:
    ollama pull bge-m3              # modelo de embeddings multilingüe
"""
import re
import sys
from pathlib import Path

import chromadb
import ollama

DOCS_DIR = Path("docs")              # carpeta con tus .md y .txt (admite subcarpetas)
DB_DIR = "chroma_db"                 # donde Chroma guarda los datos
COLECCION = "docs_bge_m3"            # nombre de la colección (ligado al modelo de embeddings)
MODELO = "qwen2:7b"                  # modelo que redacta las respuestas
MODELO_EMB = "bge-m3"                # modelo de embeddings (multilingüe)
N_FRAGMENTOS = 4                     # cuántos trozos se pasan al modelo
MAX_CAR = 1200                       # tamaño máximo aproximado de cada trozo
NUM_CTX = 4096                       # ventana de contexto del modelo (en tokens)
GLOSARIO_FILE = Path("glosario.md")  # vocabulario y estilo: se añade SIEMPRE al prompt
DEBUG = "--debug" in sys.argv        # muestra qué fragmentos se recuperan


def trocear(texto, max_car=MAX_CAR):
    """Divide por encabezados Markdown; las secciones largas se parten por párrafos."""
    secciones = re.split(r"(?m)^(?=#{1,4} )", texto)
    trozos = []
    for sec in secciones:
        sec = sec.strip()
        if not sec:
            continue
        if len(sec) <= max_car:
            trozos.append(sec)
            continue
        titulo = sec.splitlines()[0] if sec.startswith("#") else ""
        actual = ""
        for parrafo in sec.split("\n\n"):
            if actual and len(actual) + len(parrafo) > max_car:
                trozos.append(actual.strip())
                actual = (titulo + "\n\n") if titulo and parrafo != titulo else ""
            actual += parrafo + "\n\n"
        if actual.strip():
            trozos.append(actual.strip())
    return trozos


def embeber(textos):
    """Convierte una lista de textos en vectores usando Ollama."""
    return ollama.embed(model=MODELO_EMB, input=textos)["embeddings"]


def indexar(coleccion):
    """Añade a Chroma los fragmentos que todavía no están indexados."""
    ids, docs, metas = [], [], []
    for f in sorted(DOCS_DIR.rglob("*")):  # incluye subcarpetas
        if f.suffix.lower() not in {".txt", ".md"}:
            continue
        nombre = f.relative_to(DOCS_DIR).as_posix()
        texto = f.read_text(encoding="utf-8", errors="replace")
        for n, trozo in enumerate(trocear(texto)):
            ids.append(f"{nombre}-{n}")
            docs.append(trozo)
            metas.append({"fuente": nombre})

    existentes = set(coleccion.get(include=[])["ids"])
    nuevos = [i for i, id_ in enumerate(ids) if id_ not in existentes]
    LOTE = 16
    for k in range(0, len(nuevos), LOTE):
        idx = nuevos[k:k + LOTE]
        textos = [docs[i] for i in idx]
        coleccion.add(
            ids=[ids[i] for i in idx],
            documents=textos,
            metadatas=[metas[i] for i in idx],
            embeddings=embeber(textos),
        )
        print(f"  indexados {min(k + LOTE, len(nuevos))}/{len(nuevos)}", end="\r")
    if nuevos:
        print()
    return len(nuevos), len(ids)


def construir_instrucciones():
    """Instrucciones base + contenido de glosario.md (si existe)."""
    base = (
        "Responde en español usando SOLO el contexto proporcionado. "
        "Si la respuesta no está en el contexto, di que no lo sabes. "
        "Si el contexto incluye código, cópialo tal cual y no inventes "
        "funciones, macros ni constantes que no aparezcan en él."
    )
    if GLOSARIO_FILE.exists():
        glosario = GLOSARIO_FILE.read_text(encoding="utf-8").strip()
        if glosario:
            base += (
                "\n\nSigue estrictamente este estilo y vocabulario "
                "(úsalo en tus respuestas):\n" + glosario
            )
    return base


def abrir_coleccion(reindex=False):
    """Abre (o crea) la colección de Chroma. Con reindex=True la borra antes."""
    cliente = chromadb.PersistentClient(path=DB_DIR)
    if reindex:
        try:
            cliente.delete_collection(COLECCION)
        except Exception:
            pass
    return cliente.get_or_create_collection(
        COLECCION, metadata={"hnsw:space": "cosine"}
    )


def recuperar(coleccion, pregunta):
    """Busca los fragmentos más parecidos a la pregunta.

    Devuelve (fragmentos, metadatos, distancias).
    """
    res = coleccion.query(
        query_embeddings=embeber([pregunta]),
        n_results=N_FRAGMENTOS,
        include=["documents", "metadatas", "distances"],
    )
    return res["documents"][0], res["metadatas"][0], res["distances"][0]


def generar(pregunta, fragmentos, metas):
    """Generador: va devolviendo trozos de la respuesta según el modelo los produce."""
    contexto = "\n\n".join(f"[{m['fuente']}] {d}" for d, m in zip(fragmentos, metas))
    flujo = ollama.chat(
        model=MODELO,
        messages=[
            {"role": "system", "content": construir_instrucciones()},
            {"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"},
        ],
        options={"num_ctx": NUM_CTX},
        stream=True,
    )
    for parte in flujo:
        yield parte["message"]["content"]


def fuentes_de(metas):
    """Lista ordenada y sin repetir de los archivos de los que salen los fragmentos."""
    return sorted({m["fuente"] for m in metas})


def responder(coleccion, pregunta):
    """Versión para terminal: imprime la respuesta en streaming."""
    fragmentos, metas, distancias = recuperar(coleccion, pregunta)
    if DEBUG:
        print("\n--- Fragmentos recuperados ---")
        for d, m, dist in zip(fragmentos, metas, distancias):
            print(f"[{m['fuente']}] distancia={dist:.3f}\n{d[:300]}...\n")
        print("------------------------------")

    print("\nIA: ", end="", flush=True)
    for trozo in generar(pregunta, fragmentos, metas):
        print(trozo, end="", flush=True)
    print(f"\n(Fuentes: {', '.join(fuentes_de(metas))})\n")


def main():
    # Comprueba que el modelo de embeddings está descargado
    try:
        embeber(["prueba"])
    except Exception as e:
        print(f"No se pudo usar el modelo de embeddings '{MODELO_EMB}': {e}")
        print(f"Descárgalo con:  ollama pull {MODELO_EMB}")
        sys.exit(1)

    coleccion = abrir_coleccion(reindex="--reindex" in sys.argv)

    nuevos, total = indexar(coleccion)
    print(f"{total} fragmentos en '{DOCS_DIR}/' ({nuevos} nuevos indexados).")
    print("Si modificas o borras documentos, ejecuta con --reindex.")
    print("Escribe tu pregunta (o 'salir').\n")

    while True:
        pregunta = input("Tú: ").strip()
        if pregunta.lower() in {"salir", "exit", "q"}:
            break
        if not pregunta:
            continue
        responder(coleccion, pregunta)


if __name__ == "__main__":
    main()
