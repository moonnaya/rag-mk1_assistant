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
MODELO = "qwen2.5:7b-instruct"       # modelo que redacta las respuestas
MODELO_EMB = "bge-m3"                # modelo de embeddings (multilingüe)
N_FRAGMENTOS = 6                     # cuántos trozos se pasan al modelo
MAX_CAR = 800                        # tamaño máximo aproximado de cada trozo
NUM_CTX = 4096                       # ventana de contexto del modelo (en tokens)
UMBRAL_DISTANCIA = 0.55              # descarta fragmentos con distancia coseno mayor que esto
                                     # (medido: relevante 0.34-0.52; fuera de corpus >= 0.55)
TEMPERATURA = 0.1                    # baja: respuestas pegadas al contexto, sin divagar
GLOSARIO_FILE = Path("glosario.md")  # vocabulario y estilo: se añade SIEMPRE al prompt
DEBUG = "--debug" in sys.argv        # muestra qué fragmentos se recuperan


def trocear(texto, max_car=MAX_CAR):
    """Divide por encabezados Markdown; las secciones largas se parten por párrafos.

    Devuelve una lista de tuplas (titulo_de_seccion, fragmento).
    """
    secciones = re.split(r"(?m)^(?=#{1,4} )", texto)
    trozos = []
    for sec in secciones:
        sec = sec.strip()
        if not sec:
            continue
        if len(sec) <= max_car:
            trozos.append((titulo_de(sec), sec))
            continue
        titulo = sec.splitlines()[0] if sec.startswith("#") else ""
        actual = ""
        for parrafo in sec.split("\n\n"):
            if actual and len(actual) + len(parrafo) > max_car:
                trozos.append((titulo_de(actual), actual.strip()))
                actual = (titulo + "\n\n") if titulo and parrafo != titulo else ""
            actual += parrafo + "\n\n"
        if actual.strip():
            trozos.append((titulo_de(actual), actual.strip()))
    return trozos


def titulo_de(trozo):
    """Primera línea del fragmento si es encabezado, como texto limpio."""
    for linea in trozo.splitlines():
        if linea.startswith("#"):
            return linea.lstrip("#").strip()
        if linea.strip():
            break
    return ""



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
        for n, (seccion, trozo) in enumerate(trocear(texto)):
            ids.append(f"{nombre}-{n}")
            docs.append(trozo)
            metas.append({"fuente": nombre, "seccion": seccion})

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
        "Responde en español usando SOLO el contexto proporcionado.\n"
        "REGLAS (obligatorias):\n"
        "- Cada afirmación factual debe terminar con la fuente entre corchetes, "
        "así: [nombre-archivo]. No la repitas más de una vez por párrafo.\n"
        "- Si el contexto no basta para responder, tu respuesta COMPLETA debe "
        "ser exactamente y solo: "
        "\"No lo sé, eso no aparece en la documentación.\" "
        "Sin añadir nada más: ni sugerencias, ni escenarios, ni fuentes.\n"
        "- Nunca inventes funciones, macros, constantes, nombres ni cifras. "
        "Si el contexto incluye código, cópialo tal cual.\n"
        "- No uses conocimiento ajeno al contexto, aunque lo parezcas saber."
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
    """Busca los fragmentos más parecidos a la pregunta (por encima del umbral).

    Devuelve (fragmentos, metadatos, distancias).
    """
    res = coleccion.query(
        query_embeddings=embeber([pregunta]),
        n_results=N_FRAGMENTOS,
        include=["documents", "metadatas", "distances"],
    )
    buenos = [i for i, d in enumerate(res["distances"][0]) if d <= UMBRAL_DISTANCIA]
    return (
        [res["documents"][0][i] for i in buenos],
        [res["metadatas"][0][i] for i in buenos],
        [res["distances"][0][i] for i in buenos],
    )


def generar(pregunta, fragmentos, metas):
    """Generador: va devolviendo trozos de la respuesta según el modelo los produce."""
    contexto = "\n\n".join(
        f"[{m['fuente']}] {('('+m['seccion']+') ' if m.get('seccion') else '')}{d}"
        for d, m in zip(fragmentos, metas)
    )
    flujo = ollama.chat(
        model=MODELO,
        messages=[
            {"role": "system", "content": construir_instrucciones()},
            {"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"},
        ],
        options={"num_ctx": NUM_CTX, "temperature": TEMPERATURA, "top_p": 0.8},
        stream=True,
    )
    for parte in flujo:
        yield parte["message"]["content"]


def sin_contexto(fragmentos):
    """Verdad si tras el filtro de distancia no queda fragmento útil."""
    return not fragmentos


def fuentes_de(metas):
    """Fuentes para mostrar: 'archivo › sección', ordenadas y sin repetir."""
    return sorted({f"{m['fuente']} › {m['seccion']}" if m.get("seccion") else m["fuente"]
                   for m in metas})


def responder(coleccion, pregunta):
    """Versión para terminal: imprime la respuesta en streaming."""
    fragmentos, metas, distancias = recuperar(coleccion, pregunta)
    if DEBUG:
        print("\n--- Fragmentos recuperados ---")
        for d, m, dist in zip(fragmentos, metas, distancias):
            print(f"[{m['fuente']}] distancia={dist:.3f}\n{d[:300]}...\n")
        print("------------------------------")

    print("\nIA: ", end="", flush=True)
    if sin_contexto(fragmentos):
        print("No lo sé, eso no aparece en la documentación.")
        return
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
