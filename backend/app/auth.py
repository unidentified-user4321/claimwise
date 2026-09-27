"""Clerk authenticates identities; local mappings authorize application access."""

import httpx
from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.db.database import get_db
from app.db.models import User

bearer = HTTPBearer(auto_error=False)


def get_clerk_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    unauthorized = HTTPException(401, "Invalid or expired authentication token", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise unauthorized
    if not config.CLERK_SECRET_KEY:
        raise HTTPException(503, "Clerk authentication is not configured")
    try:
        state = authenticate_request(
            httpx.Request(request.method, str(request.url), headers={"Authorization": f"Bearer {credentials.credentials}"}),
            AuthenticateRequestOptions(
                secret_key=config.CLERK_SECRET_KEY,
                authorized_parties=[config.FRONTEND_ORIGIN],
                accepts_token=["session_token"],
            ),
        )
    except httpx.HTTPError:
        raise HTTPException(503, "Authentication service unavailable") from None
    subject = (state.payload or {}).get("sub")
    if not state.is_signed_in or not isinstance(subject, str) or not subject.startswith("user_"):
        raise unauthorized
    return subject


def get_current_user(
    clerk_user_id: str = Depends(get_clerk_user_id),
    db: Session = Depends(get_db),
) -> User:
    user = db.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
    if user is None:
        raise HTTPException(403, "Account linking required")
    return user


def require_employee(user: User = Depends(get_current_user)) -> User:
    if user.role != "employee":
        raise HTTPException(403, "Employee access required")
    return user
