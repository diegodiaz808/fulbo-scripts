#!/usr/bin/env python3
"""
Fulbo Script Bot — Generador de guiones.

Combina assets (hook + context + body + cta + imagenes) en videos COHERENTES por topic,
les asigna un ID unico y medible, y exporta:

  output/videos.csv            -> tabla de IDs (para medir performance)
  output/videos.jsonl          -> guiones completos con textos (input del bot de video)
  output/scripts_preview.md    -> primeros guiones renderizados para leer
  output/image_master_list.csv -> lista maestra de TODAS las imagenes a crear/buscar
  output/performance_template.csv -> plantilla vacia para cargar metricas

Uso:
  python3 generate.py                       # default: hasta 12 videos por topic
  python3 generate.py --max-per-topic 6
  python3 generate.py --all                 # todas las combinaciones posibles
  python3 generate.py --topics AI_MANAGER MARKET
"""
import argparse, csv, itertools, json, os, random

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "assets.json")
OUT = os.path.join(ROOT, "output")
SECTIONS = ["HOOK", "CONTEXT", "BODY", "CTA"]


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def scenes_by_section(topic):
    out = {s: [] for s in SECTIONS}
    for sc in topic.get("scenes", []):
        out.setdefault(sc["section"], []).append(sc)
    return out


def pick_images(scene_map, rnd):
    """Una imagen por seccion que tenga escenas disponibles."""
    chosen = []
    for sec in SECTIONS:
        opts = scene_map.get(sec, [])
        if opts:
            chosen.append(rnd.choice(opts))
    return chosen


def build(data, topic_filter, max_per_topic, take_all, seed):
    rnd = random.Random(seed)
    videos = []
    n = 0
    for tkey, topic in data["topics"].items():
        if topic_filter and tkey not in topic_filter:
            continue
        scene_map = scenes_by_section(topic)
        combos = list(itertools.product(
            topic["hooks"], topic["contexts"], topic["bodies"], topic["ctas"]))
        rnd.shuffle(combos)
        if not take_all:
            combos = combos[:max_per_topic]
        for hook, ctx, body, cta in combos:
            n += 1
            imgs = pick_images(scene_map, rnd)
            videos.append({
                "video_id": f"VIDEO_{n:04d}",
                "topic": tkey,
                "topic_name": topic["name"],
                "duration_hint": data["_meta"].get("duration_hint", "20-35s"),
                "hook": hook, "context": ctx, "body": body, "cta": cta,
                "images": imgs,
            })
    return videos


def write_videos_csv(videos):
    path = os.path.join(OUT, "videos.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["video_id", "topic", "hook_id", "context_id", "body_id",
                    "cta_id", "image_ids", "duration_hint"])
        for v in videos:
            w.writerow([v["video_id"], v["topic"], v["hook"]["id"],
                        v["context"]["id"], v["body"]["id"], v["cta"]["id"],
                        " | ".join(i["id"] for i in v["images"]),
                        v["duration_hint"]])
    return path


def write_videos_jsonl(videos):
    path = os.path.join(OUT, "videos.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for v in videos:
            obj = {
                "video_id": v["video_id"], "topic": v["topic"],
                "topic_name": v["topic_name"], "duration_hint": v["duration_hint"],
                "script": {
                    "HOOK": {"id": v["hook"]["id"], "text": v["hook"]["text"]},
                    "CONTEXT": {"id": v["context"]["id"], "text": v["context"]["text"]},
                    "BODY": {"id": v["body"]["id"], "text": v["body"]["text"]},
                    "CTA": {"id": v["cta"]["id"], "text": v["cta"]["text"]},
                },
                "images": [{"id": i["id"], "section": i["section"],
                            "title": i["title"], "prompt": i["prompt"]}
                           for i in v["images"]],
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    return path


def write_preview(videos, limit=12):
    path = os.path.join(OUT, "scripts_preview.md")
    lines = ["# Vista previa de guiones\n",
             f"Mostrando {min(limit, len(videos))} de {len(videos)} videos.\n"]
    for v in videos[:limit]:
        lines.append(f"\n---\n\n## {v['video_id']} — {v['topic']} ({v['duration_hint']})\n")
        lines.append(f"- **HOOK** `{v['hook']['id']}`: {v['hook']['text']}")
        lines.append(f"- **CONTEXT** `{v['context']['id']}`: {v['context']['text']}")
        lines.append(f"- **BODY** `{v['body']['id']}`: {v['body']['text']}")
        lines.append(f"- **CTA** `{v['cta']['id']}`: {v['cta']['text']}")
        lines.append(f"- **IMÁGENES**: {', '.join(i['id'] for i in v['images'])}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def write_image_master(data, topic_filter):
    path = os.path.join(OUT, "image_master_list.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image_id", "topic", "section", "title", "prompt", "variant"])
        for tkey, topic in data["topics"].items():
            if topic_filter and tkey not in topic_filter:
                continue
            for sc in topic.get("scenes", []):
                w.writerow([sc["id"], tkey, sc["section"], sc["title"],
                            sc["prompt"], sc.get("variant", "")])
    return path


def write_perf_template(videos):
    path = os.path.join(OUT, "performance_template.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["video_id", "plays", "avg_watch_pct", "likes", "shares",
                    "comments", "profile_visits", "signups", "score"])
        for v in videos:
            w.writerow([v["video_id"], "", "", "", "", "", "", "", ""])
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-per-topic", type=int, default=12)
    ap.add_argument("--all", action="store_true", help="todas las combinaciones")
    ap.add_argument("--topics", nargs="*", default=None)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    data = load()
    tf = set(args.topics) if args.topics else None
    videos = build(data, tf, args.max_per_topic, args.all, args.seed)

    p1 = write_videos_csv(videos)
    p2 = write_videos_jsonl(videos)
    p3 = write_preview(videos)
    p4 = write_image_master(data, tf)
    p5 = write_perf_template(videos)

    topics_used = sorted({v["topic"] for v in videos})
    print(f"OK — {len(videos)} videos generados en {len(topics_used)} topics: {', '.join(topics_used)}")
    for p in (p1, p2, p3, p4, p5):
        print("  ->", os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()
