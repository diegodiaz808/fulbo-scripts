import subprocess
import random
from pathlib import Path
from .config import (
    IMAGES_DIR, MUSIC_DIR, OUTPUT_DIR, TEMP_DIR,
    WIDTH, HEIGHT, FPS, MUSIC_VOLUME, VOICE_VOLUME,
)


def map_sections_to_images(sections: list[dict], images: list[dict]) -> list[dict]:
    """
    Asocia cada sección (con su duración) a su imagen correspondiente.
    Si una sección no tiene imagen propia, reutiliza la última disponible.
    Retorna [{section, duration, image_path}]
    """
    by_section = {}
    for img in images:
        by_section.setdefault(img["section"], []).append(img["id"])

    timeline = []
    last_path = None
    for s in sections:
        sec = s["section"]
        img_path = None
        if sec in by_section and by_section[sec]:
            img_id = by_section[sec][0]
            candidate = _find_image_file(img_id)
            if candidate:
                img_path = candidate
                last_path = candidate
        if img_path is None:
            img_path = last_path or _fallback_image()
        timeline.append({
            "section": sec,
            "duration": s["duration"],
            "image_path": img_path,
        })
    return timeline


def _find_image_file(img_id: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = IMAGES_DIR / f"{img_id}{ext}"
        if p.exists():
            return p
    return None


def _fallback_image() -> Path | None:
    imgs = list(IMAGES_DIR.glob("*.png")) + list(IMAGES_DIR.glob("*.jpg"))
    return imgs[0] if imgs else None


def render_clip(image_path: Path, duration: float, out_path: Path):
    """Genera un clip de video con zoom lento (Ken Burns) a partir de una imagen."""
    frames = max(1, int(duration * FPS))
    # escala para cubrir 9:16, upscale x2 para zoom suave, zoompan, vuelve a 1080x1920
    vf = (
        f"scale={WIDTH*2}:{HEIGHT*2}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH*2}:{HEIGHT*2},"
        f"zoompan=z='min(zoom+0.0006,1.12)':d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={WIDTH}x{HEIGHT}:fps={FPS},"
        f"format=yuv420p"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loop", "1", "-i", str(image_path),
         "-t", f"{duration:.3f}", "-vf", vf, "-r", str(FPS),
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         str(out_path)],
        check=True, capture_output=True,
    )


def concat_clips(video_id: str, clip_paths: list[Path]) -> Path:
    list_file = TEMP_DIR / f"{video_id}_cliplist.txt"
    list_file.write_text("\n".join(f"file '{p.name}'" for p in clip_paths))
    out_path = TEMP_DIR / f"{video_id}_silent.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c", "copy", str(out_path)],
        check=True, capture_output=True, cwd=str(TEMP_DIR),
    )
    return out_path


def finalize(video_id: str, silent_video: Path, voice_audio: Path,
             subs_ass: Path | None) -> Path:
    """
    Une video + subtítulos + voz + música de fondo en el MP4 final.
    """
    music = _pick_music()
    out_path = OUTPUT_DIR / f"{video_id}.mp4"

    inputs = ["-i", str(silent_video), "-i", str(voice_audio)]
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(music)]

    # filtro de video: subtítulos quemados
    if subs_ass and subs_ass.exists():
        # ass filter necesita el path escapado
        ass_escaped = str(subs_ass).replace(":", "\\:").replace("'", "\\'")
        video_filter = f"[0:v]ass='{ass_escaped}'[v]"
    else:
        video_filter = "[0:v]copy[v]"

    # filtro de audio: voz + música
    if music:
        audio_filter = (
            f"[1:a]volume={VOICE_VOLUME}[voz];"
            f"[2:a]volume={MUSIC_VOLUME}[mus];"
            f"[voz][mus]amix=inputs=2:duration=first:dropout_transition=0[a]"
        )
    else:
        audio_filter = f"[1:a]volume={VOICE_VOLUME}[a]"

    filter_complex = f"{video_filter};{audio_filter}"

    cmd = ["ffmpeg", "-y", *inputs,
           "-filter_complex", filter_complex,
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k",
           "-shortest", str(out_path)]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def _pick_music() -> Path | None:
    files = (list(MUSIC_DIR.glob("*.mp3")) +
             list(MUSIC_DIR.glob("*.m4a")) +
             list(MUSIC_DIR.glob("*.wav")))
    return random.choice(files) if files else None
