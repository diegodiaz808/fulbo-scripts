from pathlib import Path
from .config import (
    TEMP_DIR, WHISPER_MODEL, SUBTITLE_MAX_WORDS,
    SUBTITLE_FONT, SUBTITLE_FONTSIZE, WIDTH, HEIGHT,
)

_model = None


def _get_model():
    global _model
    if _model is None:
        import whisper
        print(f"  Cargando modelo Whisper '{WHISPER_MODEL}' (1ra vez tarda)...")
        _model = whisper.load_model(WHISPER_MODEL)
    return _model


def generate_subtitles(video_id: str, audio_path: Path) -> Path:
    """
    Transcribe el audio con Whisper y genera un .ass con subtítulos
    sincronizados en bloques cortos. Retorna la ruta del .ass.
    """
    model = _get_model()
    result = model.transcribe(
        str(audio_path),
        language="es",
        word_timestamps=True,
        fp16=False,
    )

    words = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            words.append({
                "text": w["word"].strip(),
                "start": w["start"],
                "end": w["end"],
            })

    blocks = _group_words(words, SUBTITLE_MAX_WORDS)
    ass_path = TEMP_DIR / f"{video_id}_subs.ass"
    _write_ass(blocks, ass_path)
    return ass_path


def _group_words(words: list[dict], max_words: int) -> list[dict]:
    blocks = []
    for i in range(0, len(words), max_words):
        chunk = words[i:i + max_words]
        if not chunk:
            continue
        blocks.append({
            "text": " ".join(w["text"] for w in chunk),
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
        })
    return blocks


def _write_ass(blocks: list[dict], out_path: Path):
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Fulbo,{SUBTITLE_FONT},{SUBTITLE_FONTSIZE},&H00FFFFFF,&H00000000,&H64000000,1,1,4,2,2,80,80,420

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for b in blocks:
        start = _ass_time(b["start"])
        end = _ass_time(b["end"])
        text = b["text"].upper().replace("\n", " ")
        lines.append(f"Dialogue: 0,{start},{end},Fulbo,,0,0,0,,{text}")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
