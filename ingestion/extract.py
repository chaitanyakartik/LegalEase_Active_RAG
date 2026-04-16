import base64
import pdfplumber
import fitz  # PyMuPDF
from docx import Document


def extract_from_pdf(file_path: str) -> dict:
    """Extract text and base64-encoded images from a PDF file."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    images = []
    doc = fitz.open(file_path)
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            images.append(b64)
    doc.close()

    return {"text": text, "images": images}


def extract_from_docx(file_path: str) -> dict:
    """Extract text from a DOCX file (no image extraction for simplicity)."""
    doc = Document(file_path)
    text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    return {"text": text, "images": []}


def extract_from_txt(file_path: str) -> dict:
    """Extract text from a TXT file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return {"text": text, "images": []}


def extract(file_path: str) -> dict:
    """Route to correct extractor based on file extension."""
    lower = file_path.lower()
    if lower.endswith(".pdf"):
        return extract_from_pdf(file_path)
    elif lower.endswith(".docx"):
        return extract_from_docx(file_path)
    elif lower.endswith(".txt"):
        return extract_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
