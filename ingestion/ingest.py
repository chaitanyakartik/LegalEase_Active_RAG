import os
import shutil
import uuid
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.stores import InMemoryStore
from rag.raptor_retriever import CustomRaptorRetriever

from config import CHROMA_DIR, UPLOADS_DIR
from rag.embeddings import LocalEmbeddings
from ingestion.extract import extract
from ingestion.chunker import chunk_and_summarize
from db.models import add_document
from logging_config import get_logger

logger = get_logger("ingestion.ingest")

# In-memory docstore shared across the process lifetime
# For persistence across restarts, a proper DB-backed store would be needed
_docstores: dict[str, InMemoryStore] = {}


def _get_retriever(collection_name: str) -> CustomRaptorRetriever:
    embeddings = LocalEmbeddings(dim=256)
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )
    
    # Collect all documents from the vectorstore
    all_docs = vectorstore.get(include=["documents", "metadatas"])
    documents = []
    for doc_content, metadata in zip(all_docs["documents"], all_docs["metadatas"]):
        documents.append(Document(page_content=doc_content, metadata=metadata))
    
    # Build CustomRaptorRetriever with the documents
    raptor = CustomRaptorRetriever(documents=documents, embedding=embeddings, k=4)
    return raptor


def get_retriever_for_case(case_id: str) -> CustomRaptorRetriever:
    return _get_retriever(f"case_{case_id}")


def get_global_retriever() -> CustomRaptorRetriever:
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
    embeddings = LocalEmbeddings(dim=256)
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )

    # Store text chunks (summaries for retrieval, full chunks as metadata)
    for i, (chunk, summary) in enumerate(zip(chunked["text_chunks"], chunked["text_summaries"])):
        chunk_id = f"{doc_id}_text_{i}"
        summary_doc = Document(
            page_content=summary,
            metadata={"doc_id": chunk_id, "case_id": case_id, "type": "text", "source_doc": doc_id, "full_chunk": chunk}
        )
        vectorstore.add_documents([summary_doc])
    logger.info(f"   ✓ Stored {len(chunked['text_chunks'])} text chunks (with embeddings)")

    # Store image descriptions
    for i, (b64, desc) in enumerate(zip(chunked["image_b64s"], chunked["image_descriptions"])):
        img_id = f"{doc_id}_img_{i}"
        desc_doc = Document(
            page_content=desc,
            metadata={"doc_id": img_id, "case_id": case_id, "type": "image", "source_doc": doc_id, "b64": b64}
        )
        vectorstore.add_documents([desc_doc])
    logger.info(f"   ✓ Stored {len(chunked['image_descriptions'])} image descriptions (with embeddings)")
