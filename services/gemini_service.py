import os
import json
import time
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


def _resolve_key_value(val: str | None) -> str | None:
    """Resolve API key, including cases where env var contains the name of another env var."""
    if not val:
        return None
    val = val.strip()
    if val in os.environ and os.environ[val] != val:
        return os.environ[val].strip()
    return val


def _get_client_and_model() -> tuple[genai.Client, str]:
    """
    Get client and model.
    Prioritizes gemini_key_3.5 (with gemini-3.8-flash).
    If gemini_key_3.5 has depleted credits or errors, falls back to gemini_key_2.5 (gemini-2.5-flash).
    """
    key_35 = _resolve_key_value(os.environ.get("gemini_key_3.5"))
    key_25 = (
        _resolve_key_value(os.environ.get("gemini_key_2.5"))
        or _resolve_key_value(os.environ.get("GEMINI_API_KEY"))
        or _resolve_key_value(os.environ.get("GOOGLE_API_KEY"))
    )

    # 1. Try gemini_key_3.5 first if present
    if key_35 and key_35 != key_25:
        try:
            client_35 = genai.Client(api_key=key_35)
            # Lightweight probe to check if billing/credits allow inference
            client_35.models.generate_content(model="gemini-3.8-flash", contents="ping")
            return client_35, "gemini-3.8-flash"
        except Exception:
            # If 3.5 is depleted or fails, fall through to 2.5
            pass

    # 2. Use gemini_key_2.5 (or GEMINI_API_KEY/GOOGLE_API_KEY)
    if key_25:
        return genai.Client(api_key=key_25), "gemini-2.5-flash"

    # If only 3.5 was configured but failed
    if key_35:
        return genai.Client(api_key=key_35), "gemini-3.8-flash"

    raise ValueError(
        "No se encontró una API Key válida de Gemini. "
        "Definí gemini_key_2.5, gemini_key_3.5 o GEMINI_API_KEY en tus variables de entorno."
    )


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


def _generate_with_retry(client: genai.Client, model: str, prompt: str, max_retries: int = 3):
    """Retry transient quota/rate-limit errors without failing the whole batch."""
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=MATCH_SCHEMA,
                    temperature=0.2,
                ),
            )
        except Exception as exc:
            last_error = exc
            message = str(exc).upper()
            is_rate_limited = "429" in message or "RESOURCE_EXHAUSTED" in message or "RATE_LIMIT" in message
            if is_rate_limited and attempt < max_retries:
                time.sleep(2 ** (attempt - 1))
                continue
            raise

    raise last_error


def evaluate_matches(cv_text: str, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Evaluate each job offer against the CV using Gemini.
    Returns the jobs list enriched with match_percentage, verdict, suggestion.
    """
    if not cv_text or not jobs:
        return jobs

    client, model = _get_client_and_model()
    enriched = []

    # If the API is rate-limited, reduce the batch to the jobs that are most likely useful.
    # This keeps the app responsive and avoids failing the whole request on one quota issue.
    working_jobs = jobs[:]
    if len(working_jobs) > 8:
        working_jobs = working_jobs[:8]

    for job in working_jobs:
        try:
            prompt = _build_prompt(cv_text, job)
            response = _generate_with_retry(client, model, prompt, max_retries=3)
            result = json.loads(response.text)
            job["match_percentage"] = max(0, min(100, int(result.get("match_percentage", 0))))
            job["verdict"] = result.get("verdict", "No")
            job["suggestion"] = result.get("suggestion", "")
        except Exception as e:
            # On failure, mark with neutral values so the rest still show
            job.setdefault("match_percentage", 0)
            job.setdefault("verdict", "No")
            if "429" in str(e).upper() or "RESOURCE_EXHAUSTED" in str(e).upper():
                job.setdefault("suggestion", "La evaluación de esta oferta se reintentó y quedó fuera por límite de cuota de la API; revisá más tarde o probá con menos ofertas.")
            else:
                job.setdefault("suggestion", f"No se pudo evaluar esta oferta: {str(e)[:80]}")

        enriched.append(job)

    # Sort by match_percentage descending
    enriched.sort(key=lambda j: j.get("match_percentage", 0), reverse=True)
    return enriched
