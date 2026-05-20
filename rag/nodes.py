import google.generativeai as genai
import time
import requests
from langchain_core.documents import Document
from duckduckgo_search import DDGS
from google.api_core.exceptions import ResourceExhausted

from config import (GEMINI_API_KEY, FLASH_MODEL, PRO_MODEL, OPENAI_API_KEY, OPENAI_MODEL,
                   GROQ_API_KEY, GROQ_MODEL, GROQ_FALLBACK_MODELS, OLLAMA_BASE_URL,
                   OLLAMA_MODEL, OLLAMA_API_KEY,
                   MAX_RETRIES, INITIAL_RETRY_DELAY, MAX_RETRY_DELAY, BATCH_DELAY, MAX_RESPONSE_TOKENS,
                   USE_FALLBACK, FALLBACK_PRIORITY, USE_GOOGLE_PRIMARY)
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

# Initialize clients if keys/URLs available
_openai_client = None
if OPENAI_API_KEY:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=OPENAI_API_KEY)

_groq_client = None
if GROQ_API_KEY:
    try:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
    except ImportError:
        logger.warning("Groq not installed. Run: pip install groq")

# Track last API call time for throttling
_last_call_time = 0

# Track provider availability for this session
_provider_status = {
    "google": True,
    "groq": bool(_groq_client),
    "ollama": True,
    "openai": bool(_openai_client),
}


def _mark_provider_dead(provider: str, reason: str):
    _provider_status[provider] = False
    logger.warning(f"🚫 Provider {provider.upper()} disabled: {reason}")


def _call_groq(prompt: str) -> str:
    """Fallback: Call Groq's free Mixtral model (generous free tier)."""
    if not _groq_client:
        raise Exception("❌ Groq API key not configured. Get free key at: https://console.groq.com")
    last_error = None
    for model_name in [GROQ_MODEL] + [m for m in GROQ_FALLBACK_MODELS if m != GROQ_MODEL]:
        try:
            logger.info(f"🔄 Switching to Groq model: {model_name}")
            response = _groq_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=MAX_RESPONSE_TOKENS
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            logger.warning(f"⚠️  Groq model {model_name} failed: {str(e)[:120]}")
            continue
    _mark_provider_dead("groq", "all Groq models failed; check your API key or model access")
    logger.error(f"❌ Groq fallback failed after trying {len(GROQ_FALLBACK_MODELS)} models.")
    raise last_error


def _call_ollama(prompt: str) -> str:
    """Fallback: Call local Ollama (completely free, runs locally)."""
    try:
        logger.info(f"🔄 Switching to Ollama ({OLLAMA_MODEL}) fallback...")
        headers = {}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
                "max_tokens": MAX_RESPONSE_TOKENS,
            },
            headers=headers,
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["response"].strip()
        else:
            raise Exception(f"Ollama error: {response.text}")
    except requests.exceptions.ConnectionError:
        _mark_provider_dead("ollama", "local Ollama server not reachable")
        raise Exception(f"❌ Ollama not running. Start it: ollama serve (or ollama pull {OLLAMA_MODEL})")
    except Exception as e:
        logger.error(f"❌ Ollama fallback failed: {str(e)}")
        raise


def _call_openai(prompt: str) -> str:
    """Fallback: Call OpenAI's GPT-4o-mini."""
    if not _openai_client:
        raise Exception("❌ OpenAI API key not configured. Set OPENAI_API_KEY in .env")
    
    try:
        logger.info("🔄 Switching to OpenAI (GPT-4o-mini) fallback...")
        response = _openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        err_text = str(e).lower()
        if "quota" in err_text or "insufficient_quota" in err_text or "rate limit" in err_text or "429" in err_text:
            _mark_provider_dead("openai", err_text)
        elif "authentication" in err_text or "invalid_api_key" in err_text:
            _mark_provider_dead("openai", err_text)
        logger.error(f"❌ OpenAI fallback failed: {str(e)}")
        raise


def _try_fallbacks(prompt: str, priority: list) -> str:
    """Try fallback providers in priority order."""
    fallback_methods = {
        "groq": _call_groq,
        "ollama": _call_ollama,
        "openai": _call_openai,
    }
    for provider in priority:
        if provider not in fallback_methods:
            continue

        if not _provider_status.get(provider, False):
            logger.info(f"ℹ️  Skipping {provider.upper()} because it is disabled or unavailable.")
            continue

        if provider == "groq" and not _groq_client:
            logger.info("ℹ️  Skipping Groq fallback because GROQ_API_KEY is not configured.")
            continue
        if provider == "openai" and not _openai_client:
            logger.info("ℹ️  Skipping OpenAI fallback because OPENAI_API_KEY is not configured.")
            continue

        try:
            logger.info(f"✅ Trying fallback provider: {provider.upper()}")
            return fallback_methods[provider](prompt)
        except Exception as e:
            logger.warning(f"⚠️  {provider.upper()} failed: {str(e)[:100]}")
            continue
    
    raise Exception(
        "❌ All fallback providers failed. Please check your setup. "
        "Make sure Groq key is valid, Ollama is running, or OpenAI quota is available."
    )


def _call(model, prompt: str, max_retries: int = MAX_RETRIES) -> str:
    """Call model with exponential backoff retry logic for quota exhaustion."""
    global _last_call_time

    if not USE_GOOGLE_PRIMARY:
        logger.info("ℹ️ Skipping Google Gemini primary model in favor of free fallbacks.")
        return _try_fallbacks(prompt, FALLBACK_PRIORITY)

    if not _provider_status.get("google", True):
        logger.info("ℹ️ Skipping Google Gemini because it has been disabled for this session.")
        return _try_fallbacks(prompt, FALLBACK_PRIORITY)
    
    # Throttle consecutive API calls
    elapsed = time.time() - _last_call_time
    if elapsed < BATCH_DELAY:
        time.sleep(BATCH_DELAY - elapsed)
    
    retry_delay = INITIAL_RETRY_DELAY
    
    for attempt in range(max_retries):
        if attempt == 0:
            logger.info("✅ Using Google Gemini primary model")
        try:
            _last_call_time = time.time()
            return model.generate_content(prompt).text.strip()
        except ResourceExhausted as e:
            if attempt == max_retries - 1:
                logger.warning(f"⚠️  Google quota exhausted after {max_retries} retries")
                
                # Try fallback chain if enabled
                _mark_provider_dead("google", "quota exhausted")
                if USE_FALLBACK:
                    return _try_fallbacks(prompt, FALLBACK_PRIORITY)
                else:
                    raise
            
            # Extract retry delay from error if available
            error_msg = str(e)
            if "retry in" in error_msg.lower():
                try:
                    retry_seconds = float(error_msg.split("retry in")[1].split("s")[0].strip())
                    retry_delay = max(retry_seconds + 2, retry_delay)
                except:
                    pass
            
            logger.warning(f"⏳ Rate limited (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
        except Exception as e:
            err_text = str(e).lower()
            if "quota" in err_text or "rate limit" in err_text or "429" in err_text:
                _mark_provider_dead("google", err_text)
            logger.error(f"❌ Unexpected error: {str(e)}")
            if USE_FALLBACK:
                logger.info("Attempting fallback...")
                return _try_fallbacks(prompt, FALLBACK_PRIORITY)
            raise
    
    raise Exception("Failed after all retries")


def fallback_generate(prompt: str) -> str:
    """Generate text using the current fallback providers (Groq/Ollama)."""
    return _call(_pro, prompt)


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
    from rag.query_expander import LegalQueryExpander
    from rag.jurisdiction_manager import JurisdictionManager

    logger.info("🔍 MULTI-QUERY: Generating query variants with legal expansion")

    # Basic multi-query
    prompt = MULTIQUERY_PROMPT.format(
        law_category=state["law_category"],
        question=state["question"]
    )
    result = _call(_flash, prompt)
    variants = [q.strip() for q in result.split("\n") if q.strip()][:3]
    if not variants:
        variants = [state["question"]]

    # Enhanced query expansion
    expander = LegalQueryExpander()
    expanded_queries = expander.expand_query(state["question"], state["law_category"])
    variants.extend(expanded_queries)

    # Jurisdiction enhancement
    jm = JurisdictionManager()
    jurisdiction = jm.detect_jurisdiction(state["question"])
    jurisdiction_enhanced = jm.enhance_query_with_jurisdiction(state["question"], jurisdiction)

    variants.append(jurisdiction_enhanced)

    # Remove duplicates and limit
    seen = set()
    unique_variants = []
    for v in variants:
        if v not in seen and len(v) > 10:
            seen.add(v)
            unique_variants.append(v)

    variants = unique_variants[:6]  # Limit to 6 total

    logger.info(f"   Generated {len(variants)} enhanced query variants:")
    for i, variant in enumerate(variants, 1):
        logger.info(f"   {i}. {variant[:80]}...")
    return {"query_variants": variants}


# --- Node: Retrieve ---

def retrieve(state: RAGState) -> dict:
    from ingestion.ingest import get_retriever_for_case, get_global_retriever
    from rag.hyde_retriever import HydeRetriever
    from rag.embeddings import LocalEmbeddings

    case_id = state.get("case_id")
    logger.info(f"📚 RETRIEVE: Fetching documents using Raptor + Hyde")

    retriever = get_retriever_for_case(case_id) if case_id else get_global_retriever()
    hyde = HydeRetriever()
    embeddings = LocalEmbeddings(dim=256)

    seen_ids = set()
    all_docs = []

    # 1. Standard multi-query retrieval with Raptor
    for query in state["query_variants"]:
        try:
            docs = retriever.invoke(query)
            logger.info(f"   Multi-query: '{query}' → Found {len(docs)} documents")
            for doc in docs:
                doc_id = doc.metadata.get("doc_id", doc.page_content[:50])
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_docs.append(doc)
        except Exception as e:
            logger.warning(f"   Error retrieving for query '{query}': {e}")

    # 2. Hyde-based retrieval
    try:
        original_query = state["question"]
        hyde_embedding = hyde.get_hypothetical_embedding(original_query, embeddings)
        logger.info("   Hyde: Generated hypothetical answer for enhanced retrieval")

        # Find documents similar to the hypothetical answer
        # Since RaptorRetriever uses invoke, we need to create a dummy query or modify approach
        # For now, we'll use the hypothetical answer as a query
        hypothetical_answer = hyde.generate_hypothetical_answer(original_query)
        hyde_docs = retriever.invoke(hypothetical_answer[:500])  # Limit length
        logger.info(f"   Hyde retrieval: Found {len(hyde_docs)} additional documents")

        for doc in hyde_docs:
            doc_id = doc.metadata.get("doc_id", doc.page_content[:50])
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                all_docs.append(doc)
                logger.info(f"   ✓ Added Hyde document: {doc_id}")
    except Exception as e:
        logger.warning(f"   Hyde retrieval failed: {e}")

    logger.info(f"   ✓ Total unique documents retrieved: {len(all_docs)} (Raptor + Hyde)")
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
    from rag.confidence_scorer import ConfidenceScorer
    from rag.multi_modal import MultiModalRetriever

    logger.info("✍️  GENERATE: Creating enhanced response from graded documents")

    # Build context from graded docs + web results
    context_parts = []

    # Separate text and image documents
    text_docs = []
    image_docs = []

    for doc in state["graded_documents"]:
        content = doc.page_content
        if doc.metadata.get("type") == "image":
            image_docs.append(doc)
        else:
            text_docs.append(doc)

        # Skip raw base64 image data for context
        if len(content) > 500 and not all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in content[:100]):
            context_parts.append(content)
        elif len(content) <= 500:
            context_parts.append(content)

    for web_result in state.get("web_results", []):
        context_parts.append(f"[Web] {web_result}")

    # Enhance with multi-modal analysis
    mm_retriever = MultiModalRetriever()
    enhanced_docs = mm_retriever.enhance_text_with_images(text_docs, image_docs, state["question"])

    # Add enhanced content to context
    for doc in enhanced_docs:
        if doc.metadata.get("enhanced"):
            context_parts.append(f"[Enhanced] {doc.page_content}")

    context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant documents found."

    logger.info(f"   Context sources: {len(state['graded_documents'])} docs + {len(state.get('web_results', []))} web results")
    logger.info(f"   Enhanced with {len([d for d in enhanced_docs if d.metadata.get('enhanced')])} multi-modal analyses")
    logger.info(f"   Context length: {len(context)} characters")

    prompt = GENERATE_PROMPT.format(
        law_category=state["law_category"],
        context=context,
        question=state["question"]
    )
    generation = _call(_pro, prompt)

    # Score confidence
    scorer = ConfidenceScorer()
    confidence = scorer.score_confidence(state["question"], generation, context)

    logger.info(f"   ✓ Response generated (confidence: {confidence}/10): {generation[:100]}...")
    return {"generation": generation, "confidence_score": confidence}


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


