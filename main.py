import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from services import pdf_service

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
    Process emails for the given label and evaluate matches.
    Will be fully integrated in Slices 2 & 3.
    """
    if not pdf_service.cv_exists():
        raise HTTPException(status_code=400, detail="Debes subir tu CV antes de procesar las ofertas.")

    return {
        "status": "ready_for_slices_2_and_3",
        "message": f"Etiqueta '{req.label}' recibida para {req.count} correos.",
        "jobs": []
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
