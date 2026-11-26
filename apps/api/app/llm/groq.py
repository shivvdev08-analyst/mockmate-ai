"""Groq adapter via the OpenAI-compatible endpoint.

validate_connection(): GET /models AND a tiny chat completion
(max_tokens=5). Only both succeeding counts as connected.
Errors are classified: 401 -> bad_key, 429 -> rate_limited,
timeout -> timeout, anything else -> provider_error.
The API key is never logged.
"""
from __future__ import annotations

import httpx

from .base import LLMProvider, ProviderValidationError, ProviderValidationResult

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout_seconds: int = 30):
        super().__init__(api_key, base_url or DEFAULT_BASE_URL, timeout_seconds)
        self._usage = {"requests": 0, "tokens": 0}

    def configure(self, **kwargs) -> None:
        if "api_key" in kwargs:
            self.api_key = kwargs["api_key"]
        if "base_url" in kwargs and kwargs["base_url"]:
            self.base_url = kwargs["base_url"]
        if "timeout_seconds" in kwargs:
            self.timeout_seconds = int(kwargs["timeout_seconds"])

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _classify(status: int) -> str:
        if status == 401:
            return "bad_key"
        if status == 429:
            return "rate_limited"
        return "provider_error"

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.get(f"{self.base_url}/models", headers=self._headers())
        if resp.status_code == 401:
            raise ProviderValidationError("Invalid Groq API key (401).", "bad_key")
        if resp.status_code == 429:
            raise ProviderValidationError("Groq rate limit reached (429). Try again later.", "rate_limited")
        if resp.status_code >= 400:
            raise ProviderValidationError(f"Groq returned HTTP {resp.status_code}.", "provider_error")
        data = resp.json()
        return [m["id"] for m in data.get("data", []) if m.get("id")]

    async def validate_connection(self) -> ProviderValidationResult:
        if not self.api_key:
            return ProviderValidationResult(ok=False, error="No API key provided.", error_code="bad_key")
        try:
            models = await self.list_models()
        except ProviderValidationError as exc:
            return ProviderValidationResult(ok=False, error=str(exc), error_code=exc.code)
        except httpx.TimeoutException:
            return ProviderValidationResult(ok=False, error="Connection to Groq timed out.", error_code="timeout")
        except httpx.HTTPError:
            return ProviderValidationResult(ok=False, error="Could not reach Groq.", error_code="unreachable")
        if not models:
            return ProviderValidationResult(ok=False, error="Groq returned no models.", error_code="provider_error")

        # Tiny completion proves the key can actually generate, not just list.
        model = models[0]
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
                        "max_tokens": 5,
                    },
                )
        except httpx.TimeoutException:
            return ProviderValidationResult(ok=False, error="Groq chat completion timed out.", error_code="timeout")
        except httpx.HTTPError:
            return ProviderValidationResult(ok=False, error="Could not reach Groq.", error_code="unreachable")
        if resp.status_code == 401:
            return ProviderValidationResult(ok=False, error="Invalid Groq API key (401).", error_code="bad_key")
        if resp.status_code == 429:
            return ProviderValidationResult(ok=False, error="Groq rate limit reached (429).", error_code="rate_limited")
        if resp.status_code >= 400:
            return ProviderValidationResult(
                ok=False, error=f"Groq chat completion failed (HTTP {resp.status_code}).", error_code="provider_error"
            )
        self._usage["requests"] += 1
        return ProviderValidationResult(ok=True, models=models, default_model=model)

    async def generate_response(self, prompt: str, model: str | None = None, **kwargs) -> str:
        model = model or (await self.list_models())[0]
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={"model": model, "messages": [{"role": "user", "content": prompt}], **kwargs},
            )
            resp.raise_for_status()
            data = resp.json()
        self._usage["requests"] += 1
        return data["choices"][0]["message"]["content"]

    async def generate_structured_response(self, prompt: str, model: str | None = None, **kwargs) -> dict:
        import json

        text = await self.generate_response(
            prompt, model=model, response_format={"type": "json_object"}, **kwargs
        )
        return json.loads(text)

    async def stream_response(self, prompt: str, model: str | None = None, **kwargs):
        model = model or (await self.list_models())[0]
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": True, **kwargs},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line[6:].strip() != "[DONE]":
                        import json

                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0].get("delta", {}).get("content")
                        if delta:
                            yield delta

    async def get_usage(self) -> dict:
        return dict(self._usage)

    async def health_check(self) -> bool:
        result = await self.validate_connection()
        return result.ok
