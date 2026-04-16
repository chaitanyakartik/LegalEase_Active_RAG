"""Logging configuration for LegalEase RAG system."""
import logging
import sys
import os
from datetime import datetime

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/rag_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

# Get logger for RAG system
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"legalease.{name}")

# Suppress verbose logs from libraries
logging.getLogger("langchain").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)
