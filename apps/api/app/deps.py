from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User
from .security import verify_session


def get_current_user(
    db: Session = Depends(get_db),
    session: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> User:
    if not session:
        raise HTTPException(status_code=401, detail="Not signed in")
    user_id = verify_session(session)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
