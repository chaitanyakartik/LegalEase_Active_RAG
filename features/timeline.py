import google.generativeai as genai
from config import GEMINI_API_KEY, FLASH_MODEL
from prompts.templates import TIMELINE_PROMPT
from db.models import add_timeline_event, get_timeline, get_case

genai.configure(api_key=GEMINI_API_KEY)
_flash = genai.GenerativeModel(FLASH_MODEL)


def suggest_timeline_events(case_id: str, law_category: str) -> list[dict]:
    """
    Use Gemini to suggest timeline events based on the case description.
    Returns a list of suggested event dicts (not yet saved).
    """
    case = get_case(case_id)
    if not case:
        return []

    case_description = case.get("description", "No description provided.")
    prompt = TIMELINE_PROMPT.format(
        case_description=case_description,
        law_category=law_category
    )

    response = _flash.generate_content(prompt).text.strip()
    suggestions = []
    for line in response.split("\n"):
        line = line.strip()
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                suggestions.append({
                    "event_type": parts[0],
                    "title": parts[1],
                    "description": parts[2],
                    "timeframe": parts[3],
                })
    return suggestions


def add_suggested_event(case_id: str, suggestion: dict) -> str:
    """Save a suggested event to the database."""
    return add_timeline_event(
        case_id=case_id,
        title=suggestion["title"],
        event_type=suggestion.get("event_type", "Note"),
        description=suggestion.get("description", ""),
        event_date=None
    )


def get_case_timeline(case_id: str) -> list[dict]:
    return get_timeline(case_id)
