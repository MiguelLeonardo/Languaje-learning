"""Builds exercises with decreasing visual support from curriculum content.

Stages (Speak-like progression, all answered by voice):
  shadowing   -> listen & repeat with full text + audio (main input exercise)
  recall      -> FULL support: text, translation, glossary, visual hint
  guided      -> PARTIAL support: translation + first-letter hints, visual hint
  completion  -> LOW support: sentence with blanks, no translation
  roleplay    -> SCRIPT support: open AI chat with suggested lines (see roleplay.py)
"""

from enum import StrEnum

from pydantic import BaseModel

from app.content.repository import ContentRepository
from app.content.schema import GlossaryEntry, Phrase, Scenario


class ExerciseType(StrEnum):
    SHADOWING = "shadowing"
    RECALL = "recall"
    GUIDED = "guided"
    COMPLETION = "completion"


class SupportLevel(StrEnum):
    FULL = "full"
    PARTIAL = "partial"
    LOW = "low"


STAGE_CONFIG: dict[ExerciseType, tuple[SupportLevel, float, str]] = {
    ExerciseType.SHADOWING: (SupportLevel.FULL, 0.70, "Escucha y repite la frase imitando el ritmo y la entonación."),
    ExerciseType.RECALL: (SupportLevel.FULL, 0.75, "Lee la frase en voz alta. Revisa las palabras clave."),
    ExerciseType.GUIDED: (SupportLevel.PARTIAL, 0.80, "Di la frase en inglés usando las pistas."),
    ExerciseType.COMPLETION: (SupportLevel.LOW, 0.85, "Completa la frase diciéndola completa en voz alta."),
}
LESSON_ORDER = [ExerciseType.SHADOWING, ExerciseType.RECALL, ExerciseType.GUIDED, ExerciseType.COMPLETION]


class ExercisePrompt(BaseModel):
    instruction_es: str
    display_text: str | None = None
    translation: str | None = None
    glossary: list[GlossaryEntry] = []
    visual_hint: str | None = None
    audio_text: str | None = None  # text the client sends to TTS for model audio
    focus_words: list[str] = []


class Exercise(BaseModel):
    id: str
    type: ExerciseType
    support: SupportLevel
    scenario_id: str
    phrase_id: str
    prompt: ExercisePrompt
    expected_text: str
    pass_threshold: float
    response_mode: str = "speech"  # every exercise is answered with the microphone


def exercise_id(scenario_id: str, phrase_id: str, kind: ExerciseType) -> str:
    return f"{scenario_id}.{phrase_id}.{kind.value}"


def _first_letter_hint(text: str) -> str:
    out = []
    for w in text.split():
        core = w.rstrip(".,!?")
        tail = w[len(core):]
        out.append((core[0] + "_" * (len(core) - 1) if len(core) > 1 else core) + tail)
    return " ".join(out)


def _cloze(phrase: Phrase) -> str:
    words = phrase.text.split()
    idx = set(phrase.cloze) or {len(words) // 2}
    return " ".join("____" if i in idx else w for i, w in enumerate(words))


def build_exercise(
    scenario: Scenario, phrase: Phrase, kind: ExerciseType, focus_words: list[str] | None = None
) -> Exercise:
    support, threshold, instruction = STAGE_CONFIG[kind]
    if kind == ExerciseType.SHADOWING:
        prompt = ExercisePrompt(instruction_es=instruction, display_text=phrase.text, translation=phrase.translation,
                                visual_hint=phrase.visual_hint, audio_text=phrase.text)
    elif kind == ExerciseType.RECALL:
        prompt = ExercisePrompt(instruction_es=instruction, display_text=phrase.text, translation=phrase.translation,
                                glossary=phrase.glossary, visual_hint=phrase.visual_hint, audio_text=phrase.text)
    elif kind == ExerciseType.GUIDED:
        prompt = ExercisePrompt(instruction_es=instruction, display_text=_first_letter_hint(phrase.text),
                                translation=phrase.translation, visual_hint=phrase.visual_hint)
    else:
        prompt = ExercisePrompt(instruction_es=instruction, display_text=_cloze(phrase))
    if focus_words:
        prompt.focus_words = focus_words
    return Exercise(
        id=exercise_id(scenario.id, phrase.id, kind), type=kind, support=support, scenario_id=scenario.id,
        phrase_id=phrase.id, prompt=prompt, expected_text=phrase.text, pass_threshold=threshold,
    )


def resolve_exercise(repo: ContentRepository, ex_id: str) -> Exercise | None:
    parts = ex_id.split(".")
    if len(parts) != 3:
        return None
    scenario_id, phrase_id, kind = parts
    try:
        ex_type = ExerciseType(kind)
    except ValueError:
        return None
    scenario = repo.get(scenario_id)
    phrase = repo.phrase(scenario_id, phrase_id)
    if not scenario or not phrase:
        return None
    return build_exercise(scenario, phrase, ex_type)


class LessonStage(BaseModel):
    type: ExerciseType
    support: SupportLevel
    exercises: list[Exercise]


class RoleplayScriptOverview(BaseModel):
    ai_role: str
    user_role: str
    setting: str
    target_phrases: list[str]
    user_missions: list[str]


class LessonPlan(BaseModel):
    scenario_id: str
    title: str
    cefr: str
    stages: list[LessonStage]
    roleplay_available: bool = True
    roleplay_script: RoleplayScriptOverview | None = None


def build_lesson(scenario: Scenario) -> LessonPlan:
    stages = [
        LessonStage(type=k, support=STAGE_CONFIG[k][0],
                    exercises=[build_exercise(scenario, p, k) for p in scenario.phrases])
        for k in LESSON_ORDER
    ]
    script = RoleplayScriptOverview(
        ai_role=scenario.roleplay.ai_role,
        user_role=scenario.roleplay.user_role,
        setting=scenario.roleplay.setting,
        target_phrases=[p.text for p in scenario.phrases],
        user_missions=[t.goal for t in scenario.roleplay.turns if t.speaker == "user" and t.goal],
    )
    return LessonPlan(
        scenario_id=scenario.id, title=scenario.title, cefr=scenario.cefr.value,
        stages=stages, roleplay_script=script,
    )

