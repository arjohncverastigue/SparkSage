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


class ChannelPromptRequest(BaseModel):
    channel_id: str
    guild_id: str
    system_prompt: str

@router.get("/channel_prompts")
async def get_channel_prompts(user: dict = Depends(get_current_user)):
    prompts = await db.get_all_channel_prompts()
    return {"channel_prompts": prompts}

@router.post("/channel_prompts")
async def set_channel_prompt_api(body: ChannelPromptRequest, user: dict = Depends(get_current_user)):
    await db.set_channel_prompt(body.channel_id, body.guild_id, body.system_prompt)
    return {"status": "ok"}

@router.delete("/channel_prompts/{channel_id}")
async def delete_channel_prompt_api(channel_id: str, user: dict = Depends(get_current_user)):
    await db.delete_channel_prompt(channel_id)
    return {"status": "ok"}


class ChannelProviderRequest(BaseModel):
    channel_id: str
    guild_id: str
    provider_name: str

@router.get("/channel_providers")
async def get_channel_providers(user: dict = Depends(get_current_user)):
    providers = await db.get_all_channel_providers()
    return {"channel_providers": providers}

@router.post("/channel_providers")
async def set_channel_provider_api(body: ChannelProviderRequest, user: dict = Depends(get_current_user)):
    await db.set_channel_provider(body.channel_id, body.guild_id, body.provider_name)
    return {"status": "ok"}

@router.delete("/channel_providers/{channel_id}")
async def delete_channel_provider_api(channel_id: str, user: dict = Depends(get_current_user)):
    await db.delete_channel_provider(channel_id)
    return {"status": "ok"}

