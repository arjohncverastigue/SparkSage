from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.deps import get_current_user
import db as database
import os
import json

router = APIRouter()

class PluginManifest(BaseModel):
    name: str
    version: str
    author: str | None = None
    description: str | None = None
    cog: str # The Python module path for the cog

class PluginEnableDisableRequest(BaseModel):
    plugin_name: str

@router.get("")
async def list_plugins(user: dict = Depends(get_current_user)):
    plugins = await database.get_all_plugins()
    return {"plugins": plugins}

@router.post("/install")
async def install_plugin(manifest: PluginManifest, user: dict = Depends(get_current_user)):
    # Basic validation for cog path
    if not manifest.cog.startswith("plugins."):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cog path must start with 'plugins.'"
        )
    
    # Check if plugin already exists
    if await database.get_plugin(manifest.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Plugin '{manifest.name}' already installed."
        )
    
    # For now, we are not handling actual file uploads or manifest parsing here.
    # This endpoint assumes the manifest data is provided directly and
    # the cog file exists at the specified cog_path.
    # In a real scenario, this would involve more robust file handling.

    try:
        # Save manifest data to DB
        await database.add_plugin(
            name=manifest.name,
            version=manifest.version,
            author=manifest.author,
            description=manifest.description,
            cog_path=manifest.cog,
            manifest_path="N/A" # We are not storing actual manifest files for now
        )
        return {"status": "ok", "message": f"Plugin '{manifest.name}' registered. You can now enable it."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register plugin: {e}"
        )

@router.post("/enable")
async def enable_plugin(request: PluginEnableDisableRequest, user: dict = Depends(get_current_user)):
    plugin = await database.get_plugin(request.plugin_name)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{request.plugin_name}' not found."
        )
    
    if plugin["enabled"]:
        return {"status": "ok", "message": f"Plugin '{request.plugin_name}' is already enabled."}

    # Dynamic loading of plugin cog
    from bot import bot as discord_bot
    try:
        await discord_bot._load_plugin(plugin["name"], plugin["cog_path"])
        await database.set_plugin_enabled(plugin["name"], True)
        return {"status": "ok", "message": f"Plugin '{request.plugin_name}' enabled successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable plugin '{request.plugin_name}': {e}"
        )

@router.post("/disable")
async def disable_plugin(request: PluginEnableDisableRequest, user: dict = Depends(get_current_user)):
    plugin = await database.get_plugin(request.plugin_name)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{request.plugin_name}' not found."
        )
    
    if not plugin["enabled"]:
        return {"status": "ok", "message": f"Plugin '{request.plugin_name}' is already disabled."}

    # Dynamic unloading of plugin cog
    from bot import bot as discord_bot
    try:
        await discord_bot._unload_plugin(plugin["name"], plugin["cog_path"])
        await database.set_plugin_enabled(plugin["name"], False)
        return {"status": "ok", "message": f"Plugin '{request.plugin_name}' disabled successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable plugin '{request.plugin_name}': {e}"
        )

@router.delete("/{plugin_name}")
async def delete_plugin(plugin_name: str, user: dict = Depends(get_current_user)):
    plugin = await database.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_name}' not found."
        )
    
    if plugin["enabled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plugin '{plugin_name}' is currently enabled. Please disable it first."
        )

    # Delete from DB
    try:
        await database.delete_plugin(plugin_name)
        # TODO: In a more robust system, this would also delete plugin files
        return {"status": "ok", "message": f"Plugin '{plugin_name}' deleted successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete plugin '{plugin_name}': {e}"
        )
