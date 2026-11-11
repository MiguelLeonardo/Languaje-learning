import os

import pytest

os.environ.setdefault("ENV", "test")
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret-with-at-least-32-bytes-0123456789"


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.db.session import Base, get_engine
    from app.main import create_app

    engine = get_engine()
    Base.metadata.drop_all(engine)
    with TestClient(create_app()) as c:
        yield c
    Base.metadata.drop_all(engine)


@pytest.fixture()
def auth(client):
    token = client.post("/v1/auth/dev-token", json={"user_id": "tester"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def speak(client, url, headers, transcript, ctype="audio/wav"):
    return client.post(url, headers=headers, files={"audio": ("a.wav", b"RIFFfake", ctype)},
                       data={"debug_transcript": transcript})
