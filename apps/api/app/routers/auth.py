from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import AuditLog, User, UserPreferences
from ..schemas import PinLoginRequest, PinSetupRequest
from ..security import hash_pin, sign_session, verify_pin

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=sign_session(user_id),
        httponly=True,
        samesite="lax",
        max_age=settings.session_max_age_seconds,
        path="/",
    )


@router.post("/setup-pin")
def setup_pin(body: PinSetupRequest, response: Response, db: Session = Depends(get_db)):
    """First-run only. Once any user exists, this endpoint refuses."""
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="PIN is already set up")
    pin_hash, salt = hash_pin(body.pin)
    user = User(pin_hash=pin_hash, pin_salt=salt, is_owner=True)
    db.add(user)
    db.flush()
    db.add(UserPreferences(user_id=user.id))
    db.add(AuditLog(user_id=user.id, action="pin_setup", details={}))
    db.commit()
    _set_session_cookie(response, user.id)
    return {"ok": True, "user_id": user.id}


@router.post("/login")
def login(body: PinLoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).order_by(User.id).first()
    if user is None or not user.pin_hash or not user.pin_salt:
        raise HTTPException(status_code=400, detail="PIN has not been set up yet")
    if not verify_pin(body.pin, user.pin_hash, user.pin_salt):
        raise HTTPException(status_code=401, detail="Incorrect PIN")
    db.add(AuditLog(user_id=user.id, action="login", details={}))
    db.commit()
    _set_session_cookie(response, user.id)
    return {"ok": True, "user_id": user.id}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.session_cookie_name, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"ok": True, "user_id": user.id, "is_owner": user.is_owner}
