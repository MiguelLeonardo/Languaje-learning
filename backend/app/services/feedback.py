"""Turns an Evaluation into learner-facing feedback (Spanish UI, English targets)."""

from pydantic import BaseModel

from app.content.schema import Phrase
from app.services.evaluation import Evaluation, WordStatus


class Tip(BaseModel):
    word: str
    issue: str
    advice: str


class Feedback(BaseModel):
    level: str  # excellent | good | retry
    message_es: str
    tips: list[Tip]
    focus_words: list[str]
    model_answer: str


def build_feedback(evaluation: Evaluation, phrase: Phrase | None = None) -> Feedback:
    glossary = {g.word.lower(): g for g in (phrase.glossary if phrase else [])}
    tips: list[Tip] = []
    for w in evaluation.words:
        if w.status == WordStatus.MISSING and w.expected:
            extra = f" ({glossary[w.expected].meaning})" if w.expected in glossary else ""
            tips.append(Tip(word=w.expected, issue="missing",
                            advice=f"No escuchamos '{w.expected}'{extra}. Dila con claridad."))
        elif w.status == WordStatus.MISPRONOUNCED and w.expected:
            ipa = glossary[w.expected].ipa if w.expected in glossary and glossary[w.expected].ipa else None
            hint = f" Pronunciación: /{ipa}/." if ipa else ""
            tips.append(Tip(word=w.expected, issue="mispronounced",
                            advice=f"Escuchamos '{w.heard}' en lugar de '{w.expected}'.{hint}"))
    extras = [w.heard for w in evaluation.words if w.status == WordStatus.EXTRA and w.heard]
    if extras:
        tips.append(Tip(word=" ".join(extras), issue="extra", advice="Intenta no añadir palabras de relleno."))

    if evaluation.score >= 0.95:
        level, msg = "excellent", "¡Excelente! Suenas muy natural."
    elif evaluation.passed:
        level, msg = "good", "¡Bien hecho! Pulamos algunos detalles."
    else:
        level, msg = "retry", "Casi. Escucha el modelo y vuelve a intentarlo."
    return Feedback(level=level, message_es=msg, tips=tips, focus_words=evaluation.problem_words,
                    model_answer=evaluation.expected_text)
