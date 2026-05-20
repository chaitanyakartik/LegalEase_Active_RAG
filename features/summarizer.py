from langchain_chroma import Chroma

from config import GEMINI_API_KEY, PRO_MODEL, CHROMA_DIR
from rag.embeddings import LocalEmbeddings
from prompts.templates import SUMMARIZE_PROMPT
from rag.nodes import fallback_generate

# Old direct Gemini/OpenAI code (commented out):
# import google.generativeai as genai
# genai.configure(api_key=GEMINI_API_KEY)
# _pro = genai.GenerativeModel(PRO_MODEL)



def summarize_document(case_id: str, doc_id: str) -> str:
    """
    Retrieve all chunks for a specific document from ChromaDB and
    generate a structured legal summary.
    """
    embeddings = LocalEmbeddings(dim=256)
    vectorstore = Chroma(
        collection_name=f"case_{case_id}",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )

    # Retrieve all chunks belonging to this document
    results = vectorstore.get(where={"source_doc": doc_id})
    docs_content = results.get("documents", [])

    if not docs_content:
        return "No document content found. Please ensure the document was uploaded and processed successfully."

    # Combine content (skip base64 image data)
    text_parts = []
    for content in docs_content:
        if content and len(content) < 5000:
            text_parts.append(content)

    combined = "\n\n---\n\n".join(text_parts[:20])  # Limit to avoid token overflow

    prompt = SUMMARIZE_PROMPT.format(content=combined)
    # Use fallback generation only (Groq / Ollama) since Gemini/OpenAI quota is disabled.
    # return _pro.generate_content(prompt).text.strip()
    return fallback_generate(prompt)
