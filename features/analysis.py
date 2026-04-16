import google.generativeai as genai
from config import GEMINI_API_KEY, PRO_MODEL
from prompts.templates import ANALYSIS_PROMPT
from rag.graph import run_rag
from db.models import get_case

genai.configure(api_key=GEMINI_API_KEY)
_pro = genai.GenerativeModel(PRO_MODEL)


def analyze_case(case_id: str, question: str, law_category: str) -> str:
    """
    Run AI legal analysis on a case.
    Uses the Active RAG pipeline to retrieve relevant context from uploaded docs,
    then generates a structured legal analysis.
    """
    case = get_case(case_id)
    case_description = case.get("description", "") if case else ""

    # Augment the question with case context for better analysis
    full_question = question
    if case_description:
        full_question = f"Case Background: {case_description}\n\nAnalysis Request: {question}"

    return run_rag(full_question, law_category, case_id)
