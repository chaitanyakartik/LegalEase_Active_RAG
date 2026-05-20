from config import GEMINI_API_KEY, PRO_MODEL
from prompts.templates import ANALYSIS_PROMPT
from rag.graph import run_rag
from db.models import get_case, get_documents
from rag.citation_analyzer import CitationNetworkAnalyzer
from rag.counterfactual_analyzer import CounterfactualAnalyzer
from rag.research_report_generator import LegalResearchReportGenerator


def analyze_case(case_id: str, question: str, law_category: str) -> tuple[str, int]:
    """
    Run AI legal analysis on a case.
    Uses the Active RAG pipeline to retrieve relevant context from uploaded docs,
    then generates a structured legal analysis.
    Returns (response, confidence_score)
    """
    case = get_case(case_id)
    case_description = case.get("description", "") if case else ""

    # Augment the question with case context for better analysis
    full_question = question
    if case_description:
        full_question = f"Case Background: {case_description}\n\nAnalysis Request: {question}"

    return run_rag(full_question, law_category, case_id)


def analyze_citation_network(case_id: str) -> str:
    """
    Analyze citation relationships in case documents.
    Returns a comprehensive citation network analysis report.
    """
    documents = get_documents(case_id)
    if not documents:
        return "No documents available for citation analysis."

    analyzer = CitationNetworkAnalyzer()
    return analyzer.generate_citation_report(documents, case_id)


def analyze_counterfactual_scenarios(case_id: str, jurisdiction: str) -> str:
    """
    Analyze counterfactual legal scenarios for a case.
    Returns a comprehensive counterfactual analysis report.
    """
    case = get_case(case_id)
    if not case:
        return "Case not found."

    analyzer = CounterfactualAnalyzer()
    return analyzer.generate_counterfactual_report(case, jurisdiction)


def generate_research_memo(case_id: str, research_query: str, jurisdiction: str) -> str:
    """
    Generate a comprehensive legal research memorandum.
    """
    case = get_case(case_id)
    if not case:
        return "Case not found."

    documents = get_documents(case_id)
    # For precedents, we'll use a simple search - could be enhanced
    precedents = []  # TODO: Implement precedent search

    generator = LegalResearchReportGenerator()
    return generator.generate_research_memo(case, research_query, jurisdiction, documents, precedents)


def generate_case_brief(case_id: str, jurisdiction: str) -> str:
    """
    Generate a professional case brief.
    """
    case = get_case(case_id)
    if not case:
        return "Case not found."

    documents = get_documents(case_id)

    generator = LegalResearchReportGenerator()
    return generator.generate_case_brief(case, jurisdiction, documents)
