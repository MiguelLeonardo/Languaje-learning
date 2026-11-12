"""Merge content/idioms/*.json into content/scenarios/*.yaml (idempotent) and resync FALLBACK_SCENARIOS."""

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = ROOT / "content" / "scenarios"
IDIOMS_DIR = ROOT / "content" / "idioms"
STATIC_INDEX = ROOT / "backend" / "app" / "static" / "index.html"


def compute_cloze(text: str) -> list[int]:
    n = len(text.split())
    if n <= 4:
        return [max(0, n - 2)]
    return sorted({min(n - 1, max(1, n // 3)), min(n - 1, max(2, (2 * n) // 3))})


def main() -> None:
    merged = 0
    for f in sorted(IDIOMS_DIR.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for scenario_id, entries in data.items():
            path = SCENARIOS_DIR / f"{scenario_id}.yaml"
            sc = yaml.safe_load(path.read_text(encoding="utf-8"))
            sc["phrases"] = [p for p in sc["phrases"] if p.get("kind", "phrase") == "phrase"]
            for e in entries:
                sc["phrases"].append({
                    "id": re.sub(r"[^a-z0-9-]+", "-", e["id"].lower()).strip("-"),
                    "text": e["text"],
                    "translation": e["translation"],
                    "visual_hint": e.get("visual_hint", ""),
                    "cloze": compute_cloze(e["text"]),
                    "glossary": [{"word": e["glossary_word"], "meaning": e["glossary_meaning"],
                                  "ipa": e.get("glossary_ipa", "")}],
                    "kind": e.get("kind", "idiom"),
                    "apply_sentence": e["apply_sentence"],
                    "apply_answer": e["apply_answer"],
                    "apply_translation": e["apply_translation"],
                })
                merged += 1
            path.write_text(yaml.safe_dump(sc, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")

    sys.path.insert(0, str(ROOT / "backend"))
    from app.content.repository import get_repository

    get_repository.cache_clear()
    scenarios = get_repository().list()
    fallback = []
    for s in scenarios:
        d = s.model_dump(mode="json")
        d["band"] = s.cefr.band
        fallback.append(d)
    html = STATIC_INDEX.read_text(encoding="utf-8")
    pattern = re.compile(r"const FALLBACK_SCENARIOS = \[.*?\n    \];|const FALLBACK_SCENARIOS = \[.*?\];", re.DOTALL)
    new_html, count = pattern.subn(lambda _: "const FALLBACK_SCENARIOS = " + json.dumps(fallback, ensure_ascii=False, indent=6) + ";", html, count=1)
    assert count == 1
    STATIC_INDEX.write_text(new_html, encoding="utf-8")
    print(f"Merged {merged} idiom entries; {len(scenarios)} scenarios; "
          f"{sum(len(s.phrases) for s in scenarios)} phrases; fallback synced")


if __name__ == "__main__":
    main()
