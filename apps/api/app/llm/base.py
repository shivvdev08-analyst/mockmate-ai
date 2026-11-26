"""Provider-independent LLM interface. Every provider implements this ABC."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderValidationResult:
    ok: bool
    models: list[str] = field(default_factory=list)
    default_model: str | None = None
    error: str | None = None
    error_code: str | None = None  # bad_key | rate_limited | timeout | provider_error | unreachable


class ProviderValidationError(Exception):
    def __init__(self, message: str, code: str = "provider_error"):
        super().__init__(message)
        self.code = code


class LLMProvider(ABC):
    name: str = "base"

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout_seconds: int = 30):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def configure(self, **kwargs) -> None: ...

    @abstractmethod
    async def validate_connection(self) -> ProviderValidationResult: ...

    @abstractmethod
    async def list_models(self) -> list[str]: ...

    @abstractmethod
    async def generate_response(self, prompt: str, model: str | None = None, **kwargs) -> str: ...

    @abstractmethod
    async def generate_structured_response(self, prompt: str, model: str | None = None, **kwargs) -> dict: ...

    @abstractmethod
    async def stream_response(self, prompt: str, model: str | None = None, **kwargs):
        """Async generator yielding text chunks."""
        yield ""  # pragma: no cover - subclasses override

    @abstractmethod
    async def get_usage(self) -> dict: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
