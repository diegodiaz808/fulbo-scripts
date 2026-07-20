# Handoff: Script Bot → Video Bot

Este documento define **de dónde saca cada cosa** el bot de video. El script bot ya dejó
todo listo; el bot de video solo consume estos archivos. No inventa contenido.

## Archivo de entrada (la fuente)
`output/videos.jsonl` - **un video por línea**. Cada línea trae todo lo necesario:

```json
{
  "video_id": "VIDEO_0001",
  "topic": "AI_MANAGER",
  "topic_name": "Sos el DT, la IA juega",
  "duration_hint": "20-35s",
  "script": {
    "HOOK":    {"id": "AI_MANAGER_HOOK_B",    "text": "Esto no es FIFA..."},
    "CONTEXT": {"id": "AI_MANAGER_CONTEXT_A",  "text": "Fulbo es un juego..."},
    "BODY":    {"id": "AI_MANAGER_BODY_C",     "text": "El que tiene mejores reflejos..."},
    "CTA":     {"id": "AI_MANAGER_CTA_A",      "text": "Probá ser DT en la beta..."}
  },
  "images": [
    {"id": "AI_MANAGER_SCENE_001_A", "section": "HOOK",    "title": "...", "prompt": "..."},
    {"id": "AI_MANAGER_SCENE_002_A", "section": "CONTEXT", "title": "...", "prompt": "..."}
  ]
}
```

Regla: el orden del guión es SIEMPRE `HOOK → CONTEXT → BODY → CTA`.

## De dónde saca cada cosa
| Necesita | De dónde |
|---|---|
| Texto a narrar / subtitular | `script.HOOK/CONTEXT/BODY/CTA.text`, en ese orden |
| Qué imagen va en cada momento | `images[]`, campo `section` dice a qué parte pertenece |
| Archivo de imagen real | `assets/images/<image_id>.png` (ver convención abajo) |
| Nombre del video final | `video_id` (ej: `VIDEO_0001.mp4`) - NO cambiar |
| Duración objetivo | `duration_hint` |

## Convención de imágenes (el puente)
1. Diego (o un bot de imágenes) genera cada imagen de `output/image_master_list.csv`
   usando su `prompt`.
2. Cada imagen se guarda con el nombre EXACTO de su `image_id`:
   `assets/images/AI_MANAGER_SCENE_001_A.png`
3. El bot de video, para cada item de `images[]`, busca `assets/images/<id>.png` y la usa
   en la sección que indica `section`. Así nunca se cruzan imágenes de otro topic.

## Qué le queda por hacer al bot de video
El script bot NO hace nada de esto - es 100% trabajo del bot de video:
1. **Voz / narración**: TTS de los 4 textos (o locución). Voz en es-AR.
2. **Subtítulos**: texto en pantalla sincronizado con la voz (clave en mobile).
3. **Montaje de imágenes**: una imagen por sección, en orden, con la duración repartida.
4. **Timing/pacing**: HOOK corto y fuerte (~2-3s), CONTEXT rápido, BODY el grueso, CTA al final.
5. **Música y SFX**: pista de fondo + efecto en el hook.
6. **Transiciones / movimiento**: zoom lento (Ken Burns), cortes al ritmo.
7. **Formato**: render 9:16 vertical (1080x1920).
8. **Branding**: logo/marca de agua sutil, CTA visual con 'Fulbo.fun' al cierre.
9. **Nombrar el output con `video_id`** para poder medir después.

## El loop de medición (cierra el círculo)
1. El bot de video exporta `VIDEO_0001.mp4`, etc.
2. Diego los publica y junta métricas.
3. Carga resultados en `output/performance.csv` (columna `score` con el KPI que importe).
4. `python3 analyze.py` devuelve qué hooks/contexts/bodies/ctas/imágenes ganan.
5. Con eso se ajusta `data/assets.json` y se regenera. Repetir.

## Prompt sugerido para arrancar el bot de video
> "Sos un bot que arma videos verticales (9:16) a partir de un archivo `videos.jsonl`.
> Por cada línea: narrá en español rioplatense los textos de `script` en orden
> HOOK→CONTEXT→BODY→CTA, poné subtítulos sincronizados, y mostrá las imágenes de `images[]`
> tomándolas de `assets/images/<image_id>.png` según su `section`. Música de fondo, hook de
> 2-3s, CTA visual al final con 'Fulbo.fun'. Exportá cada video como `<video_id>.mp4`.
> No mezcles assets de distintos `topic` ni inventes texto fuera del que viene en el archivo."
