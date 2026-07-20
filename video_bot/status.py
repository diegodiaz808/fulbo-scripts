"""
Verifica qué falta antes de generar videos.
Uso: python3 -m video_bot.status
"""
import csv
import json
from pathlib import Path
from .config import (
    IMAGES_DIR, MUSIC_DIR, VIDEOS_JSONL, OUTPUT_DIR,
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ES,
)

ROOT = Path(__file__).parent.parent
MASTER_CSV = ROOT / "output" / "image_master_list.csv"
EXTS = (".png", ".jpg", ".jpeg", ".webp")


def _image_exists(img_id: str) -> bool:
    return any((IMAGES_DIR / f"{img_id}{e}").exists() for e in EXTS)


def check_images() -> dict:
    rows = list(csv.DictReader(open(MASTER_CSV, encoding="utf-8")))
    have, missing = [], []
    for r in rows:
        (have if _image_exists(r["image_id"]) else missing).append(r)
    return {"total": len(rows), "have": have, "missing": missing}


def check_music() -> list:
    return (list(MUSIC_DIR.glob("*.mp3")) +
            list(MUSIC_DIR.glob("*.m4a")) +
            list(MUSIC_DIR.glob("*.wav")))


def check_key() -> dict:
    import requests
    try:
        r = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": ELEVENLABS_API_KEY}, timeout=10,
        )
        if r.status_code != 200:
            return {"ok": False, "msg": f"key inválida ({r.status_code})"}
        # probar permiso TTS con un request mínimo
        test = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ES}",
            headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
            json={"text": "test", "model_id": "eleven_multilingual_v2"}, timeout=15,
        )
        if test.status_code == 200:
            d = r.json()
            return {"ok": True, "msg": f"{d.get('character_limit',0)-d.get('character_count',0)} chars disponibles"}
        if test.status_code == 401:
            return {"ok": False, "msg": "key sin permiso text_to_speech — activalo en ElevenLabs"}
        return {"ok": False, "msg": f"error TTS ({test.status_code})"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def count_videos() -> int:
    with open(VIDEOS_JSONL, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def count_done() -> int:
    return len(list(OUTPUT_DIR.glob("*.mp4")))


def main():
    print("\n" + "=" * 50)
    print("  ESTADO DEL BOT DE VIDEOS FULBO")
    print("=" * 50)

    # Imágenes
    img = check_images()
    pct = int(len(img["have"]) / img["total"] * 100) if img["total"] else 0
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"\n📸 IMÁGENES   {bar} {len(img['have'])}/{img['total']} ({pct}%)")
    if img["missing"]:
        print(f"   Faltan {len(img['missing'])} imágenes. Nombres exactos que tenés que crear:")
        by_topic = {}
        for r in img["missing"]:
            by_topic.setdefault(r["topic"], []).append(r)
        for topic, items in by_topic.items():
            print(f"\n   {topic}:")
            for r in items:
                print(f"     • {r['image_id']}.png  —  {r['title']}")

    # Música
    music = check_music()
    print(f"\n🎵 MÚSICA     {'✓' if music else '✗'}  {len(music)} track(s) en assets/music/")
    if not music:
        print("   Poné al menos 1 archivo .mp3 en assets/music/")

    # API key
    key = check_key()
    print(f"\n🔑 VOZ (API)  {'✓' if key['ok'] else '✗'}  {key['msg']}")

    # Videos
    total = count_videos()
    done = count_done()
    print(f"\n🎬 VIDEOS     {done}/{total} generados")

    # Veredicto
    print("\n" + "-" * 50)
    ready = bool(music) and key["ok"] and len(img["have"]) > 0
    if ready and not img["missing"]:
        print("  ✅ TODO LISTO — corré: python3 -m video_bot.build")
    elif ready:
        print(f"  ⚠️  Podés generar parcial (faltan {len(img['missing'])} imágenes).")
        print("     Los videos sin todas sus imágenes usan fallback.")
        print("     Corré: python3 -m video_bot.build")
    else:
        print("  ⛔ Faltan cosas (ver arriba) antes de generar.")
    print("-" * 50 + "\n")


if __name__ == "__main__":
    main()
