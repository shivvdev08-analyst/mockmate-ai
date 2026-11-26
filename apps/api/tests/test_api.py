"""Phase 1 tests: health, PIN auth, provider validation (mocked Groq HTTP),
masked-key listing, onboarding persistence."""
import httpx
import pytest

import app.llm.groq as groq_mod


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeClient:
    """Stands in for httpx.AsyncClient; records that Groq was 'called'."""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, headers=None):
        assert "api.groq.com" in url
        assert headers and headers["Authorization"].startswith("Bearer gsk_")
        return FakeResponse(200, {"data": [{"id": "openai/gpt-oss-20b"}, {"id": "openai/gpt-oss-120b"}]})

    async def post(self, url, headers=None, json=None):
        assert json["max_tokens"] == 5
        return FakeResponse(200, {"choices": [{"message": {"content": "ok"}}]})


class FakeClient401(FakeClient):
    async def get(self, url, headers=None):
        return FakeResponse(401, {"error": {"message": "Invalid API Key"}})


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_onboarding_status_before_setup(client):
    r = client.get("/api/v1/onboarding/status")
    assert r.status_code == 200
    assert r.json() == {
        "setup_complete": False,
        "pin_set": False,
        "provider_configured": False,
        "profile_completed": False,
        "onboarding_completed": False,
    }


def test_pin_setup_login_and_me(client):
    r = client.post("/api/v1/auth/setup-pin", json={"pin": "1234"})
    assert r.status_code == 200, r.text
    # Second setup must be refused.
    assert client.post("/api/v1/auth/setup-pin", json={"pin": "9999"}).status_code == 400
    # Wrong PIN fails.
    fresh = client.post("/api/v1/auth/login", json={"pin": "0000"})
    assert fresh.status_code == 401
    # Correct PIN succeeds and /me works with the session cookie.
    assert client.post("/api/v1/auth/login", json={"pin": "1234"}).status_code == 200
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["is_owner"] is True


def test_provider_validate_mocked_groq(authed_client, monkeypatch):
    monkeypatch.setattr(groq_mod.httpx, "AsyncClient", FakeClient)
    r = authed_client.post(
        "/api/v1/providers/validate",
        json={"provider": "groq", "api_key": "gsk_testkey1234"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["models"] == ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
    assert "gsk_testkey1234" not in r.text  # full key is never echoed back


def test_provider_validate_bad_key(authed_client, monkeypatch):
    monkeypatch.setattr(groq_mod.httpx, "AsyncClient", FakeClient401)
    r = authed_client.post(
        "/api/v1/providers/validate",
        json={"provider": "groq", "api_key": "gsk_badkey"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is False
    assert r.json()["error_code"] == "bad_key"


def test_provider_save_lists_masked_key_and_usage(authed_client, monkeypatch):
    monkeypatch.setattr(groq_mod.httpx, "AsyncClient", FakeClient)
    r = authed_client.post(
        "/api/v1/providers",
        json={"provider": "groq", "api_key": "gsk_testkey1234"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["key_hint"] == "gsk_••••1234"
    assert r.json()["task_models"]["interview"] == "openai/gpt-oss-20b"

    listing = authed_client.get("/api/v1/providers")
    assert listing.status_code == 200
    assert "gsk_testkey1234" not in listing.text
    assert listing.json()[0]["key_hint"] == "gsk_••••1234"

    usage = authed_client.get("/api/v1/providers/usage")
    assert usage.status_code == 200
    assert usage.json() == {"total_tokens": 0, "estimated_cost_usd": 0.0, "calls": 0}

    # Onboarding status now reports a provider configured.
    status = authed_client.get("/api/v1/onboarding/status")
    assert status.json()["provider_configured"] is True


def test_onboarding_profile_persists(authed_client):
    r = authed_client.post(
        "/api/v1/onboarding/profile",
        json={"full_name": "Test Candidate", "target_roles": ["AI Engineer"], "experience_level": "Fresher"},
    )
    assert r.status_code == 200
    status = authed_client.get("/api/v1/onboarding/status")
    assert status.json()["profile_completed"] is True
    assert status.json()["onboarding_completed"] is True
