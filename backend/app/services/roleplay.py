"""Scripted + Free-form AI conversation (Stage 5 of every lesson):
The AI follows the scenario script, while the learner can either speak one of the suggested script lines
OR improvise freely in their own words around the turn's mission and scenario vocabulary."""

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.content.schema import Scenario
from app.db.models import RoleplaySession
from app.llm.base import LLMProvider, RoleplayContext
from app.services.evaluation import evaluate, similarity
from app.services.feedback import Feedback, build_feedback
from app.services.text import normalize_words

ROLEPLAY_THRESHOLD = 0.6


class PendingTurn(BaseModel):
    goal: str
    suggested_lines: list[str]


class RoleplayState(BaseModel):
    session_id: str
    scenario_id: str
    status: str
    ai_messages: list[str]
    pending_turn: PendingTurn | None
    history: list[dict]
    last_score: float | None = None
    accepted: bool | None = None
    response_style: str | None = None  # "scripted" | "freeform"
    natural_alternative: str | None = None
    target_phrases: list[str] = []
    used_lesson_phrases: list[str] = []
    feedback: Feedback | None = None
    average_score: float | None = None


def _advance_ai(scenario: Scenario, index: int) -> tuple[list[str], int]:
    """Collect consecutive AI lines starting at index; return them and the next user-turn index (or len)."""
    turns, lines = scenario.roleplay.turns, []
    while index < len(turns) and turns[index].speaker == "ai":
        lines.append(turns[index].text or "")
        index += 1
    return lines, index


def _detect_used_phrases(scenario: Scenario, history: list[dict]) -> list[str]:
    user_text = " ".join(h.get("text", "") for h in history if h.get("speaker") == "user")
    used = []
    for p in scenario.phrases:
        if similarity(user_text, p.text) >= 0.45 or all(
            w in normalize_words(user_text) for w in normalize_words(p.text)[:3]
        ):
            used.append(p.text)
    return used


def _is_relevant_freeform(utterance: str, suggested_lines: list[str], scenario: Scenario) -> bool:
    words = normalize_words(utterance)
    if len(words) < 3:
        return False
    vocab = set()
    for line in suggested_lines:
        vocab.update(normalize_words(line))
    for p in scenario.phrases:
        vocab.update(normalize_words(p.text))
    stopwords = {"the", "a", "an", "to", "is", "are", "in", "on", "at", "of", "for", "and", "or", "it"}
    meaningful = (vocab - stopwords) & set(words)
    return len(meaningful) >= 1


def _state(session: RoleplaySession, scenario: Scenario, ai_messages: list[str], **extra) -> RoleplayState:
    turns = scenario.roleplay.turns
    pending = None
    if session.status == "active" and session.turn_index < len(turns):
        t = turns[session.turn_index]
        pending = PendingTurn(goal=t.goal or "", suggested_lines=t.suggested_lines)
    avg = round(sum(session.scores) / len(session.scores), 3) if session.scores else None
    return RoleplayState(
        session_id=session.id,
        scenario_id=scenario.id,
        status=session.status,
        ai_messages=ai_messages,
        pending_turn=pending,
        history=list(session.history),
        target_phrases=[p.text for p in scenario.phrases],
        used_lesson_phrases=_detect_used_phrases(scenario, list(session.history)),
        average_score=avg,
        **extra,
    )


def start(db: Session, user_id: str, scenario: Scenario) -> RoleplayState:
    lines, idx = _advance_ai(scenario, 0)
    session = RoleplaySession(
        user_id=user_id,
        scenario_id=scenario.id,
        turn_index=idx,
        status="active" if idx < len(scenario.roleplay.turns) else "completed",
        history=[{"speaker": "ai", "text": t} for t in lines],
        scores=[],
    )
    db.add(session)
    db.commit()
    return _state(session, scenario, lines)


async def submit(
    db: Session, session: RoleplaySession, scenario: Scenario, utterance: str, llm: LLMProvider
) -> RoleplayState:
    turns = scenario.roleplay.turns
    turn = turns[session.turn_index]
    best_line = max(turn.suggested_lines, key=lambda line: similarity(utterance, line))
    best = similarity(utterance, best_line)
    ev = evaluate(best_line, utterance, threshold=ROLEPLAY_THRESHOLD)
    fb = build_feedback(ev)

    is_scripted = best >= ROLEPLAY_THRESHOLD
    is_freeform = not is_scripted and _is_relevant_freeform(utterance, turn.suggested_lines, scenario)

    if not is_scripted and not is_freeform:
        fb.message_es = "Intenta de nuevo. Puedes leer una línea del libreto o improvisar sobre el objetivo del turno."
        return _state(session, scenario, [], last_score=round(best, 3), accepted=False, feedback=fb)

    style = "scripted" if is_scripted else "freeform"
    turn_score = round(best if is_scripted else max(0.78, best), 3)
    if is_freeform:
        fb.level = "good"
        fb.message_es = f"¡Respuesta libre aceptada! Otra forma según el libreto: «{best_line}»."

    history = list(session.history) + [{"speaker": "user", "text": utterance}]
    next_idx = session.turn_index + 1
    scripted, after = _advance_ai(scenario, next_idx)
    ai_messages: list[str] = []
    if scripted:
        ctx = RoleplayContext(
            scenario_title=scenario.title,
            cefr=scenario.cefr.value,
            setting=scenario.roleplay.setting,
            ai_role=scenario.roleplay.ai_role,
            user_role=scenario.roleplay.user_role,
            history=session.history,
            user_utterance=utterance,
            next_scripted_line=scripted[0],
        )
        ai_messages = [await llm.roleplay_reply(ctx), *scripted[1:]]
    history += [{"speaker": "ai", "text": m} for m in ai_messages]
    session.history = history
    session.scores = list(session.scores) + [turn_score]
    session.turn_index = after
    if after >= len(turns):
        session.status = "completed"
    db.commit()
    return _state(
        session,
        scenario,
        ai_messages,
        last_score=turn_score,
        accepted=True,
        response_style=style,
        natural_alternative=best_line,
        feedback=fb,
    )

