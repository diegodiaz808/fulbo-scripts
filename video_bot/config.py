import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

# --- API ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ES = os.getenv("ELEVENLABS_VOICE_ES")

# --- Rutas ---
VIDEOS_JSONL = ROOT / "output" / "videos.jsonl"
IMAGES_DIR = ROOT / "assets" / "images"
MUSIC_DIR = ROOT / "assets" / "music"
OUTPUT_DIR = ROOT / "output" / "videos_terminados"
TEMP_DIR = ROOT / "output" / "temp"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# --- Video ---
WIDTH = 1080
HEIGHT = 1920
FPS = 30

# --- Audio ---
MUSIC_VOLUME = 0.12          # música de fondo bien baja
VOICE_VOLUME = 1.0

# --- Timing (segundos) entre secciones cuando hace falta padding ---
SECTION_GAP = 0.25           # micro-pausa entre secciones

# --- Subtítulos ---
SUBTITLE_FONT = "Arial"
SUBTITLE_FONTSIZE = 64
SUBTITLE_MAX_WORDS = 4       # palabras por bloque de subtítulo
WHISPER_MODEL = "base"       # base = buen balance velocidad/calidad en M1

# --- Branding ---
BRAND_TEXT = "Fulbo.fun"
