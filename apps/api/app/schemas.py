from __future__ import annotations

from pydantic import BaseModel, Field


class PinSetupRequest(BaseModel):
    pin: str = Field(min_length=4, max_length=12, pattern=r"^\d{4,12}$")


class PinLoginRequest(BaseModel):
    pin: str = Field(min_length=4, max_length=12)


class ProfileRequest(BaseModel):
    full_name: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    experience_level: str | None = None
    target_companies: str | None = None
    bio: str | None = None


class ProviderValidateRequest(BaseModel):
    provider: str = "groq"
    api_key: str = Field(min_length=1)
    base_url: str | None = None
    model: str | None = None


class ProviderCreateRequest(BaseModel):
    provider: str = "groq"
    api_key: str = Field(min_length=1)
    base_url: str | None = None
    default_model: str | None = None
    # Task-specific routing, e.g. {"resume": "...", "interview": "...",
    # "evaluation": "...", "report": "...", "fallback": "..."}
    task_models: dict[str, str] = Field(default_factory=dict)


class ProviderOut(BaseModel):
    id: int
    name: str
    display_name: str
    base_url: str | None
    is_active: bool
    is_enabled: bool
    default_model: str | None
    task_models: dict[str, str]
    key_hint: str | None
    validation_status: str
    last_validated_at: str | None
