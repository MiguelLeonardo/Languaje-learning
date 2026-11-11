"""Compares what the learner said with the expected sentence (word-level alignment)."""

from difflib import SequenceMatcher
from enum import StrEnum

from pydantic import BaseModel

from app.services.text import normalize_words


class WordStatus(StrEnum):
    CORRECT = "correct"
    MISPRONOUNCED = "mispronounced"  # substituted by a different word
    MISSING = "missing"
    EXTRA = "extra"


class WordResult(BaseModel):
    expected: str | None
    heard: str | None
    status: WordStatus


class Evaluation(BaseModel):
    expected_text: str
    transcript: str
    accuracy: float  # share of expected words said correctly
    fluency: float  # penalises extra/garbage words
    confidence: float | None  # provider pronunciation confidence (0..1) if available
    score: float
    passed: bool
    words: list[WordResult]

    @property
    def problem_words(self) -> list[str]:
        return [w.expected for w in self.words if w.expected and w.status != WordStatus.CORRECT]


def evaluate(expected_text: str, transcript: str, threshold: float, confidence: float | None = None) -> Evaluation:
    exp = normalize_words(expected_text)
    got = normalize_words(transcript)
    words: list[WordResult] = []
    for op, i1, i2, j1, j2 in SequenceMatcher(a=exp, b=got, autojunk=False).get_opcodes():
        if op == "equal":
            words += [WordResult(expected=exp[i], heard=exp[i], status=WordStatus.CORRECT) for i in range(i1, i2)]
        elif op == "delete":
            words += [WordResult(expected=exp[i], heard=None, status=WordStatus.MISSING) for i in range(i1, i2)]
        elif op == "insert":
            words += [WordResult(expected=None, heard=got[j], status=WordStatus.EXTRA) for j in range(j1, j2)]
        else:  # replace
            a, b = exp[i1:i2], got[j1:j2]
            for k in range(max(len(a), len(b))):
                e = a[k] if k < len(a) else None
                h = b[k] if k < len(b) else None
                status = WordStatus.MISPRONOUNCED if e and h else (WordStatus.MISSING if e else WordStatus.EXTRA)
                words.append(WordResult(expected=e, heard=h, status=status))

    correct = sum(w.status == WordStatus.CORRECT for w in words)
    extra = sum(w.status == WordStatus.EXTRA for w in words)
    accuracy = correct / len(exp) if exp else 0.0
    fluency = max(0.0, 1.0 - extra / max(len(exp), 1)) if got else 0.0
    score = 0.8 * accuracy + 0.2 * fluency
    if confidence is not None:
        score = 0.7 * accuracy + 0.1 * fluency + 0.2 * confidence
    score = round(min(1.0, score), 3)
    return Evaluation(
        expected_text=expected_text, transcript=transcript, accuracy=round(accuracy, 3),
        fluency=round(fluency, 3), confidence=confidence, score=score,
        passed=score >= threshold, words=words,
    )


def similarity(a: str, b: str) -> float:
    """Order-aware word similarity used for open (scripted) roleplay answers."""
    wa, wb = normalize_words(a), normalize_words(b)
    if not wa or not wb:
        return 0.0
    return SequenceMatcher(a=wa, b=wb, autojunk=False).ratio()
