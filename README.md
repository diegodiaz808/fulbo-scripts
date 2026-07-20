# Fulbo Script Bot

Script generator for vertical videos (TikTok / Reels / Shorts) promoting [fulbo.fun](https://fulbo.fun). It doesn't render video — it produces reusable, combinable, measurable **scripts** that the video bot consumes downstream.

> Docs in Spanish: [README.es.md](README.es.md)

## Concept

Every video follows a fixed narrative structure — `HOOK → CONTEXT → BODY → CTA` — where the CONTEXT beat always explains what Fulbo is. The generator assembles scripts from a curated content pool (`fulbo_context.md`), tracks which combinations were already produced, and exports CSV/JSONL manifests so performance per script can be measured later.

## Usage

```bash
python generate.py    # produce new scripts
python analyze.py     # analyze performance data
```

Outputs land in `output/` (git-ignored): script previews in Markdown plus CSV/JSONL manifests for the production pipeline.

## Stack

Python · content templating · CSV/JSONL pipelines
