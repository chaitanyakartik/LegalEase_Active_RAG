from rag.graph import run_rag


def search_precedents(case_description: str, law_category: str, case_id: str = None) -> str:
    """
    Search for relevant legal precedents and similar cases.
    Uses the Active RAG pipeline — retrieves from uploaded docs first,
    falls back to web search if local docs aren't sufficient.
    """
    query = f"Find legal precedents, similar court judgments, and relevant case law for: {case_description}"
    return run_rag(query, law_category, case_id)
