#!/usr/bin/env python
"""
Script to bulk ingest documents into the knowledge base.
Usage: python ingest_docs.py <docs_folder> <case_id>
"""
import os
import sys
from pathlib import Path
from db.init_db import init_db
from db.models import create_case, get_case
from ingestion.ingest import ingest_file
from logging_config import get_logger

logger = get_logger("ingest_docs")


def ingest_folder(folder_path: str, case_title: str = "Consumer Law Knowledge Base",
                 case_category: str = "Consumer Law"):
    """
    Ingest all documents from a folder into the system.

    Args:
        folder_path: Path to folder containing documents
        case_title: Name of the case to create/use
        case_category: Category of the case

    Returns:
        Number of documents ingested
    """
    init_db()

    # Check folder exists
    folder = Path(folder_path)
    if not folder.exists():
        logger.error(f"❌ Folder not found: {folder_path}")
        return 0

    # Create or get case
    existing_cases = [c for c in __import__('db.models', fromlist=['get_cases']).get_cases()
                     if c['title'] == case_title]
    if existing_cases:
        case_id = existing_cases[0]['id']
        logger.info(f"📂 Using existing case: {case_id}")
    else:
        case_id = create_case(case_title, case_category, f"Knowledge base for {case_category}")
        logger.info(f"📂 Created new case: {case_id}")

    # Find all documents
    supported_extensions = ['.pdf', '.txt', '.docx', '.doc', '.png', '.jpg', '.jpeg']
    files = [f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in supported_extensions]

    if not files:
        logger.warning(f"⚠️  No supported documents found in {folder_path}")
        return 0

    logger.info(f"📥 Starting ingestion of {len(files)} documents...")
    logger.info("=" * 80)

    ingested_count = 0
    failed_files = []

    for file_path in sorted(files):
        try:
            logger.info(f"\n📄 Processing: {file_path.name}")
            doc_id = ingest_file(str(file_path), case_id, file_path.name)
            logger.info(f"✅ Successfully ingested: {file_path.name} (ID: {doc_id})")
            ingested_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to ingest {file_path.name}: {e}")
            failed_files.append(file_path.name)

    logger.info("\n" + "=" * 80)
    logger.info(f"📊 INGESTION SUMMARY")
    logger.info(f"   ✅ Successful: {ingested_count}/{len(files)}")
    logger.info(f"   ❌ Failed: {len(failed_files)}/{len(files)}")
    if failed_files:
        logger.info(f"   Failed files: {', '.join(failed_files)}")
    logger.info("=" * 80)

    return ingested_count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_docs.py <docs_folder> [case_title] [case_category]")
        print("\nExample:")
        print("  python ingest_docs.py ./docs")
        print("  python ingest_docs.py ./docs 'My Case' 'Contract Law'")
        sys.exit(1)

    folder = sys.argv[1]
    case_title = sys.argv[2] if len(sys.argv) > 2 else "Consumer Law Knowledge Base"
    category = sys.argv[3] if len(sys.argv) > 3 else "Consumer Law"

    count = ingest_folder(folder, case_title, category)
    sys.exit(0 if count > 0 else 1)
