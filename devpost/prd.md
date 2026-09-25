---
doc: prd
status: approved
---
<!-- `status` is the progress state every skill reads. Write `draft` when you first save this file,
     and change it to `approved` when the learner clearly approves the displayed plan ("looks good" counts).
     Do not request a second sign-off. Never skip the draft save —
     an unsaved draft dies with the conversation. -->

# Ofertas vs CV — Product Requirements

App local para vos: elegís una etiqueta de Gmail, leés esos digests y ves cada empleo con match al CV, para no tener que leer el montón.
Source: `scope.md > The Unique Kernel`, `scope.md > Who It's For`.

## The Core Journey
Source: `scope.md > The Core Loop`, `scope.md > What "Working" Looks Like`.

1. Abrís la app.
2. Si no hay un CV cargado de antes, la app **pregunta** y cargás un **PDF**. Si ya está, no lo vuelve a pedir.
3. Elegís **una etiqueta** (ej. LinkedIn o Glassdoor). Esas etiquetas **ya están** en el correo; no las crea la app.
4. La **conexión es local**. Se ejecuta la lectura de los mails con esa etiqueta.
5. Ves la **lista de empleos**, cada uno con porcentaje y el resto de datos de la fila.
6. Abrís a mano el **link** de los que valen la pena.
7. Éxito: no leíste el digest entero ni todas las ofertas; la lista ya te dice cuáles mirar.

## Screens and Layout
Una superficie principal, no un tablero.

- **Arriba / inicio:** si falta el CV, el pedido del PDF. Siempre, una forma de **elegir la etiqueta** (ej. LinkedIn o Glassdoor) y disparar la lectura.
- **Después de leer:** la **lista de empleos**. Cada fila muestra lo de Features and Behavior.
- No hay pantalla de stats ni de “guardados” en este POC.

## Look and Feel
Clara, útil, **light**, y **más armada** que un listado crudo: se nota pensada, no el look genérico de app de IA. Colores y tipografía exactos no se fijaron; el build debe sentirse ordenado y con jerarquía (porcentaje y veredicto fáciles de ver), no un dump de texto.

## Features and Behavior

### Cargar el CV
Si no hay CV previo, se pregunta y se acepta **PDF**. Si ya está cargado, se sigue a la etiqueta.
Source: `scope.md > The POC Boundary`.

### Elegir etiqueta y leer
Elegís una etiqueta que ya existe en el correo. La conexión es local. Al ejecutar, se leen solo los mails con esa etiqueta (un tipo de digest HTML: lista de jobs + links).
Source: `scope.md > The POC Boundary`.

### Lista de empleos
Cada fila incluye:
- empresa
- descripción del puesto
- **porcentaje** de match al CV
- veredicto **sí / no / puede ser**
- una **sugerencia**
- **link** para revisar el trabajo

Source: `scope.md > The Unique Kernel`.

## States and Boundaries

- **Primer uso (sin CV)** — se pide el PDF; sin eso no hay match.
- **CV ya cargado** — no se vuelve a preguntar; vas a elegir etiqueta.
- **Sin mails con esa etiqueta** — mensaje claro: **elegí otra etiqueta**, o **aplicá esa etiqueta en el mail** y volvé a leer.
- **Éxito** — lista con filas completas (empresa, descripción, %, veredicto, sugerencia, link).
- **Persistencia** — el CV cargado se reutiliza la próxima vez. No se guarda tracking de postulaciones (empresa/postulación/link) en este POC.
- **Límite** — solo Gmail local, solo la etiqueta elegida, un formato de digest para el demo. Quién usa esto: vos.

## Product Decisions

- Etiqueta primero (ej. LinkedIn o Glassdoor), ya presente en el correo — para no leer todo Gmail.
- Conexión local — el mail no se manda a otro lado.
- Si no hay CV, preguntar; formato PDF.
- Fila = empresa + descripción + link + porcentaje + sí/no/puede ser + sugerencia — para decidir rápido y abrir solo lo que vale.
- Vacío de etiqueta: otra etiqueta o aplicarla en el mail — el filtro lo ponés vos en Gmail.
- Visual más armada, light — que no se vea genérica ni un listado pelado.

## What We're Building
Source: `scope.md > The POC Boundary`.

- Pedido de CV PDF si falta.
- Elección de una etiqueta y lectura local de esos mails.
- Un tipo de digest HTML (jobs + links) extraído a filas.
- Lista en pantalla con empresa, descripción, %, veredicto, sugerencia, link.
- Estado vacío: cambiar etiqueta o aplicarla en el correo.
- Look light y más armado, en una superficie.

## Deferred From the POC
- Guardar empresa, postulación y link — tracking; no hace falta para el demo de match.
- Varios formatos de digest / varios portales a la vez — el demo prueba uno.
- Persistencia JSON u otro almacenamiento interno — detalle de `4-spec`, no de la experiencia del demo.
- Tablero, columnas, stats.
- Auth si algún día no es local.

## Possible Later Enhancements
Tablero con stats. Más pulido visual. Más portales/layouts. Guardar postulaciones. Un modelo aparte sobre los datos leídos.

## Non-Goals
Source: `scope.md > Explicitly Cut`.

- Dashboard de estadísticas en este hackathon.
- Producto para otras personas o SaaS.
- Scrapear las plataformas: el input es Gmail etiquetado.
- Leer todo el Gmail: solo la etiqueta elegida.

## Open Questions
- Cómo se calcula el porcentaje y el veredicto — no es decisión de producto de pantallas; se resuelve en `4-spec` (no bloquea este PRD).
- Paleta y tipografía concretas — no bloquea; `4-spec` traduce “light y más armada”.
