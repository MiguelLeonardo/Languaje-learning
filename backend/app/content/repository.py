"""Loads and indexes curriculum YAML files."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from app.content.schema import CEFR, Phrase, Scenario


class ContentRepository:
    def __init__(self, scenarios: list[Scenario]):
        self._scenarios = {s.id: s for s in scenarios}
        if len(self._scenarios) != len(scenarios):
            raise ValueError("duplicate scenario ids")

    @classmethod
    def from_dir(cls, path: Path) -> ContentRepository:
        scenarios = []
        for file in sorted(path.glob("*.yaml")):
            data = yaml.safe_load(file.read_text(encoding="utf-8"))
            scenarios.append(Scenario.model_validate(data))
        return cls(scenarios)

    def list(self, cefr: CEFR | None = None, band: str | None = None) -> list[Scenario]:
        items = list(self._scenarios.values())
        if cefr:
            items = [s for s in items if s.cefr == cefr]
        if band:
            items = [s for s in items if s.cefr.band == band]
        return sorted(items, key=lambda s: (s.cefr.value, s.id))

    def get(self, scenario_id: str) -> Scenario | None:
        return self._scenarios.get(scenario_id)

    def phrase(self, scenario_id: str, phrase_id: str) -> Phrase | None:
        s = self.get(scenario_id)
        return next((p for p in s.phrases if p.id == phrase_id), None) if s else None

    def common_phrases(self, cefr: CEFR | None = None) -> list[tuple[Scenario, Phrase]]:
        return [(s, p) for s in self.list(cefr) for p in s.phrases if p.common]


@lru_cache
def get_repository() -> ContentRepository:
    from app.core.config import get_settings

    return ContentRepository.from_dir(get_settings().content_dir)
