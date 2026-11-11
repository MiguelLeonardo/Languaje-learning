"""Spaced repetition (SM-2 variant) driven by speech scores.

Two kinds of cards are tracked per user:
  * phrase   -> every phrase practised in a lesson
  * feedback -> the specific words the learner struggled with (from Feedback.focus_words)
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

MIN_EASE = 1.3


def score_to_quality(score: float, threshold: float) -> int:
    if score >= 0.95:
        return 5
    if score >= 0.85:
        return 4
    if score >= threshold:
        return 3
    if score >= 0.5:
        return 2
    if score >= 0.3:
        return 1
    return 0


@dataclass
class SrsState:
    ease: float = 2.5
    interval_days: float = 0.0
    repetitions: int = 0
    lapses: int = 0


def schedule(state: SrsState, quality: int, now: datetime | None = None) -> tuple[SrsState, datetime]:
    now = now or datetime.now(UTC)
    ease = max(MIN_EASE, state.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    if quality < 3:
        new = SrsState(ease=ease, interval_days=10 / (24 * 60), repetitions=0, lapses=state.lapses + 1)  # 10 min
    else:
        reps = state.repetitions + 1
        interval = 1.0 if reps == 1 else 3.0 if reps == 2 else round(state.interval_days * ease, 2)
        new = SrsState(ease=ease, interval_days=interval, repetitions=reps, lapses=state.lapses)
    return new, now + timedelta(days=new.interval_days)
