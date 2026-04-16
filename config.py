import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

FLASH_MODEL = "gemini-2.5-flash"
PRO_MODEL = "gemini-2.5-pro"
EMBEDDING_MODEL = "models/gemini-embedding-001"

CHROMA_DIR = "chroma_db"
UPLOADS_DIR = "uploads"
DB_PATH = "legalease.db"

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

LAW_CATEGORIES = ["Civil Law", "Criminal Law", "Consumer Law"]

DRAFT_TYPES = ["Legal Notice", "Complaint", "Response Letter", "Agreement Template", "Case Notes"]
EVENT_TYPES = ["Hearing", "Filing", "Deadline", "Note"]
