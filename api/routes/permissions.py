from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from api.deps import get_current_user
import db

router = APIRouter()

class CommandPermissionBase(BaseModel):
    command_name: str
    guild_id: str
    role_id: str

class CommandPermissionCreate(CommandPermissionBase):
    pass

class CommandPermissionResponse(CommandPermissionBase):
    class Config:
        from_attributes = True


@router.get("", response_model=list[CommandPermissionResponse])
async def list_command_permissions(
    user: dict = Depends(get_current_user),
    guild_id: str = Query(..., description="Filter permissions by guild ID")
):
    permissions = await db.get_all_command_permissions(guild_id=guild_id)
    return permissions


@router.post("", response_model=CommandPermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_command_permission(
    permission: CommandPermissionCreate,
    user: dict = Depends(get_current_user)
):
    # Potentially add validation here to ensure the user has permissions to set permissions
    # For now, relying on dashboard auth to restrict access
    await db.add_command_permission(
        permission.command_name,
        permission.guild_id,
        permission.role_id
    )
    return permission # Return the created permission


@router.delete("/{command_name}/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_command_permission(
    command_name: str,
    role_id: str,
    user: dict = Depends(get_current_user),
    guild_id: str = Query(..., description="The ID of the guild the permission belongs to")
):
    # Verify ownership or admin rights if needed
    # For simplicity, assume authenticated user can delete permissions for their guild
    permissions = await db.get_command_permissions(command_name, guild_id)
    if role_id not in permissions:
        raise HTTPException(status_code=404, detail="Command permission not found")

    await db.remove_command_permission(command_name, guild_id, role_id)
    return
