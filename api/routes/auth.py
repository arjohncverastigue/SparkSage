from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.auth import create_token, hash_password, verify_password
from api.deps import get_current_user
import db

router = APIRouter()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
# Store hashed password on first use
_hashed_admin_pw: str | None = None


def _get_hashed_password() -> str:
    """Get or create the hashed admin password."""
    global _hashed_admin_pw
    if _hashed_admin_pw is None:
        pw = os.getenv("ADMIN_PASSWORD", "")
        if pw:
            _hashed_admin_pw = hash_password(pw)
    return _hashed_admin_pw or ""


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    admin_pw = os.getenv("ADMIN_PASSWORD", "")
    if not admin_pw:
        # If no password is set, check DB for one
        db_pw = await db.get_config("ADMIN_PASSWORD")
        if db_pw:
            admin_pw = db_pw

    if not admin_pw:
        raise HTTPException(status_code=400, detail="No admin password configured. Set ADMIN_PASSWORD in .env")

    # Simple direct comparison for the env-based password
    if body.password != admin_pw:
        raise HTTPException(status_code=401, detail="Invalid password")

    token, expires_at = create_token("admin")
    await db.create_session(token, "admin", expires_at)
    return TokenResponse(access_token=token, expires_at=expires_at)


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user_id": user["sub"], "role": "admin"}
