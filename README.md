# RAG local con Chroma + Ollama

## 1. Requisitos
- Python 3.10 o superior
- Ollama: https://ollama.com/download

## 2. Instalación
```bash
# (opcional) entorno virtual
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

pip install -r requirements.txt

# Descarga el modelo que genera las respuestas (unos 2 GB)
ollama pull llama3.2
```

## 3. Uso
1. Pon tus documentos `.txt` o `.md` en la carpeta `docs/` (ya hay uno de ejemplo).
2. Ejecuta:
```bash
python rag.py
```
3. Pregunta, por ejemplo: "¿Cuántos días tengo para devolver un producto?"

Si cambias o borras documentos, ejecuta `python rag.py --reindex`.

## Notas
- La primera ejecución descarga un pequeño modelo de embeddings que usa Chroma por defecto.
- Todo funciona sin conexión una vez descargado y sin claves de API.
- Para usar otro modelo, cambia `MODELO` en `rag.py` (por ejemplo `mistral`).
- Ajusta `tam` y `solape` en `trocear()` si tus documentos son muy largos o muy cortos.
