from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import RepoDep
from app.content.repository import ContentRepository
from app.content.schema import CEFR, Scenario
from app.core.security import get_current_user
from app.services.exercises import (
    Exercise,
    ExerciseType,
    LessonPlan,
    build_exercise,
    build_lesson,
    resolve_exercise,
)

router = APIRouter(prefix="/v1", tags=["catalog"], dependencies=[Depends(get_current_user)])


class LevelOut(BaseModel):
    cefr: CEFR
    band: str
    scenarios: int


class ScenarioSummary(BaseModel):
    id: str
    title: str
    title_es: str
    cefr: CEFR
    band: str
    topic: str
    description: str
    phrases: int


def _summary(s: Scenario) -> ScenarioSummary:
    return ScenarioSummary(id=s.id, title=s.title, title_es=s.title_es, cefr=s.cefr, band=s.cefr.band,
                           topic=s.topic, description=s.description, phrases=len(s.phrases))


@router.get("/levels", response_model=list[LevelOut])
def levels(repo: ContentRepository = RepoDep):
    return [LevelOut(cefr=c, band=c.band, scenarios=len(repo.list(cefr=c))) for c in CEFR]


@router.get("/scenarios", response_model=list[ScenarioSummary])
def scenarios(cefr: CEFR | None = None, band: str | None = None, repo: ContentRepository = RepoDep):
    return [_summary(s) for s in repo.list(cefr=cefr, band=band)]


@router.get("/scenarios/{scenario_id}", response_model=Scenario)
def scenario(scenario_id: str, repo: ContentRepository = RepoDep):
    s = repo.get(scenario_id)
    if not s:
        raise HTTPException(404, "scenario not found")
    return s


@router.get("/lessons/{scenario_id}", response_model=LessonPlan)
def lesson(scenario_id: str, repo: ContentRepository = RepoDep):
    s = repo.get(scenario_id)
    if not s:
        raise HTTPException(404, "scenario not found")
    return build_lesson(s)


@router.get("/shadowing/{scenario_id}", response_model=list[Exercise])
def shadowing_session(scenario_id: str, repo: ContentRepository = RepoDep):
    s = repo.get(scenario_id)
    if not s:
        raise HTTPException(404, "scenario not found")
    return [build_exercise(s, p, ExerciseType.SHADOWING) for p in s.phrases]


@router.get("/phrases/common", response_model=list[Exercise])
def common_phrases(cefr: CEFR | None = None, limit: int = 20, repo: ContentRepository = RepoDep):
    pairs = repo.common_phrases(cefr)[: max(1, min(limit, 100))]
    return [build_exercise(s, p, ExerciseType.RECALL) for s, p in pairs]


@router.get("/exercises/{exercise_id}", response_model=Exercise)
def exercise(exercise_id: str, repo: ContentRepository = RepoDep):
    ex = resolve_exercise(repo, exercise_id)
    if not ex:
        raise HTTPException(404, "exercise not found")
    return ex
