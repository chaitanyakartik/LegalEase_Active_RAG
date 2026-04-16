import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import GEMINI_API_KEY, FLASH_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel(FLASH_MODEL)


def _summarize_text(text: str) -> str:
    prompt = f"Summarize the following text concisely in 2-3 sentences:\n\n{text}"
    try:
        return _model.generate_content(prompt).text.strip()
    except Exception:
        return text[:300]


def _describe_image(b64_image: str) -> str:
    prompt = "Describe this image in detail. Be specific about any graphs, tables, charts, or legal diagrams."
    try:
        import PIL.Image
        import io
        import base64
        img_bytes = base64.b64decode(b64_image)
        img = PIL.Image.open(io.BytesIO(img_bytes))
        return _model.generate_content([prompt, img]).text.strip()
    except Exception:
        return "Image content (could not describe)"


def chunk_and_summarize(text: str, images: list[str]) -> dict:
    """
    Split text into chunks and generate summaries for both text chunks and images.

    Returns:
        {
            "text_chunks": [original chunk strings],
            "text_summaries": [summary for each chunk],
            "image_b64s": [original base64 image strings],
            "image_descriptions": [description for each image],
        }
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    text_chunks = splitter.split_text(text) if text.strip() else []

    text_summaries = [_summarize_text(chunk) for chunk in text_chunks]
    image_descriptions = [_describe_image(b64) for b64 in images]

    return {
        "text_chunks": text_chunks,
        "text_summaries": text_summaries,
        "image_b64s": images,
        "image_descriptions": image_descriptions,
    }
