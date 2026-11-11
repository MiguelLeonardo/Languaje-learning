"""Scripted open conversation: the AI follows the scenario script, the learner may use suggested lines
or their own words (lenient semantic matching)."""

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.content.schema import Scenario
from app.db.models import RoleplaySession
from app.llm.base import LLMProvider, RoleplayContext
from app.services.evaluation import evaluate, similarity
from app.services.feedback import Feedback, build_feedback

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
    feedback: Feedback | None = None
    average_score: float | None = None


def _advance_ai(scenario: Scenario, index: int) -> tuple[list[str], int]:
    """Collect consecutive AI lines starting at index; return them and the next user-turn index (or len)."""
    turns, lines = scenario.roleplay.turns, []
    while index < len(turns) and turns[index].speaker == "ai":
        lines.append(turns[index].text or "")
        index += 1
    return lines, index


def _state(session: RoleplaySession, scenario: Scenario, ai_messages: list[str], **extra) -> RoleplayState:
    turns = scenario.roleplay.turns
    pending = None
    if session.status == "active" and session.turn_index < len(turns):
        t = turns[session.turn_index]
        pending = PendingTurn(goal=t.goal or "", suggested_lines=t.suggested_lines)
    avg = round(sum(session.scores) / len(session.scores), 3) if session.scores else None
    return RoleplayState(session_id=session.id, scenario_id=scenario.id, status=session.status,
                         ai_messages=ai_messages, pending_turn=pending, history=list(session.history),
                         average_score=avg, **extra)


def start(db: Session, user_id: str, scenario: Scenario) -> RoleplayState:
    lines, idx = _advance_ai(scenario, 0)
    session = RoleplaySession(user_id=user_id, scenario_id=scenario.id, turn_index=idx,
                              status="active" if idx < len(scenario.roleplay.turns) else "completed",
                              history=[{"speaker": "ai", "text": t} for t in lines], scores=[])
    db.add(session)
    db.commit()
    return _state(session, scenario, lines)


async def submit(db: Session, session: RoleplaySession, scenario: Scenario, utterance: str,
                 llm: LLMProvider) -> RoleplayState:
    turns = scenario.roleplay.turns
    turn = turns[session.turn_index]
    best_line = max(turn.suggested_lines, key=lambda line: similarity(utterance, line))
    best = similarity(utterance, best_line)
    ev = evaluate(best_line, utterance, threshold=ROLEPLAY_THRESHOLD)
    fb = build_feedback(ev)
    if best < ROLEPLAY_THRESHOLD:
        fb.message_es = "Intenta de nuevo. Puedes usar una de las frases sugeridas."
        return _state(session, scenario, [], last_score=round(best, 3), accepted=False, feedback=fb)

    history = list(session.history) + [{"speaker": "user", "text": utterance}]
    next_idx = session.turn_index + 1
    scripted, after = _advance_ai(scenario, next_idx)
    ai_messages: list[str] = []
    if scripted:
        ctx = RoleplayContext(
            scenario_title=scenario.title, cefr=scenario.cefr.value, setting=scenario.roleplay.setting,
            ai_role=scenario.roleplay.ai_role, user_role=scenario.roleplay.user_role, history=session.history,
            user_utterance=utterance, next_scripted_line=scripted[0])
        ai_messages = [await llm.roleplay_reply(ctx), *scripted[1:]]
    history += [{"speaker": "ai", "text": m} for m in ai_messages]
    session.history = history
    session.scores = list(session.scores) + [round(best, 3)]
    session.turn_index = after
    if after >= len(turns):
        session.status = "completed"
    db.commit()
    return _state(session, scenario, ai_messages, last_score=round(best, 3), accepted=True, feedback=fb)
