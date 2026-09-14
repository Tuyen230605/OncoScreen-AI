"""Dependencies: get_db, get_current_user, require_role."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DB = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    payload = decode_token(token)
    if not payload or not (user := db.get(User, payload.get("sub"))):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token không hợp lệ")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: str) -> Callable[[User], User]:
    def _check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền")
        return user

    return _check


Patient = Annotated[User, Depends(require_role("patient"))]
Doctor = Annotated[User, Depends(require_role("doctor"))]
