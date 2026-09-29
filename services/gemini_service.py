import os
import json
from typing import List, Dict, Any
from google import genai
from google.genai import types


# Schema de salida estructurada para cada oferta evaluada
MATCH_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "match_percentage": {
            "type": "INTEGER",
            "description": "Porcentaje de afinidad entre el CV y la oferta, de 0 a 100."
        },
        "verdict": {
            "type": "STRING",
            "description": "Veredicto: exactamente uno de 'Sí', 'No', o 'Puede ser'."
        },
        "suggestion": {
            "type": "STRING",
            "description": "Una sola oración explicando el veredicto: qué encaja y qué no."
        }
    },
    "required": ["match_percentage", "verdict", "suggestion"]
}


def _get_client() -> genai.Client:
    """Create a Gemini client using available API key from env."""
    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("gemini_key_2.5")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not api_key:
        raise ValueError(
            "No se encontró la API Key de Gemini. "
            "Definí GEMINI_API_KEY en tus variables de entorno o en el archivo .env."
        )
    return genai.Client(api_key=api_key)


def _build_prompt(cv_text: str, job: Dict[str, Any]) -> str:
    """Build evaluation prompt for a single job offer."""
    title = job.get("title", "Sin título")
    context = job.get("company_or_context") or job.get("snippet") or ""
    return (
        f"Sos un asistente de búsqueda de empleo. "
        f"Analizá la afinidad entre este CV y esta oferta de trabajo.\n\n"
        f"=== CV DEL CANDIDATO ===\n{cv_text[:6000]}\n\n"
        f"=== OFERTA DE TRABAJO ===\n"
        f"Título: {title}\n"
        f"Contexto: {context}\n\n"
        f"Evaluá la afinidad y devolvé:\n"
        f"- match_percentage: número entero entre 0 y 100\n"
        f"- verdict: exactamente 'Sí' (>=75%), 'Puede ser' (50-74%), o 'No' (<50%)\n"
        f"- suggestion: una sola oración concisa explicando qué encaja y qué no encaja"
    )


def evaluate_matches(cv_text: str, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Evaluate each job offer against the CV using Gemini.
    Returns the jobs list enriched with match_percentage, verdict, suggestion.
    """
    if not cv_text or not jobs:
        return jobs

    client = _get_client()
    enriched = []

    for job in jobs:
        try:
            prompt = _build_prompt(cv_text, job)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=MATCH_SCHEMA,
                    temperature=0.2,
                ),
            )
            result = json.loads(response.text)
            job["match_percentage"] = max(0, min(100, int(result.get("match_percentage", 0))))
            job["verdict"] = result.get("verdict", "No")
            job["suggestion"] = result.get("suggestion", "")
        except Exception as e:
            # On failure, mark with neutral values so the rest still show
            job.setdefault("match_percentage", 0)
            job.setdefault("verdict", "Error")
            job.setdefault("suggestion", f"No se pudo evaluar esta oferta: {str(e)[:80]}")

        enriched.append(job)

    # Sort by match_percentage descending
    enriched.sort(key=lambda j: j.get("match_percentage", 0), reverse=True)
    return enriched
