"""Application configuration for the Migrationsverket RAG chatbot."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = ROOT_DIR / "migrationsverket_rag.sqlite"

# Ollama models and endpoints
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1"
EMBEDDING_MODEL = "nomic-embed-text"

# Retrieval settings
TOP_K = 5
CONFIDENCE_THRESHOLD = 0.4
RETRIEVAL_BATCH_SIZE = 10
RETRY_LIMIT = 2
SUPPORTED_LANGUAGES = ["sv", "en"]
DEFAULT_LANGUAGE = "sv"

# Scraping settings
BASE_URL = "https://www.migrationsverket.se"
USER_AGENT = "Mozilla/5.0 (compatible; MigrationsverketRAG/1.0)"
SCRAPE_TIMEOUT = 30

# UI settings
STREAMLIT_PORT = 8501

# Evaluation settings
EVALUATION_TEST_SET_PATH = ROOT_DIR / "evaluation" / "test_set.json"
LOGGING_DB = DB_PATH

# Application metadata
PROJECT_NAME = "Migrationsverket RAG Chatbot"
VERSION = "0.1.0"
