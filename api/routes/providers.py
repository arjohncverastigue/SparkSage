from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.deps import get_current_user
import config
import providers
import db

router = APIRouter()


class SetPrimaryRequest(BaseModel):
    provider: str


@router.get("")
async def list_providers(user: dict = Depends(get_current_user)):
    available = providers.get_available_providers()
    result = []
    for name, info in config.PROVIDERS.items():
        result.append({
            "name": name,
            "display_name": info["name"],
            "model": info["model"],
            "free": info["free"],
            "configured": name in available,
            "is_primary": name == config.AI_PROVIDER,
        })
    return {"providers": result, "fallback_order": providers.FALLBACK_ORDER}


class TestProviderRequest(BaseModel):
    provider: str


@router.post("/test")
async def test_provider(body: TestProviderRequest, user: dict = Depends(get_current_user)):
    result = providers.test_provider(body.provider)
    return result


@router.put("/primary")
async def set_primary(body: SetPrimaryRequest, user: dict = Depends(get_current_user)):
    if body.provider not in config.PROVIDERS:
        return {"error": f"Unknown provider: {body.provider}"}

    await db.set_config("AI_PROVIDER", body.provider)
    config.AI_PROVIDER = body.provider
    config.PROVIDERS = config._build_providers()
    providers.reload_clients()

    return {"status": "ok", "primary": body.provider}
