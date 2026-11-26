import os

os.environ["MOCKMATE_SECRET_KEY"] = "test-secret-key-for-pytest-only"
os.environ["DATABASE_URL"] = "sqlite:///./test_mockmate.db"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    # Dispose pooled connections first: a stale SQLite connection to a
    # previously dropped file makes the next CREATE TABLE fail read-only.
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    engine.dispose()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def authed_client(client):
    r = client.post("/api/v1/auth/setup-pin", json={"pin": "1234"})
    assert r.status_code == 200, r.text
    return client
