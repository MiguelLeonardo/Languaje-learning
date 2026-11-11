from tests.conftest import speak


def test_scripted_roleplay_full_flow(client, auth):
    st = client.post("/v1/roleplay/a1-ordering-coffee/sessions", headers=auth).json()
    assert st["ai_messages"] == ["Hi! What can I get for you?"]
    assert st["pending_turn"]["suggested_lines"]
    sid = st["session_id"]
    url = f"/v1/roleplay/sessions/{sid}/turns"

    retry = speak(client, url, auth, "where is the bathroom").json()
    assert retry["accepted"] is False and retry["feedback"]["level"] == "retry"

    # Free-form response using scenario vocabulary is accepted with natural_alternative
    free = speak(client, url, auth, "I would really love a hot coffee right now").json()
    assert free["accepted"] is True and free["response_style"] == "freeform"
    assert free["natural_alternative"]

    answers = ["Medium please", "How much is it", "Thank you very much"]
    for a in answers:
        st = speak(client, url, auth, a).json()
        assert st["accepted"] is True, a
    assert st["status"] == "completed" and st["pending_turn"] is None
    assert st["ai_messages"] == ["Have a nice day!"]
    assert st["average_score"] > 0.75
    assert speak(client, url, auth, "hello").status_code == 409


def test_roleplay_errors(client, auth):
    assert client.post("/v1/roleplay/nope/sessions", headers=auth).status_code == 404
    assert speak(client, "/v1/roleplay/sessions/nope/turns", auth, "hi").status_code == 404


def test_debug_transcript_rejected_for_real_provider(client, auth):
    from app.main import app as _  # noqa: F401
    from app.speech.factory import get_speech_provider

    class Fake:
        name = "real"

        async def transcribe(self, *a, **k):
            raise AssertionError

    client.app.dependency_overrides[get_speech_provider] = lambda: Fake()
    r = speak(client, "/v1/exercises/a1-ordering-coffee.thank-you.recall/attempts", auth, "thank you")
    assert r.status_code == 400
    client.app.dependency_overrides.clear()
