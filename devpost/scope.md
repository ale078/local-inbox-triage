---
doc: scope
status: approved
---
<!-- `status` is the progress state every skill reads. Write `draft` when you first save this file,
     and change it to `approved` when the learner clearly approves the displayed plan ("looks good" counts).
     Do not request a second sign-off. Never skip the draft save —
     an unsaved draft dies with the conversation. -->

# Ofertas vs CV

App local sobre **Gmail**: lee mails de alertas de plataformas (etiqueta que puede variar), saca **cada oferta y su link** de esas listas, y te muestra cuáles matchean con tu CV — para no tener que leer el montón.

## The Unique Kernel
No scrapeás las plataformas. Las plataformas te mandan mails (cada uno con **una lista de trabajos y sus links**). Vos les ponés **una etiqueta que puede variar**. La app, en local, abre esos mails, **desarma la lista**, y contra **tu CV** te dice el **porcentaje de match** de cada oferta (y el veredicto sí / no / puede ser, más una sugerencia). El punto es **reducir cuántos mails y cuántas ofertas tenés que leer a diario**.

## Who It's For
Vos, buscando trabajo. Estás registrado en plataformas que te llenan Gmail con alertas. Hoy etiquetás y igual tenés que leer un montón de digest. Esto es para vos, no un producto para otros.

## The Core Loop
Abrís la app con el CV cargado. Lee Gmail por la etiqueta (variable). De cada mail saca las ofertas y los links. Ves una **lista en pantalla**: cada trabajo con porcentaje, sí/no/puede ser, el link, y una línea de sugerencia. Abrís a mano solo lo que vale. Volvés a la mañana: nuevos digest etiquetados → lista ya filtrada.

## Inspiration & Identity
Visual poco por ahora; energía clara, útil, **light**. Tablero/stats: más adelante. JSON de las lecturas por debajo (para un modelo después); el demo es la lista.

## Why This Matters to the Learner
“Lo que pretendo es reducir la cantidad de mails que tengo que leer a diario.” Gmail, ofertas de plataformas en las que te registraste, etiqueta variable, y no leerlos todos.

## What "Working" Looks Like
En el video: un digest típico (lista de jobs + links) entra, y en pantalla aparece **cada oferta ya con % de match al CV**, veredicto, link, sugerencia. El beat: no tuviste que leer el mail entero ni todas las ofertas.

## The POC Boundary
- **Gmail**, lectura **local**.
- Mails con **etiqueta** (el nombre de la etiqueta **puede variar**).
- Cada mail es un **digest**: lista de trabajos + links → extraer ítems directamente del código HTML del mail (no hacen falta imágenes, es más directo y exacto).
- Un **CV en formato PDF** contra el que se compara (se procesará el texto completo, ya que los modelos actuales lo manejan bien y da más contexto que solo usar palabras clave).
- Lista en pantalla: porcentaje, sí / no / puede ser, link, una sugerencia.
- El demo prueba **un** tipo de digest (un mail HTML con lista de jobs + links). Otros portales / layouts distintos: después.

## Later
- Tablero (columnas, stats).
- Más visual / pulido.
- Autenticación si algún día no es local.
- Imagen del mail o HTML embebido como otra entrada.
- Un modelo que consuma el JSON como producto aparte.
- Guardar empresa, postulación y link (tracking de postulaciones).
- Más de un formato de digest / varios portales.
- Persistencia JSON u otro almacenamiento interno (detalle en `4-spec`).

## Explicitly Cut
- Tablero o dashboard de estadísticas **en este hackathon**.
- Producto para otras personas o SaaS.
- Entrar a las plataformas a scrapear ofertas: el input es **Gmail etiquetado**, no el sitio de cada portal.
- Vaciar o leer **todo** el Gmail: solo los mails con esa etiqueta.
