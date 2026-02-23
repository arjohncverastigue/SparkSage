from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.deps import get_current_user
import discord

router = APIRouter()


@router.get("/status")
async def bot_status(user: dict = Depends(get_current_user)):
    from bot import get_bot_status
    return get_bot_status()

class ChannelIDsRequest(BaseModel):
    channel_ids: List[str]

@router.post("/resolve_channels")
async def resolve_channels(body: ChannelIDsRequest, user: dict = Depends(get_current_user)):
    from bot import bot as discord_bot # Import the running bot instance
    
    resolved_names = {}
    for channel_id_str in body.channel_ids:
        try:
            channel_id = int(channel_id_str)
            channel = discord_bot.get_channel(channel_id)
            if channel:
                resolved_names[channel_id_str] = channel.name
            else:
                resolved_names[channel_id_str] = "Unknown Channel"
        except ValueError:
            resolved_names[channel_id_str] = "Invalid ID"
    
    return {"resolved_names": resolved_names}
