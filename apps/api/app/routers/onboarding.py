from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import LLMProvider, User, UserPreferences, UserProfile
from ..schemas import ProfileRequest

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/status")
def status(db: Session = Depends(get_db)):
    user = db.query(User).order_by(User.id).first()
    if user is None:
        return {
            "setup_complete": False,
            "pin_set": False,
            "provider_configured": False,
            "profile_completed": False,
            "onboarding_completed": False,
        }
    provider_configured = (
        db.query(LLMProvider)
        .filter(LLMProvider.user_id == user.id, LLMProvider.is_active == True)  # noqa: E712
        .count()
        > 0
    )
    prefs = db.query(UserPreferences).filter_by(user_id=user.id).first()
    profile = db.query(UserProfile).filter_by(user_id=user.id).first()
    profile_completed = bool(profile and (profile.full_name or profile.target_roles))
    onboarding_completed = bool(prefs and prefs.onboarding_completed)
    return {
        "setup_complete": bool(provider_configured and profile_completed),
        "pin_set": bool(user.pin_hash),
        "provider_configured": provider_configured,
        "profile_completed": profile_completed,
        "onboarding_completed": onboarding_completed,
    }


@router.post("/profile")
def save_profile(body: ProfileRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = db.query(UserProfile).filter_by(user_id=user.id).first()
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    profile.full_name = body.full_name
    profile.target_roles = body.target_roles or []
    profile.experience_level = body.experience_level
    profile.target_companies = body.target_companies
    profile.bio = body.bio
    prefs = db.query(UserPreferences).filter_by(user_id=user.id).first()
    if prefs is None:
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)
    prefs.onboarding_completed = True
    db.commit()
    return {"ok": True, "onboarding_completed": True}
