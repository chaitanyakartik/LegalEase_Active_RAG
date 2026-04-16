import google.generativeai as genai
from langchain_core.documents import Document
from duckduckgo_search import DDGS

from config import GEMINI_API_KEY, FLASH_MODEL, PRO_MODEL
from rag.state import RAGState
from prompts.templates import (
    ROUTER_PROMPT, MULTIQUERY_PROMPT, GRADE_PROMPT,
    GENERATE_PROMPT, HALLUCINATION_PROMPT, DIRECT_PROMPT
)

genai.configure(api_key=GEMINI_API_KEY)
_flash = genai.GenerativeModel(FLASH_MODEL)
_pro = genai.GenerativeModel(PRO_MODEL)


def _call(model, prompt: str) -> str:
    return model.generate_content(prompt).text.strip()


# --- Node: Question Router ---

def question_router(state: RAGState) -> dict:
    prompt = ROUTER_PROMPT.format(
        law_category=state["law_category"],
        question=state["question"]
    )
    result = _call(_flash, prompt).lower()
    route = "legal" if "legal" in result else "general"
    return {"query_variants": [], "documents": [], "graded_documents": [],
            "web_results": [], "generation": "", "is_relevant": False,
            "is_grounded": False, "retry_count": 0,
            "_route": route}


# --- Node: Direct LLM (non-legal) ---

def llm_direct(state: RAGState) -> dict:
    prompt = DIRECT_PROMPT.format(question=state["question"])
    generation = _call(_pro, prompt)
    return {"generation": generation, "is_grounded": True}


# --- Node: MultiQuery ---

def multi_query(state: RAGState) -> dict:
    prompt = MULTIQUERY_PROMPT.format(
        law_category=state["law_category"],
        question=state["question"]
    )
    result = _call(_flash, prompt)
    variants = [q.strip() for q in result.split("\n") if q.strip()][:3]
    if not variants:
        variants = [state["question"]]
    return {"query_variants": variants}


# --- Node: Retrieve ---

def retrieve(state: RAGState) -> dict:
    from ingestion.ingest import get_retriever_for_case, get_global_retriever

    case_id = state.get("case_id")
    retriever = get_retriever_for_case(case_id) if case_id else get_global_retriever()

    seen_ids = set()
    all_docs = []
    for query in state["query_variants"]:
        try:
            docs = retriever.vectorstore.similarity_search(query, k=4)
            for doc in docs:
                doc_id = doc.metadata.get("doc_id", doc.page_content[:50])
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    # Fetch original content from docstore
                    original = retriever.docstore.mget([doc_id])
                    if original and original[0]:
                        all_docs.append(original[0])
                    else:
                        all_docs.append(doc)
        except Exception:
            pass

    return {"documents": all_docs}


# --- Node: Grade Documents ---

def grade_documents(state: RAGState) -> dict:
    graded = []
    for doc in state["documents"]:
        # Skip base64 image content for grading — pass it through if present
        content = doc.page_content
        if len(content) > 2000 and not content[:50].isascii():
            graded.append(doc)
            continue
        # Truncate for grading prompt
        display = content[:1500]
        prompt = GRADE_PROMPT.format(question=state["question"], document=display)
        result = _call(_flash, prompt).lower()
        if "yes" in result:
            graded.append(doc)

    is_relevant = len(graded) > 0
    return {"graded_documents": graded, "is_relevant": is_relevant}


# --- Node: Web Search ---

def web_search(state: RAGState) -> dict:
    query = state["question"]
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query + " law legal", max_results=5):
                snippet = r.get("body", "")
                title = r.get("title", "")
                if snippet:
                    results.append(f"{title}: {snippet}")
    except Exception:
        pass
    return {"web_results": results}


# --- Node: Generate ---

def generate(state: RAGState) -> dict:
    # Build context from graded docs + web results
    context_parts = []

    for doc in state["graded_documents"]:
        content = doc.page_content
        # Skip raw base64 image data
        if len(content) > 500 and not all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in content[:100]):
            context_parts.append(content)
        elif len(content) <= 500:
            context_parts.append(content)

    for web_result in state.get("web_results", []):
        context_parts.append(f"[Web] {web_result}")

    context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant documents found."

    prompt = GENERATE_PROMPT.format(
        law_category=state["law_category"],
        context=context,
        question=state["question"]
    )
    generation = _call(_pro, prompt)
    return {"generation": generation}


# --- Node: Hallucination Check ---

def hallucination_check(state: RAGState) -> dict:
    context_parts = [doc.page_content for doc in state["graded_documents"]
                     if len(doc.page_content) < 3000]
    context_parts += [f"[Web] {r}" for r in state.get("web_results", [])]
    context = "\n\n".join(context_parts[:5]) if context_parts else "No context."

    prompt = HALLUCINATION_PROMPT.format(
        context=context,
        generation=state["generation"]
    )
    result = _call(_flash, prompt).lower()
    is_grounded = "yes" in result
    retry_count = state.get("retry_count", 0) + 1
    return {"is_grounded": is_grounded, "retry_count": retry_count}
