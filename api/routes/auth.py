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
            if not pw.startswith("$"): # Assuming hashed passwords start with a '$'
                _hashed_admin_pw = hash_password(pw)
            else:
                _hashed_admin_pw = pw
    return _hashed_admin_pw or ""


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    # Try to get password from environment variable first
    admin_password_raw = os.getenv("ADMIN_PASSWORD", "")
    hashed_admin_pw = ""

    if admin_password_raw:
        if admin_password_raw.startswith("$"):
            hashed_admin_pw = admin_password_raw
        else:
            hashed_admin_pw = hash_password(admin_password_raw)
    else:
        # If not in env, check DB for one
        db_pw = await db.get_config("ADMIN_PASSWORD")
        if db_pw:
            if db_pw.startswith("$"):
                hashed_admin_pw = db_pw
            else:
                hashed_admin_pw = hash_password(db_pw)

    if not hashed_admin_pw:
        raise HTTPException(status_code=400, detail="No admin password configured. Set ADMIN_PASSWORD in .env or via dashboard.")

    if not verify_password(body.password, hashed_admin_pw):
        raise HTTPException(status_code=401, detail="Invalid password")

    token, expires_at = create_token("admin")
    await db.create_session(token, "admin", expires_at)
    return TokenResponse(access_token=token, expires_at=expires_at)


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user_id": user["sub"], "role": "admin"}
