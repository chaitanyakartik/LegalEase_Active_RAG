import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

FLASH_MODEL = "gemini-2.5-flash"
PRO_MODEL = "gemini-2.5-pro"
OPENAI_MODEL = "gpt-4o-mini"
GROQ_MODEL = "groq/compound-mini"  # Faster free model
GROQ_FALLBACK_MODELS = [
    "groq/compound-mini",
    "groq/compound",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]
OLLAMA_MODEL = "mistral"  # Download: ollama pull mistral

MAX_RESPONSE_TOKENS = 1024

EMBEDDING_MODEL = "models/gemini-embedding-001"

CHROMA_DIR = "chroma_db"
UPLOADS_DIR = "uploads"
DB_PATH = "legalease.db"

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

LAW_CATEGORIES = ["Civil Law", "Criminal Law", "Consumer Law"]

DRAFT_TYPES = ["Legal Notice", "Complaint", "Response Letter", "Agreement Template", "Case Notes"]
EVENT_TYPES = ["Hearing", "Filing", "Deadline", "Note"]

# Rate limiting configuration
MAX_RETRIES = 1
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 300    # 5 minutes
BATCH_DELAY = 0.2        # delay between API calls (seconds)

# Fallback settings
USE_FALLBACK = True  # Enable fallback when primary API fails
FALLBACK_PRIORITY = ["groq", "ollama"]  # Try Groq first (free), then Ollama (local)
USE_GOOGLE_PRIMARY = os.getenv("USE_GOOGLE_PRIMARY", "false").lower() in ("1", "true", "yes")
