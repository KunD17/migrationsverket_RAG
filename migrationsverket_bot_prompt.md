# Migrationsverket Chatbot — Full Build Instructions for Claude in VS Code

Use this file to prompt Claude in VS Code. Feed it section by section as you build, or paste the full thing at the start.

---

## Full Prompt

I want to build a local RAG-based agentic chatbot that answers Swedish immigration questions by retrieving information from the Swedish Migrationsverket website (https://www.migrationsverket.se). This is a portfolio project and needs to be built to a production-minded standard, not as a tutorial or script dump.

### Tech stack
- Ollama for local LLM inference (Llama 3.1 8B) and embeddings (nomic-embed-text). The model must handle Swedish natively — Llama 3.1 has strong Swedish language support.
- LangChain for chain and agent orchestration
- ChromaDB as the local vector store
- BeautifulSoup for scraping Migrationsverket
- langdetect for query language detection
- Streamlit for the UI
- SQLite for logging
- Python 3.11+

### Project structure — strict separation of concerns

```
migrationsverket_bot/
├── ingestion/
│   ├── scraper.py              # scrapes and cleans Swedish Migrationsverket pages
│   └── chunker.py             # chunks by document section, not fixed char size
├── retrieval/
│   ├── embedder.py            # embedding logic using nomic-embed-text via Ollama
│   └── vector_store.py        # ChromaDB setup, indexing, and retrieval
├── agent/
│   ├── query_reformulator.py  # reformulates query if retrieval confidence is low
│   ├── relevance_checker.py   # checks if retrieved chunks actually answer the question
│   ├── translator.py          # handles query and answer translation via Ollama
│   ├── language_detector.py   # detects query language using langdetect
│   └── rag_agent.py           # main agent loop combining all steps
├── evaluation/
│   ├── test_set.json          # 25 manually written question/answer pairs in both Swedish and English
│   ├── evaluator.py           # measures retrieval accuracy and answer faithfulness
│   └── metrics_logger.py      # logs results to SQLite
├── observability/
│   └── logger.py              # logs every query, chunks retrieved, confidence, latency, answer
├── ui/
│   └── app.py                 # Streamlit app with chat tab and metrics dashboard tab
├── requirements.txt
├── README.md
└── config.py                  # all configurable parameters in one place
```

### Multilingual pipeline — this is central to the architecture

All content is scraped, chunked, embedded, and stored in Swedish. The multilingual logic works as follows:

1. Detect the language of the incoming query using langdetect
2. If the query is in English: translate it to Swedish using the local Ollama LLM before retrieval
3. Perform retrieval in Swedish against the ChromaDB vector store
4. Generate the answer in Swedish grounded in the retrieved chunks
5. If the user's detected language is English, or if the language toggle is set to English: translate the final answer to English using Ollama before displaying
6. If the query is in Swedish: retrieve and answer in Swedish directly, no translation needed
7. The Streamlit UI must have a language toggle (Svenska / English) that overrides auto-detection when explicitly set by the user
8. Log the detected language, response language, and whether translation was applied in SQLite for every query

This translate→retrieve→translate pattern must be implemented as a clean pipeline step in translator.py, not scattered across the agent logic.

### Agent loop — this is the most important part

The agent must NOT be a simple retrieve-and-answer chain. It must implement the following steps:

1. Receive user query
2. Detect language and translate query to Swedish if needed
3. Embed the (Swedish) query and retrieve top-k chunks from ChromaDB with confidence scores
4. Run a relevance check — use the LLM to assess whether the retrieved chunks actually contain enough information to answer the question
5. If relevance is low: reformulate the query using the LLM and retrieve again (maximum 2 retries)
6. If after retries the chunks are still not relevant: return a grounded fallback response telling the user the answer is not available in the Migrationsverket data, and suggest they visit the website directly. Deliver this fallback in the user's language.
7. If relevance is sufficient: generate an answer strictly grounded in the retrieved chunks
8. Translate the answer to English if required
9. Every answer must cite the source URL and section it was retrieved from
10. Log the full interaction to SQLite including: original query, detected language, reformulated query if any, chunks retrieved, confidence scores, relevance decision, translation steps applied, final answer, and latency

### Evaluation framework

- Create a test set of 25 question/answer pairs in test_set.json — include questions in both Swedish and English covering common immigration scenarios: residence permits, work permits, asylum, citizenship, family reunification
- evaluator.py must measure:
  - Retrieval accuracy: did the correct chunk come back for each question
  - Answer faithfulness: did the answer stay grounded in retrieved text with no hallucination
  - Translation quality: does the English answer preserve the meaning of the Swedish source answer
- Results must be logged to SQLite and displayable in the Streamlit metrics dashboard

### Streamlit UI requirements

Tab 1 — Chat interface:
- Language toggle (Svenska / English) in the top right — overrides auto-detection
- Source citations shown below each answer (URL and section)
- Confidence indicator per answer
- Indicator showing whether the response was translated

Tab 2 — Metrics dashboard:
- Retrieval accuracy score
- Faithfulness score
- Average latency
- Translation usage rate
- Full query log table

### Code quality requirements

- Every module must have a clear docstring explaining what it does
- config.py must contain all parameters (model names, chunk size, top-k, confidence threshold, retry limit, supported languages) so nothing is hardcoded
- requirements.txt must be complete and pinned to specific versions
- README.md must include:
  - Project overview
  - Architecture diagram in Mermaid format
  - Setup instructions
  - Example queries in both Swedish and English
  - A section explaining the cross-lingual RAG architecture
- Commit regularly with meaningful commit messages — do not put everything in one commit

### Do not
- Put everything in one file
- Use OpenAI or any paid API — everything must run locally via Ollama
- Use fixed character-size chunking — chunk by document section and heading structure
- Generate answers that are not grounded in retrieved chunks
- Hardcode any parameters that belong in config.py
- Apply translation using any external service — all translation must go through the local Ollama LLM
- Collapse translator.py or language_detector.py into the agent loop — keep them as separate modules

### Build order

Implement one module at a time in this exact order:

1. Scaffold the full project structure with empty files and docstrings first
2. ingestion/ — scraper.py then chunker.py
3. retrieval/ — embedder.py then vector_store.py
4. agent/ — language_detector.py, translator.py, relevance_checker.py, query_reformulator.py, then rag_agent.py
5. evaluation/ — test_set.json, evaluator.py, metrics_logger.py
6. observability/ — logger.py
7. ui/ — app.py
8. README.md and requirements.txt last

Ask me before making any major architectural decisions. Do not move to the next module until I confirm the current one is working.

---

## Watch-outs When Prompting Claude in VS Code

These are the shortcuts Claude will try to take. Push back on all of them:

- **Collapsing modules** — it will try to merge translator.py and language_detector.py into rag_agent.py. Don't allow it.
- **Fixed-size chunking** — it will default to splitting by character count. Insist on section/heading-based chunking.
- **Skipping the relevance check** — it will try to go straight from retrieval to answer generation. The relevance check and query reformulation loop are non-negotiable.
- **Hardcoding parameters** — push everything to config.py.
- **One big commit** — remind it to commit after each module.

---

## What to Say on Your CV When It's Done

Once the project is complete and on GitHub, use this bullet:

*"Built and deployed a cross-lingual agentic RAG system for Swedish immigration queries using Ollama (Llama 3.1), LangChain, and ChromaDB — featuring self-correcting retrieval with query reformulation, cross-lingual query translation, source grounding, and an evaluation pipeline measuring retrieval accuracy and answer faithfulness."*
