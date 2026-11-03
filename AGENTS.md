# AGENTS.md

Local RAG assistant (Spanish) over `docs/` (MK1 / Mojon Twins game-dev docs): Chroma for search + Ollama for embeddings/generation. No tests, no linters configured.

## Commands

```bash
pip install -r requirements.txt   # use a fresh venv; existing venv/ is Windows-authored (only Scripts/*.exe), useless on Linux/macOS
ollama pull bge-m3                # embeddings model (required)
ollama pull qwen2:7b              # generation model (required)
python rag.py                     # terminal chat; add --debug to show retrieved chunks
python rag.py --reindex           # ONLY way to sync: incremental indexing never updates/deletes existing chunks
python server.py                  # FastAPI web chat at http://127.0.0.1:8000
curl -N -X POST 127.0.0.1:8000/api/chat -d '{"pregunta":"..."}'   # NDJSON streaming endpoint for quick checks
```

Ollama must be running (`ollama serve`) for both entrypoints; they embed/verify a test embedding at startup.

## Gotchas

- README says `llama3.2`; the code uses `qwen2.5:7b-instruct` (MODELO), `bge-m3` (MODELO_EMB), temperature 0.1 and a distance filter (UMBRAL_DISTANCIA) in `rag.py` — trust the code, gazetas readme is stale.
- Anti-hallucination stack: low temperature + strict prompt requiring `[archivo]` citations and literal "No lo sé" fallback + distance filter at `UMBRAL_DISTANCIA = 0.60` (rag.py) tuned by measurement (in-corpus distances 0.34-0.52, out-of-corpus >= 0.60). If retrieval quality changes, re-measure with `--debug`.
- `glosario.md` is appended to the system prompt on every request; editing it changes all answers.
- Chunk metadata includes `seccion` (section heading); `trocear()` returns `(titulo, fragmento)` tuples. Chunk IDs are `{relative-path}-{n}`; editing a `docs/*.md` file after indexing leaves stale chunks in `chroma_db/` unless you run `python rag.py --reindex` — mandatory now after any chunking/metadata change.
- Docs corpus topics live in `docs/`: MK1 compiler manuals (`tecnico.md`, `manual.md`, `msc4.md`, library libs, `lore/`) — the RAG answers must cite only these.
- `agent`, `static/index.html` consumes NDJSON lines `{t: text}` then `{fuentes: [...]}` or `{error: ...}` — keep that shape stable.
- server.py is single-threaded by design: a threading.Lock serializes generation (local Ollama), hard rate limit 10 req/60s per IP (reads `cf-connecting-ip` behind Cloudflare Tunnel).
- Everything (code, prompt, docs) is Spanish; identifier naming is Spanish too — follow it.
- `chroma_db/` and `preguntas.log` are generated artifacts; ignore them.
- Windows-download artifacts `*:Zone.Identifier` files litter the tree; ignore, `.md`/`.txt` suffix filter keeps them out of indexing.
