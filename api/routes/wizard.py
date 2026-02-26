from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.deps import get_current_user
import db

router = APIRouter()


@router.get("/status")
async def wizard_status():
    """Public endpoint - no auth required for first-run detection."""
    state = await db.get_wizard_state()
    return state


class WizardStepUpdate(BaseModel):
    step: int
    data: dict


@router.put("/step")
async def update_wizard_step(body: WizardStepUpdate, user: dict = Depends(get_current_user)):
    state = await db.get_wizard_state()
    current_data = state["data"]
    current_data[str(body.step)] = body.data
    await db.set_wizard_state(current_step=body.step, data=current_data)
    return {"status": "ok"}


class WizardCompleteRequest(BaseModel):
    config: dict[str, str]


@router.post("/complete")
async def complete_wizard(body: WizardCompleteRequest, user: dict = Depends(get_current_user)):
    # Save all config values to DB
    await db.set_config_bulk(body.config)

    # Mark wizard as completed
    await db.set_wizard_state(completed=True)

    # Sync to .env file
    await db.sync_db_to_env()

    # Reload config and providers
    import config as cfg
    all_config = await db.get_all_config()
    cfg.reload_from_db(all_config)

    import providers
    providers.reload_clients()

    return {"status": "ok"}
