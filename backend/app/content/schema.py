"""Curriculum schema (content-as-code). Every YAML file in content/scenarios must validate."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class CEFR(StrEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

    @property
    def band(self) -> str:
        return {"A": "basic", "B": "intermediate", "C": "advanced"}[self.value[0]]


class GlossaryEntry(BaseModel):
    word: str
    meaning: str  # explanation in Spanish
    ipa: str | None = None


SLUG = r"^[a-z0-9][a-z0-9-]*$"


class Phrase(BaseModel):
    id: str = Field(pattern=SLUG)
    text: str
    translation: str
    glossary: list[GlossaryEntry] = Field(default_factory=list)
    visual_hint: str = ""  # emoji or image description/URL
    cloze: list[int] = Field(default_factory=list, description="word indexes hidden in completion stage")
    common: bool = True  # belongs to the "common phrases" bank

    @model_validator(mode="after")
    def _cloze_in_range(self) -> "Phrase":
        n = len(self.text.split())
        if any(i < 0 or i >= n for i in self.cloze):
            raise ValueError(f"phrase {self.id}: cloze index out of range (0..{n - 1})")
        return self


class RoleplayTurn(BaseModel):
    speaker: str  # "ai" | "user"
    text: str | None = None  # ai line
    goal: str | None = None  # what the user must accomplish
    suggested_lines: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _shape(self) -> "RoleplayTurn":
        if self.speaker == "ai" and not self.text:
            raise ValueError("ai turns need text")
        if self.speaker == "user" and (not self.goal or not self.suggested_lines):
            raise ValueError("user turns need goal and suggested_lines")
        if self.speaker not in ("ai", "user"):
            raise ValueError("speaker must be 'ai' or 'user'")
        return self


class Roleplay(BaseModel):
    ai_role: str
    user_role: str
    setting: str
    turns: list[RoleplayTurn]


class Scenario(BaseModel):
    id: str = Field(pattern=SLUG)
    title: str
    title_es: str
    cefr: CEFR
    topic: str
    description: str
    phrases: list[Phrase] = Field(min_length=1)
    roleplay: Roleplay

    @model_validator(mode="after")
    def _unique_phrase_ids(self) -> "Scenario":
        ids = [p.id for p in self.phrases]
        if len(ids) != len(set(ids)):
            raise ValueError(f"scenario {self.id}: duplicate phrase ids")
        return self
