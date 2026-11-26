"""Provider endpoints. The full API key is accepted only in request
bodies, never logged, never returned — only a masked hint is exposed.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..llm import GroqProvider, OllamaProvider
from ..models import AuditLog, EncryptedProviderCredential, LLMProvider, LLMUsage, User
from ..schemas import ProviderCreateRequest, ProviderOut, ProviderValidateRequest
from ..security import decrypt_secret, encrypt_secret, mask_key

router = APIRouter(prefix="/providers", tags=["providers"])

DISPLAY_NAMES = {"groq": "Groq", "ollama": "Ollama (local)", "openai": "OpenAI", "gemini": "Google Gemini", "claude": "Anthropic Claude"}
BASE_URLS = {"groq": "https://api.groq.com/openai/v1", "ollama": "http://localhost:11434"}


def _adapter(name: str, api_key: str | None, base_url: str | None):
    if name == "ollama":
        return OllamaProvider(api_key=api_key, base_url=base_url or BASE_URLS["ollama"])
    # Default / Groq: OpenAI-compatible endpoint.
    return GroqProvider(api_key=api_key, base_url=base_url or BASE_URLS.get(name, "https://api.groq.com/openai/v1"))


def _to_out(provider: LLMProvider, db: Session) -> ProviderOut:
    cred = db.query(EncryptedProviderCredential).filter_by(provider_id=provider.id).first()
    return ProviderOut(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        base_url=provider.base_url,
        is_active=provider.is_active,
        is_enabled=provider.is_enabled,
        default_model=provider.default_model,
        task_models=provider.task_models or {},
        key_hint=cred.key_hint if cred else None,
        validation_status=cred.validation_status if cred else "unknown",
        last_validated_at=cred.last_validated_at.isoformat() if cred and cred.last_validated_at else None,
    )


@router.post("/validate")
async def validate_provider(body: ProviderValidateRequest, user: User = Depends(get_current_user)):
    adapter = _adapter(body.provider, body.api_key, body.base_url)
    result = await adapter.validate_connection()
    if not result.ok:
        return {
            "ok": False,
            "error": result.error,
            "error_code": result.error_code or "provider_error",
            "models": [],
        }
    return {"ok": True, "models": result.models, "default_model": result.default_model}


@router.post("")
async def create_provider(body: ProviderCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Validate live first; do not store a key that does not work.
    adapter = _adapter(body.provider, body.api_key, body.base_url)
    result = await adapter.validate_connection()
    if not result.ok:
        raise HTTPException(status_code=400, detail=result.error or "Provider validation failed")
    default_model = body.default_model or result.default_model
    task_models = dict(body.task_models or {})
    task_models.setdefault("fallback", default_model)
    for task in ("resume", "interview", "evaluation", "report"):
        task_models.setdefault(task, default_model)

    # Only one active provider at a time in Phase 1.
    db.query(LLMProvider).filter_by(user_id=user.id).update({"is_active": False})
    provider = LLMProvider(
        user_id=user.id,
        name=body.provider,
        display_name=DISPLAY_NAMES.get(body.provider, body.provider.title()),
        base_url=body.base_url or BASE_URLS.get(body.provider),
        is_active=True,
        is_enabled=True,
        default_model=default_model,
        task_models=task_models,
    )
    db.add(provider)
    db.flush()
    db.add(
        EncryptedProviderCredential(
            provider_id=provider.id,
            user_id=user.id,
            encrypted_key=encrypt_secret(body.api_key),
            key_hint=mask_key(body.api_key),
            validation_status="valid",
        )
    )
    db.add(AuditLog(user_id=user.id, action="provider_added", details={"provider": body.provider}))
    db.commit()
    db.refresh(provider)
    return _to_out(provider, db)


@router.get("")
def list_providers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    providers = db.query(LLMProvider).filter_by(user_id=user.id).order_by(LLMProvider.id).all()
    return [_to_out(p, db) for p in providers]


@router.post("/{provider_id}/test")
async def test_provider(provider_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    provider = db.query(LLMProvider).filter_by(id=provider_id, user_id=user.id).first()
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    cred = db.query(EncryptedProviderCredential).filter_by(provider_id=provider.id).first()
    if cred is None:
        raise HTTPException(status_code=400, detail="No credential stored for this provider")
    adapter = _adapter(provider.name, decrypt_secret(cred.encrypted_key), provider.base_url)
    result = await adapter.validate_connection()
    cred.validation_status = "valid" if result.ok else "invalid"
    if result.ok and result.default_model:
        provider.default_model = result.default_model
    db.commit()
    return {"ok": result.ok, "error": result.error, "error_code": result.error_code, "models": result.models}


@router.delete("/{provider_id}")
def delete_provider(provider_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    provider = db.query(LLMProvider).filter_by(id=provider_id, user_id=user.id).first()
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.add(AuditLog(user_id=user.id, action="provider_deleted", details={"provider": provider.name}))
    db.delete(provider)
    db.commit()
    return {"ok": True}


@router.get("/usage")
def usage(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = (
        db.query(
            func.coalesce(func.sum(LLMUsage.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(LLMUsage.estimated_cost_usd), 0.0).label("estimated_cost_usd"),
            func.count(LLMUsage.id).label("calls"),
        )
        .filter(LLMUsage.user_id == user.id)
        .one()
    )
    return {"total_tokens": int(row.total_tokens), "estimated_cost_usd": float(row.estimated_cost_usd), "calls": int(row.calls)}
