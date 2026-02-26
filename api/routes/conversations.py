from fastapi import APIRouter, Depends
from api.deps import get_current_user
import db

router = APIRouter()


@router.get("")
async def list_conversations(user: dict = Depends(get_current_user)):
    channels = await db.list_channels()
    return {"channels": channels}


@router.get("/{channel_id}")
async def get_conversation(channel_id: str, user: dict = Depends(get_current_user)):
    messages = await db.get_messages(channel_id, limit=100)
    return {"channel_id": channel_id, "messages": messages}


@router.delete("/{channel_id}")
async def delete_conversation(channel_id: str, user: dict = Depends(get_current_user)):
    await db.clear_messages(channel_id)
    return {"status": "ok"}
