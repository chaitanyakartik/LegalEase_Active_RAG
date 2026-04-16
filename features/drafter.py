import google.generativeai as genai
from config import GEMINI_API_KEY, PRO_MODEL
from prompts.templates import DRAFT_PROMPT
from rag.graph import run_rag
from db.models import get_case, save_draft

genai.configure(api_key=GEMINI_API_KEY)
_pro = genai.GenerativeModel(PRO_MODEL)


def generate_draft(case_id: str, draft_type: str, law_category: str,
                   instructions: str = "") -> tuple[str, str]:
    """
    Generate a legal document draft using case context from RAG.
    Returns (draft_content, draft_id).
    """
    case = get_case(case_id)
    case_description = case.get("description", "") if case else ""

    # Use RAG to pull relevant context from uploaded documents
    query = f"Provide relevant facts, clauses, and legal details for drafting a {draft_type}"
    context = run_rag(query, law_category, case_id)

    # Build the final draft prompt
    full_context = ""
    if case_description:
        full_context += f"Case Background:\n{case_description}\n\n"
    full_context += f"Retrieved Legal Context:\n{context}"
    if instructions:
        full_context += f"\n\nAdditional Instructions:\n{instructions}"

    prompt = DRAFT_PROMPT.format(
        law_category=law_category,
        draft_type=draft_type,
        context=full_context,
        instructions=instructions or "None"
    )
    draft_content = _pro.generate_content(prompt).text.strip()

    title = f"{draft_type} - {case.get('title', 'Case') if case else 'Case'}"
    draft_id = save_draft(case_id, draft_type, title, draft_content)

    return draft_content, draft_id
