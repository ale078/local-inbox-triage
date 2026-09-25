---
doc: spec
status: approved
---

# Ofertas vs CV — Technical Spec

## How This Works, In Plain Language

La aplicación corre como un servidor local en Python utilizando FastAPI y sirve una interfaz web clara y liviana que abrís en tu navegador (`http://localhost:8000`).

1. **Gestión de CV:** La primera vez que abrís la app, te solicita subir tu CV en PDF y lo guarda en la carpeta local `data/cv.pdf`. Si el archivo ya existe en esa carpeta, la app lo detecta automáticamente y no te lo vuelve a pedir (aunque te da la opción de reemplazarlo si querés).
2. **Consulta a Gmail:** Ingresás el nombre de tu etiqueta de Gmail (ej. `LinkedIn` o `Glassdoor`) y seleccionás cuántos correos recientes procesar (por ejemplo, los últimos 3 digests).
3. **Lectura local vía IMAP:** La app se conecta directamente a los servidores de Gmail mediante el protocolo estándar IMAP usando las variables de entorno de tu sistema, busca los correos con esa etiqueta y descarga el contenido HTML.
4. **Extracción de ofertas:** Con BeautifulSoup, la app analiza el código HTML de cada digest para desarmar la lista y extraer cada puesto de trabajo: título, empresa/contexto y su enlace directo a la oferta.
5. **Evaluación con IA (Gemini):** El servidor lee el texto completo del CV (usando `pypdf`) y envía cada oferta extraída a la API de Gemini. Gemini evalúa la afinidad y devuelve un resultado estructurado:
   - Porcentaje de match (0 al 100%).
   - Veredicto (`Sí`, `No`, `Puede ser`).
   - Sugerencia de una línea (por ejemplo: "Cumple con experiencia en Python y APIs, pero pide 3 años de AWS").
6. **Visualización y persistencia:** Las ofertas evaluadas se guardan en un archivo local `data/latest_matches.json` y se muestran en pantalla ordenadas de mayor a menor porcentaje, con tarjetas legibles y botones directos para abrir las ofertas relevantes en una pestaña nueva.

## The Core Journey Through the System

Implements `prd.md > The Core Journey`.

1. **Apertura de la app:**
   - El usuario abre `http://localhost:8000`.
   - El frontend llama a `GET /api/cv/status`. Si `data/cv.pdf` existe, la interfaz muestra "CV cargado" y activa el formulario de búsqueda de Gmail. Si no, muestra el formulario de carga de PDF.
2. **Carga de CV (si aplica):**
   - El usuario selecciona o arrastra su PDF.
   - `POST /api/cv/upload` guarda el archivo en `data/cv.pdf` y extrae su texto usando `pypdf` para dejarlo listo en memoria.
3. **Disparo de la lectura de correos:**
   - El usuario escribe la etiqueta (ej. `LinkedIn`) y selecciona la cantidad $N$ de correos (ej. 3).
   - Hace clic en "Buscar y Evaluar Ofertas".
   - `POST /api/jobs/process` inicia la secuencia de búsqueda:
     1. Conexión a `imap.gmail.com` con `IMAP_USER` e `IMAP_PASSWORD` de las variables de sistema.
     2. Selección del buzón/etiqueta y recuperación de los $N$ UIDs más recientes.
     3. Descarga del cuerpo HTML de los mensajes.
     4. Parseo de ofertas y links con `BeautifulSoup`.
     5. Evaluación en batch o paralelo contra el CV vía Gemini API.
4. **Visualización de resultados:**
   - El frontend recibe la lista JSON, la guarda en cache/estado local y la renderiza en tarjetas claras:
     - Badge con % de match (verde para alto, amarillo para medio, gris para bajo).
     - Veredicto destacado.
     - Título del empleo y contexto/digest del que proviene.
     - Sugerencia concisa de 1 línea.
     - Botón "Abrir oferta" (`target="_blank"`).
5. **Decisión del usuario:**
   - El usuario abre únicamente las ofertas recomendadas sin haber tenido que leer los correos completos.

## Stack

- **Lenguaje:** Python 3.10+
- **Backend Framework:** FastAPI (`fastapi>=0.110.0`, `uvicorn>=0.28.0`)
  - *Razón y tradeoff:* Muy ligero, rápido de iniciar, sin configuración compleja. Permite servir la API y los archivos estáticos en un solo proceso local.
  - *Documentación:* [FastAPI Docs](https://fastapi.tiangolo.com/)
- **Lectura de Correo:** `imaplib` y `email` (librerías estándar de Python)
  - *Razón y tradeoff:* Cero dependencias externas para Gmail. Aprovecha la contraseña de aplicación ya configurada por el usuario en el sistema.
  - *Documentación:* [Python imaplib Docs](https://docs.python.org/3/library/imaplib.html)
- **Extracción de PDF:** `pypdf>=4.1.0`
  - *Razón y tradeoff:* Extracción de texto pura en Python sin requerir binarios externos como Poppler o Tesseract.
  - *Documentación:* [pypdf Docs](https://pypdf.readthedocs.io/)
- **Parseo de HTML:** `beautifulsoup4>=4.12.0`
  - *Razón y tradeoff:* El estándar de facto para navegar el árbol HTML de los correos digest y extraer selectivamente enlaces y textos de ofertas.
  - *Documentación:* [BeautifulSoup4 Docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- **Modelo de IA y SDK:** `google-genai` (Gemini 2.5 Flash / 1.5 Flash)
  - *Razón y tradeoff:* SDK oficial moderno de Google Gemini. Velocidad de respuesta excelente y soporte para salidas JSON estructuradas (`response_schema`).
  - *Documentación:* [Google GenAI SDK](https://github.com/googleapis/python-genai)
- **Frontend:** HTML5 semántico, CSS3 Vanilla (Light theme, diseño limpio con tarjetas y jerarquía clara), JavaScript moderno (Fetch API).
  - *Razón y tradeoff:* Sin Node.js ni bundlers; corre directamente desde el navegador y el servidor FastAPI.

## Where It Runs and How Someone Tries It

- **Entorno:** Proceso local en Windows.
- **Requisitos previos:**
  - Python 3.10+ instalado.
  - Variable de entorno `IMAP_USER` (tu correo) e `IMAP_PASSWORD` (tu contraseña de aplicación de Gmail) en el sistema.
  - Variable de entorno `GEMINI_API_KEY` en el sistema (o en archivo `.env` local).
- **Comando de inicio:**
  ```bash
  python -m uvicorn main:app --reload --port 8000
  ```
- **Cómo probarlo:**
  1. Abrir en el navegador `http://localhost:8000`.
  2. Si no hay CV cargado, subir un PDF.
  3. Ingresar la etiqueta de Gmail (ej. `LinkedIn`) y elegir la cantidad de correos (ej. 3).
  4. Presionar "Buscar y Evaluar Ofertas".
  5. Ver la lista de empleos con porcentaje de match, veredicto y links directos.

*Nota para Devpost:* La entrega del hackathon requiere un video demo corto (mostrando este flujo en pantalla) y el repositorio público de GitHub. El despliegue en la nube no es necesario para este POC local.

## Look and Feel

Implements `prd.md > Look and Feel` y `scope.md > Inspiration & Identity`.

- **Estilo:** Limpio, moderno, tipo aplicación de productividad ligera (Light Theme). Fondo blanco/gris claro (`#f8fafc`), tarjetas blancas con bordes sutiles y sombra suave.
- **Tipografía:** Sistema de fuentes sans-serif moderno y legible (Inter / system-ui).
- **Jerarquía visual:**
  - El porcentaje de match y el veredicto son los elementos visuales más destacados de cada tarjeta.
  - Badges con código de color: Verde (`>= 75%`, "Sí"), Ámbar (`50% - 74%`, "Puede ser"), Gris (`< 50%`, "No").
  - Botón de enlace claro y accesible para ir a la postulación.
- **Estado de carga:** Indicador de progreso mientras lee IMAP y procesa el análisis con Gemini para dar feedback inmediato al usuario.

## Components

### 1. Servidor Principal (`main.py`)
Expone la API REST local y sirve la interfaz estática.
- Rutas:
  - `GET /`: Devuelve `index.html`.
  - `GET /api/cv/status`: Informa si ya existe un CV en disco (`data/cv.pdf`).
  - `POST /api/cv/upload`: Recibe y guarda el PDF del CV.
  - `POST /api/jobs/process`: Orquesta la lectura de Gmail, extracción de ofertas y match con Gemini.
- PRD ref: `prd.md > Features and Behavior`.

### 2. Servicio de CV (`services/pdf_service.py`)
Maneja la persistencia y lectura del archivo PDF.
- Funciones:
  - `save_cv_pdf(file_bytes) -> str`: Guarda el archivo en `data/cv.pdf`.
  - `extract_cv_text() -> str`: Extrae el texto del PDF usando `pypdf`.
- PRD ref: `prd.md > Cargar el CV`.

### 3. Servicio de Gmail IMAP (`services/gmail_service.py`)
Conecta con Gmail mediante IMAP usando SSL (`imap.gmail.com:993`).
- Funciones:
  - `fetch_digest_emails(label: str, limit: int = 3) -> list[dict]`: Busca los últimos correos bajo la etiqueta indicada y extrae el asunto, fecha y cuerpo HTML.
- PRD ref: `prd.md > Conexión a Gmail`.

### 4. Servicio de Parseo de Digest (`services/parser_service.py`)
Analiza el cuerpo HTML de los correos para identificar bloques de ofertas de empleo.
- Funciones:
  - `extract_jobs_from_html(html_content: str) -> list[dict]`: Extrae títulos de trabajo, texto contextual y URLs correspondientes. Incluye mecanismo de respaldo (fallback) para capturar enlaces con anclas relevantes si la estructura no es estándar.
- PRD ref: `prd.md > Extraer ofertas y links`.

### 5. Evaluador de Match con IA (`services/gemini_service.py`)
Interactúa con el SDK de Gemini para analizar la afinidad entre el CV y las ofertas.
- Funciones:
  - `evaluate_matches(cv_text: str, jobs: list[dict]) -> list[dict]`: Envía el CV y las ofertas al modelo utilizando formato estructurado JSON con `match_percentage`, `verdict` y `suggestion`.
- PRD ref: `prd.md > Match contra el CV`.

### 6. Interfaz de Usuario Web (`static/index.html`, `static/styles.css`, `static/app.js`)
Frontend interactivo SPA (Single Page Application) que gestiona el estado, subida de archivos, ejecución del análisis y renderizado de resultados.
- PRD ref: `prd.md > Screens and Layout`, `prd.md > Features and Behavior`.

## Data Model

- **CV en disco:** `data/cv.pdf`
- **Estructura de Oferta Evaluada:**
  ```json
  {
    "title": "Senior Python Developer",
    "company_or_context": "Tech Co - LinkedIn Jobs",
    "link": "https://www.linkedin.com/jobs/view/...",
    "match_percentage": 85,
    "verdict": "Sí",
    "suggestion": "Coincide fuertemente en backend con Python y APIs, aunque piden nociones de Kubernetes.",
    "email_subject": "30 nuevos empleos para 'Python Developer'",
    "email_date": "2026-09-25"
  }
  ```
- **Persistencia de Resultados:** `data/latest_matches.json` guarda el último lote procesado para recarga instantánea sin reconsultar APIs innecesariamente.

## File Structure

```
hackathon/
├── main.py                     # Aplicación FastAPI y endpoints
├── services/
│   ├── __init__.py
│   ├── pdf_service.py          # Extracción y gestión de CV PDF
│   ├── gmail_service.py        # Conexión IMAP y descarga de correos
│   ├── parser_service.py       # Parseo HTML de digests y links
│   └── gemini_service.py       # Evaluación de match con Gemini API
├── static/
│   ├── index.html              # Interfaz web
│   ├── styles.css              # Estilos visuales (Light theme limpio)
│   └── app.js                  # Lógica del cliente web
├── data/
│   ├── .gitkeep
│   ├── cv.pdf                  # CV guardado en local (excluido de git)
│   └── latest_matches.json     # Resultados del último procesamiento
├── devpost/
│   ├── learner-profile.md      # Perfil del participante
│   ├── scope.md                # Alcance aprobado
│   ├── prd.md                  # Requerimientos de producto aprobados
│   └── spec.md                 # Este documento de especificación técnica
├── requirements.txt            # Dependencias Python
├── .env.example                # Variables de entorno de referencia
└── .gitignore                  # Exclusión de data/, .env, venv, etc.
```

## External Services and Dependencies

1. **Gmail IMAP (`imap.gmail.com:993`)**:
   - Protocolo: IMAP sobre SSL.
   - Credenciales: Usuario y contraseña de aplicación de 16 caracteres.
   - Costo: Gratuito.
2. **Google Gemini API (`gemini-2.5-flash` o `gemini-1.5-flash`)**:
   - SDK: `google-genai`.
   - Llamada: `client.models.generate_content` con salida estructurada JSON.
   - Credenciales: `GEMINI_API_KEY`.
   - Costo: Nivel gratuito / pay-as-you-go estándar.

## Important Failure Modes

1. **Error de autenticación o conexión IMAP:**
   - *Falla:* Contraseña de aplicación inválida o bloqueo de red.
   - *Respuesta:* La app muestra un mensaje en pantalla indicando: "No se pudo conectar a Gmail. Verificá que las credenciales de IMAP sean correctas y que la etiqueta exista."
2. **La etiqueta de Gmail no contiene correos:**
   - *Falla:* Se escribe mal el nombre de la etiqueta o no hay mensajes nuevos.
   - *Respuesta:* La app informa: "No se encontraron correos bajo la etiqueta '[nombre]'. Verificá que el nombre coincida exactamente con la etiqueta en Gmail."
3. **Estructura HTML de digest no estándar:**
   - *Falla:* Un correo no usa las clases o etiquetas habituales de los portales comunes.
   - *Respuesta:* `parser_service.py` incluye un método de extracción heurística por enlaces que rescata las URLs que parecen ofertas con su texto circundante. Si ningún empleo se identifica, la app alerta al usuario en vez de crashear.

## What Was Simplified and Why

- **IMAP con Contraseña de Aplicación en lugar de OAuth2 Completo:**
  - *Por qué:* Configurar una pantalla de consentimiento de OAuth2 en Google Cloud Console requiere pasos tediosos de verificación y URLs de callback. IMAP permite que el POC funcione de inmediato y de forma 100% local.
- **Persistencia en archivos JSON y carpetas locales en lugar de base de datos:**
  - *Por qué:* Para un usuario individual y una sola máquina, guardar `cv.pdf` y `latest_matches.json` en disco es más transparente, directo de inspeccionar y libre de dependencias de bases de datos.
- **Frontend Vanilla servido por FastAPI en lugar de React/Next.js:**
  - *Por qué:* Evita instalar Node.js, npm, paquetes de miles de archivos y pasos de compilación. Un solo comando (`uvicorn main:app`) levanta todo el sistema.

## Decisions and Open Issues

### Decisiones acordadas
1. **Lenguaje y Backend:** Python con FastAPI, elegido por el usuario y recomendado por su facilidad para procesar PDFs, correos y llamadas a IA.
2. **Conexión a Gmail:** IMAP nativo con contraseña de aplicación preconfigurada en variables de sistema.
3. **Múltiples correos:** Se procesarán los últimos $N$ correos con la etiqueta elegida (decisión del usuario para dar un desafío mayor y más valor a la prueba).
4. **Manejo del CV:** Almacenado localmente en `data/cv.pdf` y persistido entre sesiones.

### Concepto técnico aclarado durante la sesión
- **Parseo de digest HTML con múltiples correos:** Se acordó que el extractor procese cada correo por separado, combine los trabajos encontrados deduplicando enlaces repetidos, y luego evalúe el conjunto contra el CV para devolver un único listado consolidado y ordenado.

### Aspectos abiertos para verificar durante el build
- Probar un correo real de la etiqueta de Gmail del usuario para calibrar el extractor HTML con los selectores de los digests que efectivamente recibe (ej. LinkedIn).
