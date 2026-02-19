from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.deps import get_current_user
import db

router = APIRouter()

# Keys that contain secrets and should be masked in GET responses
SENSITIVE_KEYS = {
    "DISCORD_TOKEN",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "JWT_SECRET",
    "ADMIN_PASSWORD",
    "DISCORD_CLIENT_SECRET",
}


def mask_value(key: str, value: str) -> str:
    """Mask sensitive values, showing only the last 4 chars."""
    if key in SENSITIVE_KEYS and value and len(value) > 4:
        return "***" + value[-4:]
    return value


class ConfigUpdate(BaseModel):
    values: dict[str, str]


@router.get("")
async def get_config(user: dict = Depends(get_current_user)):
    all_config = await db.get_all_config()
    masked = {k: mask_value(k, v) for k, v in all_config.items()}
    return {"config": masked}


@router.put("")
async def update_config(body: ConfigUpdate, user: dict = Depends(get_current_user)):
    await db.set_config_bulk(body.values)
    # Reload config module from DB values
    await _reload_config()
    return {"status": "ok"}


async def _reload_config():
    """Reload the config module from DB values and rebuild providers."""
    import config as cfg

    all_config = await db.get_all_config()
    cfg.reload_from_db(all_config)

    import providers
    providers.reload_clients()
