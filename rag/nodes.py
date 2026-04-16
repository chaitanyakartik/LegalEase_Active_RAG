import google.generativeai as genai
from langchain_core.documents import Document
from duckduckgo_search import DDGS

from config import GEMINI_API_KEY, FLASH_MODEL, PRO_MODEL
from rag.state import RAGState
from prompts.templates import (
    ROUTER_PROMPT, MULTIQUERY_PROMPT, GRADE_PROMPT,
    GENERATE_PROMPT, HALLUCINATION_PROMPT, DIRECT_PROMPT
)
from logging_config import get_logger

logger = get_logger("rag.nodes")

genai.configure(api_key=GEMINI_API_KEY)
_flash = genai.GenerativeModel(FLASH_MODEL)
_pro = genai.GenerativeModel(PRO_MODEL)


def _call(model, prompt: str) -> str:
    return model.generate_content(prompt).text.strip()


# --- Node: Question Router ---

def question_router(state: RAGState) -> dict:
    logger.info(f"🔀 QUESTION ROUTER: Analyzing question from category '{state['law_category']}'")
    logger.info(f"   Question: {state['question'][:100]}...")

    prompt = ROUTER_PROMPT.format(
        law_category=state["law_category"],
        question=state["question"]
    )
    result = _call(_flash, prompt).lower()
    route = "legal" if "legal" in result else "general"

    logger.info(f"   ✓ Route Decision: {route.upper()}")
    return {"query_variants": [], "documents": [], "graded_documents": [],
            "web_results": [], "generation": "", "is_relevant": False,
            "is_grounded": False, "retry_count": 0,
            "_route": route}


# --- Node: Direct LLM (non-legal) ---

def llm_direct(state: RAGState) -> dict:
    logger.info("💬 LLM DIRECT: General question - generating direct response (no RAG)")
    prompt = DIRECT_PROMPT.format(question=state["question"])
    generation = _call(_pro, prompt)
    logger.info(f"   ✓ Generated response: {generation[:100]}...")
    return {"generation": generation, "is_grounded": True}


# --- Node: MultiQuery ---

def multi_query(state: RAGState) -> dict:
    logger.info("🔍 MULTI-QUERY: Generating query variants for retrieval")
    prompt = MULTIQUERY_PROMPT.format(
        law_category=state["law_category"],
        question=state["question"]
    )
    result = _call(_flash, prompt)
    variants = [q.strip() for q in result.split("\n") if q.strip()][:3]
    if not variants:
        variants = [state["question"]]

    logger.info(f"   Generated {len(variants)} query variants:")
    for i, variant in enumerate(variants, 1):
        logger.info(f"   {i}. {variant[:80]}...")
    return {"query_variants": variants}


# --- Node: Retrieve ---

def retrieve(state: RAGState) -> dict:
    from ingestion.ingest import get_retriever_for_case, get_global_retriever

    case_id = state.get("case_id")
    logger.info(f"📚 RETRIEVE: Fetching documents from {'case-specific' if case_id else 'global'} vector store")

    retriever = get_retriever_for_case(case_id) if case_id else get_global_retriever()

    seen_ids = set()
    all_docs = []
    for query in state["query_variants"]:
        try:
            docs = retriever.vectorstore.similarity_search(query, k=4)
            logger.info(f"   Query: '{query}' → Found {len(docs)} similar documents")
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
        except Exception as e:
            logger.warning(f"   Error retrieving for query '{query}': {e}")

    logger.info(f"   ✓ Total unique documents retrieved: {len(all_docs)}")
    return {"documents": all_docs}


# --- Node: Grade Documents ---

def grade_documents(state: RAGState) -> dict:
    logger.info(f"⭐ GRADE DOCUMENTS: Evaluating relevance of {len(state['documents'])} documents")

    graded = []
    for i, doc in enumerate(state["documents"], 1):
        # Skip base64 image content for grading — pass it through if present
        content = doc.page_content
        if len(content) > 2000 and not content[:50].isascii():
            graded.append(doc)
            logger.info(f"   Doc {i}: [IMAGE/BINARY] → PASSED (skipped grading)")
            continue
        # Truncate for grading prompt
        display = content[:1500]
        prompt = GRADE_PROMPT.format(question=state["question"], document=display)
        result = _call(_flash, prompt).lower()
        is_relevant = "yes" in result
        if is_relevant:
            graded.append(doc)

        status = "✓ RELEVANT" if is_relevant else "✗ NOT RELEVANT"
        logger.info(f"   Doc {i}: {status} | {content[:80]}...")

    is_relevant = len(graded) > 0
    logger.info(f"   ✓ Total relevant documents: {len(graded)}/{len(state['documents'])}")
    return {"graded_documents": graded, "is_relevant": is_relevant}


# --- Node: Web Search ---

def web_search(state: RAGState) -> dict:
    logger.info(f"🌐 WEB SEARCH: Searching for supplementary information")
    query = state["question"]
    results = []
    try:
        with DDGS() as ddgs:
            search_query = query + " law legal"
            logger.info(f"   Search query: '{search_query}'")
            for r in ddgs.text(search_query, max_results=5):
                snippet = r.get("body", "")
                title = r.get("title", "")
                if snippet:
                    results.append(f"{title}: {snippet}")
                    logger.info(f"   ✓ Found: {title[:80]}...")
    except Exception as e:
        logger.warning(f"   Web search failed: {e}")

    logger.info(f"   ✓ Total web results: {len(results)}")
    return {"web_results": results}


# --- Node: Generate ---

def generate(state: RAGState) -> dict:
    logger.info("✍️  GENERATE: Creating response from graded documents")

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

    logger.info(f"   Context sources: {len(state['graded_documents'])} docs + {len(state.get('web_results', []))} web results")
    logger.info(f"   Context length: {len(context)} characters")

    prompt = GENERATE_PROMPT.format(
        law_category=state["law_category"],
        context=context,
        question=state["question"]
    )
    generation = _call(_pro, prompt)
    logger.info(f"   ✓ Response generated: {generation[:100]}...")
    return {"generation": generation}


# --- Node: Hallucination Check ---

def hallucination_check(state: RAGState) -> dict:
    logger.info("🔐 HALLUCINATION CHECK: Verifying response is grounded in sources")

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

    status = "✓ GROUNDED" if is_grounded else "✗ HALLUCINATION DETECTED"
    logger.info(f"   {status} (retry count: {retry_count})")
    return {"is_grounded": is_grounded, "retry_count": retry_count}
