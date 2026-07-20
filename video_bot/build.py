"""
Ensamblador de videos Fulbo.
Lee output/videos.jsonl y produce un MP4 por línea en output/videos_terminados/.
No inventa contenido: solo une voz + imágenes + subtítulos + música.

Uso:
    python3 -m video_bot.build                 # genera todos los que falten
    python3 -m video_bot.build VIDEO_0001      # genera uno solo
    python3 -m video_bot.build --limit 5       # genera los primeros 5 que falten
    python3 -m video_bot.build --force         # regenera aunque ya existan
"""
import sys
import json
import time
import traceback
from pathlib import Path

from .config import VIDEOS_JSONL, OUTPUT_DIR, IMAGES_DIR, TEMP_DIR
from .voice import generate_section_audios, concat_audios, check_quota
from .subtitles import generate_subtitles
from .assembler import map_sections_to_images, render_clip, concat_clips, finalize


def load_videos() -> list[dict]:
    videos = []
    with open(VIDEOS_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                videos.append(json.loads(line))
    return videos


def build_one(video: dict, force: bool = False) -> dict:
    vid = video["video_id"]
    out_file = OUTPUT_DIR / f"{vid}.mp4"

    if out_file.exists() and not force:
        return {"video_id": vid, "status": "skip", "reason": "ya existe"}

    print(f"\n=== {vid} ({video.get('topic_name', '')}) ===")

    # 1. Voz por sección
    print("  → Generando voz (ElevenLabs)...")
    sections = generate_section_audios(vid, video["script"])
    total_dur = sum(s["duration"] for s in sections)
    print(f"    {len(sections)} secciones, {total_dur:.1f}s de narración")

    # 2. Concatenar voz
    voice_audio = concat_audios(vid, sections)

    # 3. Subtítulos con Whisper
    print("  → Generando subtítulos (Whisper)...")
    subs = generate_subtitles(vid, voice_audio)

    # 4. Mapear secciones a imágenes
    timeline = map_sections_to_images(sections, video["images"])

    # 5. Render de clips con Ken Burns
    print("  → Renderizando clips...")
    clip_paths = []
    for i, item in enumerate(timeline):
        if item["image_path"] is None:
            raise RuntimeError(f"No hay imagen para sección {item['section']} y no hay fallback")
        clip = TEMP_DIR / f"{vid}_clip{i}.mp4"
        render_clip(item["image_path"], item["duration"], clip)
        clip_paths.append(clip)

    silent = concat_clips(vid, clip_paths)

    # 6. Final: video + subs + voz + música
    print("  → Ensamblando final...")
    final = finalize(vid, silent, voice_audio, subs)

    _cleanup(vid)
    print(f"  ✓ {final.name}")
    return {"video_id": vid, "status": "ok", "path": str(final)}


def _cleanup(vid: str):
    for f in TEMP_DIR.glob(f"{vid}_*"):
        try:
            f.unlink()
        except OSError:
            pass


def main():
    args = sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]

    limit = None
    if "--limit" in args:
        idx = args.index("--limit")
        limit = int(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    specific = args[0] if args else None

    if not IMAGES_DIR.glob("*"):
        print("⚠ No hay imágenes en assets/images/")

    videos = load_videos()
    if specific:
        videos = [v for v in videos if v["video_id"] == specific]
        if not videos:
            print(f"No se encontró {specific}")
            return

    # quota check
    try:
        q = check_quota()
        print(f"ElevenLabs: {q['remaining']} caracteres restantes\n")
    except Exception as e:
        print(f"No se pudo chequear quota: {e}\n")

    done = 0
    results = []
    for v in videos:
        if limit and done >= limit:
            break
        try:
            r = build_one(v, force=force)
            results.append(r)
            if r["status"] == "ok":
                done += 1
        except Exception as e:
            print(f"  ✗ Error en {v['video_id']}: {e}")
            traceback.print_exc()
            results.append({"video_id": v["video_id"], "status": "error", "error": str(e)})

    ok = len([r for r in results if r["status"] == "ok"])
    skip = len([r for r in results if r["status"] == "skip"])
    err = len([r for r in results if r["status"] == "error"])
    print(f"\n=== Listo: {ok} creados, {skip} saltados, {err} errores ===")
    print(f"Carpeta: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
