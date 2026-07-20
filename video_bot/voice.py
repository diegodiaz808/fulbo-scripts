import subprocess
import requests
from pathlib import Path
from .config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ES, TEMP_DIR

SECTIONS = ["HOOK", "CONTEXT", "BODY", "CTA"]


def generate_section_audios(video_id: str, script: dict) -> list[dict]:
    """
    Genera un audio por sección (HOOK, CONTEXT, BODY, CTA).
    Retorna lista ordenada: [{section, text, path, duration}]
    """
    results = []
    for section in SECTIONS:
        if section not in script:
            continue
        text = script[section]["text"]
        out_path = TEMP_DIR / f"{video_id}_{section}.mp3"
        _tts(text, out_path)
        duration = _audio_duration(out_path)
        results.append({
            "section": section,
            "text": text,
            "path": out_path,
            "duration": duration,
        })
    return results


def _tts(text: str, out_path: Path):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ES}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.75,
            "style": 0.35,
            "use_speaker_boost": True,
        },
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text[:200]}")
    out_path.write_bytes(r.content)


def _audio_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def concat_audios(video_id: str, sections: list[dict]) -> Path:
    """Une los audios de las secciones en un solo archivo de narración."""
    list_file = TEMP_DIR / f"{video_id}_audiolist.txt"
    lines = [f"file '{s['path'].name}'" for s in sections]
    list_file.write_text("\n".join(lines))

    out_path = TEMP_DIR / f"{video_id}_voz.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c", "copy", str(out_path)],
        check=True, capture_output=True, cwd=str(TEMP_DIR),
    )
    return out_path


def check_quota() -> dict:
    r = requests.get(
        "https://api.elevenlabs.io/v1/user/subscription",
        headers={"xi-api-key": ELEVENLABS_API_KEY}, timeout=10,
    )
    d = r.json()
    used = d.get("character_count", 0)
    limit = d.get("character_limit", 10000)
    return {"used": used, "limit": limit, "remaining": limit - used}
