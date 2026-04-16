import os
import shutil
import uuid
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.stores import InMemoryStore
from langchain_classic.retrievers.multi_vector import MultiVectorRetriever

from config import GEMINI_API_KEY, CHROMA_DIR, UPLOADS_DIR, EMBEDDING_MODEL
from ingestion.extract import extract
from ingestion.chunker import chunk_and_summarize
from db.models import add_document
from logging_config import get_logger

logger = get_logger("ingestion.ingest")

# In-memory docstore shared across the process lifetime
# For persistence across restarts, a proper DB-backed store would be needed
_docstores: dict[str, InMemoryStore] = {}


def _get_retriever(collection_name: str) -> MultiVectorRetriever:
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY
    )
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )
    if collection_name not in _docstores:
        _docstores[collection_name] = InMemoryStore()

    return MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=_docstores[collection_name],
        id_key="doc_id"
    )


def get_retriever_for_case(case_id: str) -> MultiVectorRetriever:
    return _get_retriever(f"case_{case_id}")


def get_global_retriever() -> MultiVectorRetriever:
    return _get_retriever("all_cases")


def ingest_file(file_path: str, case_id: str, original_filename: str) -> str:
    """
    Full ingestion pipeline for one file:
    1. Save to uploads dir
    2. Extract text + images
    3. Chunk + summarize
    4. Embed and store in ChromaDB (per-case + global collections)
    5. Record in SQLite

    Returns the document ID.
    """
    logger.info("=" * 80)
    logger.info("📥 STARTING FILE INGESTION")
    logger.info("=" * 80)
    logger.info(f"File: {original_filename}")
    logger.info(f"Case ID: {case_id}")
    logger.info(f"Source path: {file_path}")

    os.makedirs(os.path.join(UPLOADS_DIR, case_id), exist_ok=True)
    dest_path = os.path.join(UPLOADS_DIR, case_id, original_filename)
    if file_path != dest_path:
        shutil.copy2(file_path, dest_path)
        logger.info(f"✓ File copied to: {dest_path}")

    file_ext = original_filename.rsplit(".", 1)[-1].lower()
    doc_id = add_document(case_id, original_filename, file_ext, dest_path)
    logger.info(f"✓ Document registered with ID: {doc_id}")

    logger.info("-" * 80)
    logger.info("📄 EXTRACTION: Extracting text and images...")
    extracted = extract(dest_path)
    logger.info(f"✓ Text extracted: {len(extracted['text'])} characters")
    logger.info(f"✓ Images extracted: {len(extracted['images'])}")

    logger.info("-" * 80)
    logger.info("✂️  CHUNKING & SUMMARIZING: Processing extracted content...")
    chunked = chunk_and_summarize(extracted["text"], extracted["images"])
    logger.info(f"✓ Text chunks: {len(chunked['text_chunks'])}")
    logger.info(f"✓ Image descriptions: {len(chunked['image_descriptions'])}")

    logger.info("-" * 80)
    logger.info("🗂️  STORING: Adding to vector databases...")
    _store_in_collection(chunked, doc_id, case_id, f"case_{case_id}")
    _store_in_collection(chunked, doc_id, case_id, "all_cases")

    logger.info("=" * 80)
    logger.info("✅ FILE INGESTION COMPLETE")
    logger.info("=" * 80)

    return doc_id


def _store_in_collection(chunked: dict, doc_id: str, case_id: str, collection_name: str):
    logger.info(f"   Storing in collection: {collection_name}")
    retriever = _get_retriever(collection_name)

    # Store text chunks
    for i, (chunk, summary) in enumerate(zip(chunked["text_chunks"], chunked["text_summaries"])):
        chunk_id = f"{doc_id}_text_{i}"
        summary_doc = Document(
            page_content=summary,
            metadata={"doc_id": chunk_id, "case_id": case_id, "type": "text", "source_doc": doc_id}
        )
        original_doc = Document(
            page_content=chunk,
            metadata={"doc_id": chunk_id, "case_id": case_id, "type": "text", "source_doc": doc_id}
        )
        retriever.vectorstore.add_documents([summary_doc])
        retriever.docstore.mset([(chunk_id, original_doc)])
    logger.info(f"   ✓ Stored {len(chunked['text_chunks'])} text chunks (with embeddings)")

    # Store image descriptions
    for i, (b64, desc) in enumerate(zip(chunked["image_b64s"], chunked["image_descriptions"])):
        img_id = f"{doc_id}_img_{i}"
        desc_doc = Document(
            page_content=desc,
            metadata={"doc_id": img_id, "case_id": case_id, "type": "image", "source_doc": doc_id}
        )
        original_doc = Document(
            page_content=b64,
            metadata={"doc_id": img_id, "case_id": case_id, "type": "image", "source_doc": doc_id}
        )
        retriever.vectorstore.add_documents([desc_doc])
        retriever.docstore.mset([(img_id, original_doc)])
    logger.info(f"   ✓ Stored {len(chunked['image_descriptions'])} image descriptions (with embeddings)")
