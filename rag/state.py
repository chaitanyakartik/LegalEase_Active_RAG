from typing import Optional
from typing_extensions import TypedDict
from langchain_core.documents import Document


class RAGState(TypedDict):
    question: str
    law_category: str
    case_id: Optional[str]
    query_variants: list[str]
    documents: list[Document]
    graded_documents: list[Document]
    web_results: list[str]
    generation: str
    is_relevant: bool
    is_grounded: bool
    retry_count: int
