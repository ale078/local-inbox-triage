import os
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from services import pdf_service, gmail_service, parser_service, gemini_service

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
LATEST_MATCHES_FILE = DATA_DIR / "latest_matches.json"

app = FastAPI(title="Ofertas vs CV")

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ProcessRequest(BaseModel):
    label: str
    count: int = 3
    email_user: str | None = None  # Optional override if not in env


@app.get("/")
async def get_index():
    """Serve the single page application."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html no encontrado.")
    return FileResponse(str(index_file))


@app.get("/api/cv/status")
async def get_cv_status():
    """Return status and metadata of the uploaded CV."""
    return pdf_service.get_cv_info()


@app.post("/api/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    """Upload and save a CV in PDF format."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se admiten archivos en formato .pdf")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="El archivo subido está vacío.")

    try:
        pdf_service.save_cv_pdf(contents)
        info = pdf_service.get_cv_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar o procesar el CV: {str(e)}")


@app.get("/api/jobs/latest")
async def get_latest_matches():
    """Return the cached latest matches if available."""
    if LATEST_MATCHES_FILE.exists():
        try:
            with open(LATEST_MATCHES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception:
            return {"jobs": []}
    return {"jobs": []}


@app.post("/api/jobs/process")
async def process_jobs(req: ProcessRequest):
    """
    Fetch emails for the given label via IMAP and extract job offers.
    In Slice 2: extracts and returns all jobs with links.
    In Slice 3: Gemini evaluates match against CV.
    """
    if not pdf_service.cv_exists():
        raise HTTPException(status_code=400, detail="Debes subir tu CV antes de procesar las ofertas.")

    # Allow setting email_user from request if provided and not yet in environment
    if req.email_user and not os.environ.get("GMAIL_USER"):
        os.environ["GMAIL_USER"] = req.email_user

    try:
        # 1. Fetch emails via IMAP
        emails = gmail_service.fetch_emails_by_label(label=req.label, limit=req.count)
        if not emails:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron correos en la etiqueta '{req.label}'."
            )

        # 2. Extract job offers from email HTML digests
        jobs = parser_service.parse_emails_to_jobs(emails)
        if not jobs:
            raise HTTPException(
                status_code=404,
                detail=f"Se leyeron {len(emails)} correo(s), pero no se identificaron ofertas de empleo en el formato del mensaje."
            )

        # 3. Read CV text and evaluate with Gemini
        cv_text = pdf_service.extract_cv_text()
        jobs = gemini_service.evaluate_matches(cv_text=cv_text, jobs=jobs)

        # Save to latest_matches.json
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(LATEST_MATCHES_FILE, "w", encoding="utf-8") as f:
            json.dump({"jobs": jobs}, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "emails_read": len(emails),
            "jobs_found": len(jobs),
            "jobs": jobs
        }

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except ConnectionError as ce:
        raise HTTPException(status_code=502, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
