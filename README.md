# Ofertas vs CV

App local para filtrar ofertas de Gmail por afinidad con tu CV usando Python, FastAPI y Gemini.

## Qué hace

- Sube tu CV en PDF.
- Elegís una etiqueta de Gmail (por ejemplo: `Glassdoor` o `LinkedIn`).
- Lee los últimos mails de esa etiqueta vía IMAP.
- Extrae ofertas y links desde el HTML del digest.
- Evalúa cada oferta con Gemini frente al texto del CV.
- Muestra una lista ordenada con porcentaje, veredicto y enlace directo.

## Requisitos

- Python 3.10+
- Dependencias del proyecto en `requirements.txt`
- Variables de entorno:
  - `GMAIL_USER`
  - `GMAIL_APP_PASSWORD`
  - `GEMINI_API_KEY`

## Cómo correr

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Luego abrir en el navegador:

```text
http://localhost:8000
```

## Nota

La app corre localmente y usa Gmail y Gemini con tus credenciales del entorno. Si la API de Gemini alcanza cuota, la app sigue funcionando y muestra un aviso claro sin romper el flujo completo.
