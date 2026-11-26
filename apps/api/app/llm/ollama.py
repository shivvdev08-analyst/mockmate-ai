"""Ollama / local OpenAI-compatible adapter.

Not wired to the UI in Phase 1 (Groq is the primary provider), but it
implements the same LLMProvider interface, so local inference can be
enabled later without redesigning the AI layer. No API key is required.
"""
from __future__ import annotations

import httpx

from .base import LLMProvider, ProviderValidationError, ProviderValidationResult

DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout_seconds: int = 30):
        super().__init__(api_key, base_url or DEFAULT_BASE_URL, timeout_seconds)
        self._model: str | None = None

    def configure(self, **kwargs) -> None:
        if "base_url" in kwargs and kwargs["base_url"]:
            self.base_url = kwargs["base_url"]
        if "model" in kwargs:
            self._model = kwargs["model"]
        if "timeout_seconds" in kwargs:
            self.timeout_seconds = int(kwargs["timeout_seconds"])

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
        except httpx.HTTPError as exc:
            raise ProviderValidationError(f"Could not reach Ollama at {self.base_url}: {exc}", "unreachable") from exc
        if resp.status_code >= 400:
            raise ProviderValidationError(f"Ollama returned HTTP {resp.status_code}.", "provider_error")
        return [m["name"] for m in resp.json().get("models", []) if m.get("name")]

    async def validate_connection(self) -> ProviderValidationResult:
        try:
            models = await self.list_models()
        except ProviderValidationError as exc:
            return ProviderValidationResult(ok=False, error=str(exc), error_code=exc.code)
        if not models:
            return ProviderValidationResult(
                ok=False, error="Ollama is reachable but no models are installed (run `ollama pull <model>`).",
                error_code="provider_error",
            )
        return ProviderValidationResult(ok=True, models=models, default_model=models[0])

    async def generate_response(self, prompt: str, model: str | None = None, **kwargs) -> str:
        model = model or self._model or (await self.list_models())[0]
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate", json={"model": model, "prompt": prompt, "stream": False}
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def generate_structured_response(self, prompt: str, model: str | None = None, **kwargs) -> dict:
        import json

        return json.loads(await self.generate_response(prompt, model=model, **kwargs))

    async def stream_response(self, prompt: str, model: str | None = None, **kwargs):
        model = model or self._model or (await self.list_models())[0]
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            async with client.stream(
                "POST", f"{self.base_url}/api/generate", json={"model": model, "prompt": prompt, "stream": True}
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        import json

                        yield json.loads(line).get("response", "")

    async def get_usage(self) -> dict:
        return {"requests": 0, "tokens": 0, "note": "Local inference has no metered usage."}

    async def health_check(self) -> bool:
        return (await self.validate_connection()).ok
