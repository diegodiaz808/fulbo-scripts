# Fulbo Script Bot

Genera **guiones para videos verticales** (TikTok/Reels/Shorts) sobre Fulbo.
NO crea videos: produce guiones reutilizables, combinables y medibles que después
consume el bot de video.

## Estructura fija de cada video
`HOOK → CONTEXT → BODY → CTA` (el CONTEXT siempre explica qué es Fulbo).
**Regla de oro:** todo en un video pertenece al mismo `topic`. Cero mezclas.

## Archivos
```
fulbo_context.md          # fuente de verdad del proyecto (no inventar datos)
data/assets.json          # DATASET: topics > hooks/contexts/bodies/ctas/scenes
generate.py               # combina assets en videos con ID unico
analyze.py                # detecta assets y combinaciones ganadoras
output/
  videos.csv              # tabla de IDs (para medir)
  videos.jsonl            # guiones completos con textos (input del bot de video)
  scripts_preview.md      # guiones legibles para revisar
  image_master_list.csv   # LISTA MAESTRA de imagenes (seccion, titulo, prompt)
  performance_template.csv# plantilla para cargar metricas
  winners_report.md       # salida del analisis
```

## Flujo de trabajo
1. **Generar:** `python3 generate.py` → 12 videos por topic (o `--all`, `--topics`, `--max-per-topic N`).
2. **Imágenes:** abrí `output/image_master_list.csv` y creá/buscá cada imagen con su prompt.
3. **Producir:** pasás `output/videos.jsonl` al bot de video.
4. **Medir:** copiá `performance_template.csv` a `performance.csv` y cargá la columna `score`.
5. **Aprender:** `python3 analyze.py` → ranking de assets ganadores + combinaciones que más se repiten.
   (Probá `python3 analyze.py --demo` para verlo funcionar con datos sintéticos.)

## Cómo agregar contenido
Editá `data/assets.json`. Para un topic nuevo, copiá la estructura de uno existente y
respetá el formato de IDs: `TOPIC_HOOK_A`, `TOPIC_CONTEXT_A`, `TOPIC_BODY_A`,
`TOPIC_CTA_A`, `TOPIC_SCENE_001_A` (con `section` = HOOK/CONTEXT/BODY/CTA).

## Topics actuales
AI_MANAGER · PLAYER_LIFESPAN · SCOUTS · RARITY · MARKET · PRESALE_BETA
