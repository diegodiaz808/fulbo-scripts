#!/usr/bin/env python3
"""
Fulbo Script Bot — Motor de patrones ganadores.

Cruza los videos generados (output/videos.jsonl) con sus metricas
(output/performance.csv) y detecta que ASSETS rinden mejor:
  - Ranking de cada hook / context / body / cta / imagen por score promedio
  - Co-ocurrencias entre los videos top (que combinaciones se repiten)

Cargas tus metricas en output/performance.csv (usa performance_template.csv como base).
La columna que manda es 'score' (poné el KPI que te importe: signups, retencion, etc.).

Uso:
  python3 analyze.py                 # usa output/performance.csv
  python3 analyze.py --demo          # genera metricas random para ver el motor funcionando
  python3 analyze.py --top-pct 0.25  # define que % cuenta como "ganador" (default 0.30)
"""
import argparse, csv, json, os, random
from collections import defaultdict
from itertools import combinations

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output")
VIDEOS = os.path.join(OUT, "videos.jsonl")
PERF = os.path.join(OUT, "performance.csv")
ASSET_KEYS = ["HOOK", "CONTEXT", "BODY", "CTA"]


def load_videos():
    vids = {}
    with open(VIDEOS, encoding="utf-8") as f:
        for line in f:
            v = json.loads(line)
            vids[v["video_id"]] = v
    return vids


def load_perf(demo, vids):
    scores = {}
    if demo:
        rnd = random.Random(7)
        # patron oculto: ciertos assets "buenos" suben el score, para validar el motor
        good = {"AI_MANAGER_HOOK_B", "MARKET_HOOK_A", "AI_MANAGER_BODY_C",
                "RARITY_BODY_A", "PRESALE_BETA_CTA_A"}
        for vid, v in vids.items():
            base = rnd.uniform(20, 60)
            used = {v["script"][k]["id"] for k in ASSET_KEYS}
            base += 25 * len(used & good)
            scores[vid] = round(base + rnd.uniform(-5, 5), 1)
        return scores
    if not os.path.exists(PERF):
        raise SystemExit(f"No existe {PERF}. Cargá métricas o corré con --demo.")
    with open(PERF, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            s = row.get("score", "").strip()
            if s:
                scores[row["video_id"]] = float(s)
    if not scores:
        raise SystemExit("performance.csv no tiene ningún 'score' cargado.")
    return scores


def asset_usage(vids):
    """video_id -> dict(asset_type -> asset_id), incluyendo imagenes."""
    out = {}
    for vid, v in vids.items():
        u = {k: v["script"][k]["id"] for k in ASSET_KEYS}
        u["IMAGES"] = [i["id"] for i in v["images"]]
        out[vid] = u
    return out


def rank_assets(usage, scores):
    agg = defaultdict(lambda: defaultdict(list))  # type -> id -> [scores]
    for vid, u in usage.items():
        if vid not in scores:
            continue
        for k in ASSET_KEYS:
            agg[k][u[k]].append(scores[vid])
        for img in u["IMAGES"]:
            agg["IMAGE"][img].append(scores[vid])
    ranked = {}
    for typ, d in agg.items():
        rows = [(aid, sum(v) / len(v), len(v)) for aid, v in d.items()]
        rows.sort(key=lambda r: r[1], reverse=True)
        ranked[typ] = rows
    return ranked


def cooccurrence(usage, scores, top_pct):
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    n_top = max(2, int(len(ordered) * top_pct))
    winners = [vid for vid, _ in ordered[:n_top]]
    pair = defaultdict(int)
    for vid in winners:
        assets = [usage[vid][k] for k in ASSET_KEYS]
        for a, b in combinations(sorted(assets), 2):
            pair[(a, b)] += 1
    pairs = sorted(pair.items(), key=lambda kv: kv[1], reverse=True)
    return n_top, pairs


def report(ranked, n_top, pairs, top_pct):
    lines = ["# Reporte de assets ganadores\n",
             f"Top {int(top_pct*100)}% = {n_top} videos.\n"]
    for typ in ASSET_KEYS + ["IMAGE"]:
        lines.append(f"\n## {typ} (ranking por score promedio)\n")
        lines.append("| asset_id | score prom | usos |")
        lines.append("|---|---:|---:|")
        for aid, avg, cnt in ranked.get(typ, [])[:8]:
            lines.append(f"| {aid} | {avg:.1f} | {cnt} |")
    lines.append("\n## Combinaciones más frecuentes entre ganadores\n")
    lines.append("| asset A | asset B | veces juntas en el top |")
    lines.append("|---|---|---:|")
    for (a, b), c in pairs[:12]:
        if c >= 2:
            lines.append(f"| {a} | {b} | {c} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--top-pct", type=float, default=0.30)
    args = ap.parse_args()

    vids = load_videos()
    scores = load_perf(args.demo, vids)
    usage = asset_usage(vids)
    ranked = rank_assets(usage, scores)
    n_top, pairs = cooccurrence(usage, scores, args.top_pct)
    rep = report(ranked, n_top, pairs, args.top_pct)

    path = os.path.join(OUT, "winners_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(rep)
    print(rep)
    print("-> escrito en", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
