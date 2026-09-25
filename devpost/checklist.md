---
doc: checklist
status: approved
---

# Build Checklist

Build mode: learn

## Slices

- [x] **1. Carga de CV en PDF y servidor web base**
  Becomes usable: Un servidor web local corriendo en `http://localhost:8000` con una interfaz clara y limpia donde podés subir tu CV en PDF, se guarda en `data/cv.pdf` y la app recuerda que el CV ya está listo incluso al recargar.
  Why now: Pone en marcha el proyecto (FastAPI + interfaz web + extracción de PDF) y resuelve el primer paso del recorrido del usuario antes de tocar la red externa.
  PRD ref: `prd.md > The Core Journey` (pasos 1-2), `prd.md > Cargar el CV`
  Spec ref: `spec.md > Servidor Principal`, `spec.md > Servicio de CV`, `spec.md > Interfaz de Usuario Web`
  Build: Crear estructura del proyecto, `requirements.txt`, `services/pdf_service.py` (con `pypdf`), servidor `main.py`, y frontend estático (`static/index.html`, `static/styles.css`, `static/app.js`) con endpoint `POST /api/cv/upload` y `GET /api/cv/status`.
  Verify (mechanical): Iniciar el servidor localmente con uvicorn, simular la subida de un PDF y verificar que se guarda en `data/cv.pdf`, que `pypdf` extrae el texto y que el estado persiste.
  Learner check: Abrís `http://localhost:8000`, subís tu CV en PDF y confirmás que la interfaz muestra que quedó cargado y guardado.
  Commit: `Add web server, PDF CV upload and persistence`

- [ ] **2. Conexión IMAP y extracción de ofertas de Gmail**
  Becomes usable: Podés ingresar la etiqueta de Gmail (ej. `LinkedIn`), elegir cuántos correos procesar ($N$), y la app se conecta por IMAP, descarga los correos digest y extrae los títulos de las ofertas con sus links directos.
  Why now: Aborda el principal riesgo externo del proyecto (la conexión segura con Gmail y el parseo del HTML variado de los correos) antes de llamar a la IA.
  PRD ref: `prd.md > The Core Journey` (pasos 3-4), `prd.md > Conexión a Gmail`, `prd.md > Extraer ofertas y links`
  Spec ref: `spec.md > Servicio de Gmail IMAP`, `spec.md > Servicio de Parseo de Digest`
  Build: Implementar `services/gmail_service.py` usando `imaplib` con variables de sistema, `services/parser_service.py` usando `beautifulsoup4` para desarmar las listas de puestos y extraer URLs, y endpoint para testear la extracción.
  Verify (mechanical): Ejecutar script de verificación que autentica en IMAP, lee los correos con la etiqueta indicada y confirma que se extraen ofertas con enlaces válidos.
  Learner check: Ingresás tu etiqueta en la app web y ves la lista de ofertas y links extraídos directamente desde tus correos.
  Commit: `Add Gmail IMAP fetch and digest HTML parser`

- [ ] **3. Evaluación de afinidad con Gemini y tarjetas interactivas de resultados**
  Becomes usable: El flujo completo de punta a punta: Gemini compara el texto de tu CV contra cada oferta extraída, calcula el % de match, genera el veredicto (`Sí`/`No`/`Puede ser`) y la sugerencia de una línea, guardando los resultados en `data/latest_matches.json` y mostrándolos en tarjetas interactivas ordenadas por afinidad.
  Why now: Conecta todas las piezas y entrega el núcleo único del producto (el filtro inteligente para no leer digests manualmente).
  PRD ref: `prd.md > The Core Journey` (pasos 5-7), `prd.md > Match contra el CV`
  Spec ref: `spec.md > Evaluador de Match con IA`, `spec.md > Data Model`
  Build: Implementar `services/gemini_service.py` usando `google-genai` con salida estructurada JSON, conectar el endpoint `POST /api/jobs/process`, guardar `data/latest_matches.json`, y actualizar la interfaz para mostrar las tarjetas con sus badges de porcentaje y botón de enlace directo.
  Verify (mechanical): Ejecutar un análisis completo de prueba y verificar que Gemini retorna el JSON estructurado válido, que se guarda el archivo local y que el frontend renderiza las tarjetas.
  Learner check: Hacés una búsqueda completa desde la interfaz web, revisás las ofertas evaluadas con sus sugerencias y porcentajes, y hacés clic en el link de una oferta para abrirla.
  Commit: `Add Gemini AI match evaluation and interactive result cards`

## Hands-on Checkpoints

- [x] Early usable behavior explored — Slice 1 completado con subida y detección de CV
- [ ] Final kick-the-tires exploration and feedback completed — Prueba completa de punta a punta con correos reales y evaluación de Gemini

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: 
Route and stops: 
Edit outcome: 
Reflection: 
Activity mode: 

## Revisions
