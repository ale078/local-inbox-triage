from pathlib import Path
from pypdf import PdfReader

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CV_PATH = DATA_DIR / "cv.pdf"


def ensure_data_dir() -> Path:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def cv_exists() -> bool:
    """Check if a CV PDF has already been saved."""
    return CV_PATH.exists() and CV_PATH.stat().st_size > 0


def save_cv_pdf(file_bytes: bytes) -> Path:
    """Save raw PDF bytes to data/cv.pdf."""
    ensure_data_dir()
    with open(CV_PATH, "wb") as f:
        f.write(file_bytes)
    return CV_PATH


def extract_cv_text() -> str:
    """Extract and return text from the saved data/cv.pdf."""
    if not cv_exists():
        raise FileNotFoundError("No se encontró el archivo data/cv.pdf.")

    reader = PdfReader(str(CV_PATH))
    extracted_pages = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            extracted_pages.append(text.strip())

    full_text = "\n\n".join(extracted_pages)
    return full_text


def get_cv_info() -> dict:
    """Return status and basic metadata of the uploaded CV."""
    if not cv_exists():
        return {"exists": False}

    try:
        reader = PdfReader(str(CV_PATH))
        num_pages = len(reader.pages)
        size_kb = round(CV_PATH.stat().st_size / 1024, 1)
        text_preview = ""
        if num_pages > 0:
            first_page_text = reader.pages[0].extract_text() or ""
            text_preview = first_page_text.strip()[:200]

        return {
            "exists": True,
            "filename": "cv.pdf",
            "pages": num_pages,
            "size_kb": size_kb,
            "preview": text_preview
        }
    except Exception as e:
        return {
            "exists": True,
            "filename": "cv.pdf",
            "error": str(e)
        }
