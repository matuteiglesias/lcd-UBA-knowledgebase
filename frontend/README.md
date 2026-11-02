# LCD Knowledge Surface — frontend

Sitio **Next.js** para consultar una copia navegable del contenido del WordPress de LCD: noticias/publicaciones, páginas institucionales y búsqueda por texto. Es un **consumidor** de un conjunto de archivos JSON generado por el pipeline del repositorio padre. No edita WordPress, no es el origen de verdad y no dispone de un CMS propio.

## Ver la copia local

Desde `frontend/`:

```bash
npm ci
npm run dev
# http://localhost:3000
```

La aplicación lee `frontend/data/lcd_bundle/` desde el filesystem del servidor durante el render/build. Ese directorio debe existir; no se obtiene el contenido de WordPress en cada request.

Rutas: `/` (resumen), `/posts`, `/posts/[route_slug]`, `/pages`, `/pages/[route_slug]` y `/search`. La búsqueda es local sobre `search.json`, con normalización de mayúsculas y acentos, no una API semántica.

## De dónde salen los datos

```text
LCD WordPress (REST: page/post)
    → lcd_kb.sources.wordpress_rest (repositorio padre)
    → data/lcd/raw/
    → normalización / controles de build
    → data/lcd/runs/<run_id>/
    → export_front_bundle
    → data/lcd/front_bundle/
    → frontend/data/lcd_bundle/
    → Next.js
```

Archivos del bundle: `manifest.json`, `listing.json`, `posts.json`, `pages.json`, `search.json` e `items/*.json`. Los lee `lib/lcdBundle.ts` y `app/search/page.tsx`. No editar estos JSON como si fueran contenido canónico.

El **objetivo editorial** es mantener un clon consultable de WordPress; la trazabilidad de un run es útil para depurar una actualización, no un requisito de investigación para leer la copia. El pipeline de conocimiento aplica validaciones más estrictas que un simple espejo editorial.

## Refrescar manualmente desde WordPress

Desde la raíz del repositorio **`lcd-UBA-knowledgebase`**, con su entorno Python preparado:

```bash
make doctor
make fetch                # consulta WordPress REST para page y post
make build RUN_ID=lcd_refresh_YYYYMMDDTHHMMSSZ
make latest               # qué run quedó aceptado para consumo estricto
make front-bundle         # exporta el último run trusted a data/lcd/front_bundle
make front-bundle-check
make copy-front-bundle    # vuelve a generar/verificar y copia al frontend
cd frontend && npm run build
```

**Atención:** `make build` procesa los raw batches existentes, pero no hace el fetch por sí mismo. Por eso el paso `make fetch` es indispensable para obtener cambios del WordPress. `make copy-front-bundle` vuelve a exportar desde el último `latest_trusted`; si una validación falla, **no** actualiza el contenido publicado.

Para **previsualizar** un run con advertencias de fuente, existe `make front-bundle-run RUN_ID=<id>`: puede exportar desde staging. Revisar el `manifest.json` generado, el estado del run y los fallos; copiar manualmente ese bundle al frontend **solo si se decide aceptar explícitamente ese preview**. No confundirlo con una versión strict/trusted. La carpeta `data/lcd/front_bundle` del padre es el paso intermedio.

En el checkout inspeccionado el 2 de noviembre de 2026, el bundle visible era un **preview staging de 219 entradas** generado desde `live_lcd_20260424T173509Z`, con `validation_failed` y `trusted=false`. Eso no implica que el contenido sea inútil como directorio: sí implica que **no es un release estricto del corpus de conocimiento**.

## Refresco periódico (pendiente de activar)

La primera versión automatizada sólo necesita ejecutar el mismo proceso con un `RUN_ID` nuevo, comprobar que hay datos válidos, generar/copiar el bundle y **desplegar el frontend sólo cuando cambie el contenido**. Puede implementarse con un cron/runner existente, sin nueva base de datos ni un servicio de sincronización en vivo. Todavía **no hay un calendario periódico habilitado por este README**.

Conviene decidir por separado una política editorial de advertencias (por ejemplo páginas repetidas o publicaciones con sólo video) y el estándar estricto de confianza de la knowledge base. Ver [runbook de ingestión](../docs/runbook_lcd_ingest.md), [estado del pipeline](../docs/carry_state.md) y el `Makefile` del repositorio padre.

## Mantenimiento

- `npm run lint` y `npm run build` validan la aplicación, no la frescura del WordPress.
- Si faltan archivos JSON, resolver el build del **productor**, no inventar registros en este frontend.
- Ante contenido antiguo, primero comprobar fecha/estado del bundle y luego `make fetch`.
- No modificar la autoridad editorial de WordPress: este repositorio sólo publica una proyección.
