from langgraph.graph import StateGraph, END
from rag.state import RAGState
from rag.nodes import (
    question_router, llm_direct, multi_query, retrieve,
    grade_documents, web_search, generate, hallucination_check
)

MAX_RETRIES = 2


def _route_question(state: RAGState) -> str:
    return state.get("_route", "legal")


def _route_after_grading(state: RAGState) -> str:
    return "generate" if state["is_relevant"] else "web_search"


def _route_after_hallucination(state: RAGState) -> str:
    if state["is_grounded"]:
        return END
    if state.get("retry_count", 0) >= MAX_RETRIES:
        return END  # Give up after max retries
    return "web_search"


def build_graph() -> StateGraph:
    graph = StateGraph(RAGState)

    graph.add_node("question_router", question_router)
    graph.add_node("llm_direct", llm_direct)
    graph.add_node("multi_query", multi_query)
    graph.add_node("retrieve", retrieve)
    graph.add_node("grade_documents", grade_documents)
    graph.add_node("web_search", web_search)
    graph.add_node("generate", generate)
    graph.add_node("hallucination_check", hallucination_check)

    graph.set_entry_point("question_router")

    graph.add_conditional_edges(
        "question_router",
        _route_question,
        {"general": "llm_direct", "legal": "multi_query"}
    )

    graph.add_edge("llm_direct", END)
    graph.add_edge("multi_query", "retrieve")
    graph.add_edge("retrieve", "grade_documents")

    graph.add_conditional_edges(
        "grade_documents",
        _route_after_grading,
        {"generate": "generate", "web_search": "web_search"}
    )

    graph.add_edge("web_search", "generate")
    graph.add_edge("generate", "hallucination_check")

    graph.add_conditional_edges(
        "hallucination_check",
        _route_after_hallucination,
        {END: END, "web_search": "web_search"}
    )

    return graph.compile()


# Compiled graph — import and use this
rag_graph = build_graph()


def run_rag(question: str, law_category: str, case_id: str = None) -> str:
    """Run the Active RAG pipeline and return the generated answer."""
    initial_state: RAGState = {
        "question": question,
        "law_category": law_category,
        "case_id": case_id,
        "query_variants": [],
        "documents": [],
        "graded_documents": [],
        "web_results": [],
        "generation": "",
        "is_relevant": False,
        "is_grounded": False,
        "retry_count": 0,
    }
    result = rag_graph.invoke(initial_state)
    return result.get("generation", "I was unable to generate a response.")
