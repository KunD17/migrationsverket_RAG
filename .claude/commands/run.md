# Run the Migrationsverket RAG app

First, verify Ollama is running and the required models are available:

```bash
ollama list
```

Both `llama3.1` and `nomic-embed-text` must be present. If not:

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

Then start the Streamlit UI:

```bash
python -m streamlit run migrationsverket_bot/ui/app.py
```

Opens at http://localhost:8501.

- **Chat tab** — ask questions in English or Swedish; source citations and confidence scores appear below each answer
- **Metrics tab** — query history, average latency, confidence distribution

If the vector store is empty (first run or after a wipe), run ingestion first:

```bash
python ingest_personal.py
```
