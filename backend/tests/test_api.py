from datetime import UTC, datetime, timedelta

from tests.conftest import speak


def _time_travel(minutes: int) -> None:
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from app.db.models import SrsCard
    from app.db.session import get_engine

    with Session(get_engine()) as db:
        for card in db.scalars(select(SrsCard)):
            card.due_at = card.due_at - timedelta(minutes=minutes)
        db.commit()


def test_health_ready_and_auth_required(client, auth):
    ui = client.get("/")
    assert ui.status_code == 200 and "SpeakFlow" in ui.text
    fb_js = client.get("/firebase-config.js")
    assert fb_js.status_code == 200 and "SpeakFlowFirebase" in fb_js.text
    ia_js = client.get("/miServicioDeIA")
    assert ia_js.status_code == 200 and "consultarAsistente" in ia_js.text
    tpl = client.post(
        "/v1/ai/template",
        json={
            "template_id": "conexion-key",
            "template_variables": {
                "apiKey": "npm_key_live_example_9876543210abc",
                "userQuery": "Necesito un script básico de Node.js para conectar un cliente HTTP",
            },
        },
    ).json()
    assert tpl["template_id"] == "conexion-key" and "conexion-key" in tpl["response"]
    tpl2 = client.post(
        "/v1/ai/template",
        json={"template_id": "conexion-key", "template_variables": {"apiKey": "short", "userQuery": "Hola"}},
    ).json()
    assert "Hola" in tpl2["response"]
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json()["scenarios"] == 180
    st = client.get("/v1/providers/status", headers={"X-OpenAI-Key": "sk-test"}).json()
    assert st["has_openai_key"] is True and st["speech_provider"] == "openai_whisper"
    st_gc = client.get(
        "/v1/providers/status",
        headers={"X-Google-Cloud-Key": "gc-test", "X-Gemini-Key": "gm-test"},
    ).json()
    assert st_gc["speech_provider"] == "google_cloud" and st_gc["llm_provider"] == "gemini"
    fm = client.get("/v1/freemium/status", headers={**auth, "X-Freemium-Tier": "free"}).json()
    assert fm["tier"] == "free" and fm["can_start_roleplay"] is True
    assert client.post("/v1/tts", headers=auth, json={"text": "Hello"}).status_code == 400
    assert client.get("/v1/scenarios").status_code == 401
    assert client.get("/v1/scenarios", headers={"Authorization": "Bearer bad"}).status_code == 401
    assert client.post("/v1/dev/fast-forward-srs", headers=auth).json() == {"updated": 0}
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_catalog(client, auth):
    levels = client.get("/v1/levels", headers=auth).json()
    assert [lv["cefr"] for lv in levels] == ["A1", "A2", "B1", "B2", "C1", "C2"]
    assert levels[0]["band"] == "basic"
    modules = client.get("/v1/modules", headers=auth).json()
    assert len(modules) == 6 and all(m["scenarios"] == 30 for m in modules)
    assert len(client.get("/v1/scenarios?band=intermediate", headers=auth).json()) == 60
    assert len(client.get("/v1/scenarios?topic=health-and-emergencies", headers=auth).json()) == 30
    for m in modules:
        for lv in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            cell = client.get(f"/v1/scenarios?topic={m['id']}&cefr={lv}", headers=auth).json()
            assert len(cell) >= 5
    c2_ids = {s["id"] for s in client.get("/v1/scenarios?cefr=C2", headers=auth).json()}
    assert "c2-dinner-debate" in c2_ids and "c2-executive-pitch" in c2_ids
    assert client.get("/v1/scenarios/a1-ordering-coffee", headers=auth).json()["roleplay"]["ai_role"] == "barista"
    assert client.get("/v1/scenarios/nope", headers=auth).status_code == 404
    lesson = client.get("/v1/lessons/b1-hotel-check-in", headers=auth).json()
    assert len(lesson["stages"]) == 4 and lesson["roleplay_script"]["ai_role"] == "hotel receptionist"
    assert client.get("/v1/lessons/nope", headers=auth).status_code == 404
    shadow = client.get("/v1/shadowing/a2-asking-directions", headers=auth).json()
    assert all(e["type"] == "shadowing" and e["prompt"]["audio_text"] for e in shadow)
    assert client.get("/v1/shadowing/nope", headers=auth).status_code == 404
    common = client.get("/v1/phrases/common?cefr=A1&limit=2", headers=auth).json()
    assert len(common) == 2 and common[0]["type"] == "recall"
    ex_id = common[0]["id"]
    assert client.get(f"/v1/exercises/{ex_id}", headers=auth).status_code == 200
    assert client.get("/v1/exercises/bad.id.x", headers=auth).status_code == 404


def test_translate_and_bookmark_phrase(client, auth):
    tr = client.post(
        "/v1/translate",
        headers=auth,
        json={
            "selected_text": "have",
            "phrase_text": "Can I have a coffee, please?",
            "scenario_id": "a1-ordering-coffee",
            "phrase_id": "can-i-have",
        },
    ).json()
    assert tr["ipa"] == "hæv" and "café" in tr["phrase_translation_es"]

    tr_full = client.post(
        "/v1/translate",
        headers=auth,
        json={"selected_text": "Can I have a coffee, please?", "scenario_id": "a1-ordering-coffee"},
    ).json()
    assert "café" in tr_full["word_translation_es"]

    tr_fallback = client.post(
        "/v1/translate",
        headers=auth,
        json={"selected_text": "please", "phrase_text": "Can I have a coffee, please?"},
    ).json()
    assert "por favor" in tr_fallback["word_translation_es"]

    tr_unknown = client.post(
        "/v1/translate",
        headers=auth,
        json={"selected_text": "supercalifragilistic", "phrase_text": "short text"},
    ).json()
    assert "contexto" in tr_unknown["word_translation_es"]

    bm = client.post(
        "/v1/review/bookmark",
        headers=auth,
        json={"scenario_id": "a1-ordering-coffee", "phrase_id": "can-i-have", "focus_word": "coffee"},
    ).json()
    assert bm["saved"] is True and "coffee" in bm["focus_words"]
    bm2 = client.post(
        "/v1/review/bookmark",
        headers=auth,
        json={"scenario_id": "a1-ordering-coffee", "phrase_id": "can-i-have", "focus_word": "please"},
    ).json()
    assert set(bm2["focus_words"]) == {"coffee", "please"}
    assert client.post("/v1/review/bookmark", headers=auth, json={"scenario_id": "nope"}).status_code == 404
    assert (
        client.post(
            "/v1/review/bookmark",
            headers=auth,
            json={"scenario_id": "a1-ordering-coffee", "phrase_id": "missing"},
        ).status_code
        == 404
    )


def test_attempt_feedback_and_srs_loop(client, auth):
    ex = "a1-ordering-coffee.can-i-have.recall"
    bad = speak(client, f"/v1/exercises/{ex}/attempts", auth, "can I half a coffee").json()
    assert bad["evaluation"]["passed"] is False
    assert bad["feedback"]["level"] == "retry"
    assert {u["kind"] for u in bad["srs"]} == {"phrase", "feedback"}

    # Failed items re-enter after a short relearning step (10 min): nothing due right now...
    assert client.get("/v1/review/due", headers=auth).json() == []
    _time_travel(minutes=11)
    due = client.get("/v1/review/due", headers=auth).json()
    kinds = {d["kind"] for d in due}
    assert "feedback" in kinds
    fb_item = next(d for d in due if d["kind"] == "feedback")
    assert set(fb_item["exercise"]["prompt"]["focus_words"]) == {"have", "please"}
    assert fb_item["exercise"]["type"] == "recall"

    good = speak(client, f"/v1/review/{fb_item['card_id']}/attempts", auth, "Can I have a coffee please").json()
    assert good["evaluation"]["passed"] and good["feedback"]["level"] == "excellent"
    nxt = {u["kind"]: u for u in good["srs"]}
    assert datetime.fromisoformat(nxt["feedback"]["next_due_at"]) > datetime.now(UTC) + timedelta(hours=12)

    prog = client.get("/v1/progress", headers=auth).json()
    assert prog["attempts"] == 2 and prog["passed"] == 1 and prog["cards_total"] == 2


def test_review_errors_and_guided_card(client, auth):
    assert speak(client, "/v1/review/nope/attempts", auth, "x").status_code == 404
    speak(client, "/v1/exercises/a2-asking-directions.is-it-far.shadowing/attempts", auth, "is it far from here")
    from app.content.repository import get_repository
    from app.db.models import SrsCard
    from app.services.practice import card_to_exercise

    repo = get_repository()
    card = SrsCard(kind="phrase", scenario_id="a2-asking-directions", phrase_id="is-it-far", repetitions=3,
                   focus_words=[])
    assert card_to_exercise(repo, card).type == "completion"
    card.repetitions = 0
    assert card_to_exercise(repo, card).type == "guided"
    card.scenario_id = "gone"
    assert card_to_exercise(repo, card) is None


def test_upload_validation(client, auth):
    url = "/v1/exercises/a1-ordering-coffee.thank-you.recall/attempts"
    assert speak(client, url, auth, "x", ctype="text/plain").status_code == 415
    r = client.post(url, headers=auth, files={"audio": ("a.wav", b"", "audio/wav")})
    assert r.status_code == 422
    big = b"0" * (5 * 1024 * 1024 + 10)
    r = client.post(url, headers=auth, files={"audio": ("a.wav", big, "audio/wav")})
    assert r.status_code == 413
    assert speak(client, "/v1/exercises/x.y.recall/attempts", auth, "x").status_code == 404


def test_rate_limit():
    import pytest
    from fastapi import HTTPException

    from app.core.security import RateLimiter
    from app.db.models import User

    lim, u = RateLimiter(2, 60), User(id="u")
    lim(u)
    lim(u)
    with pytest.raises(HTTPException) as e:
        lim(u)
    assert e.value.status_code == 429
