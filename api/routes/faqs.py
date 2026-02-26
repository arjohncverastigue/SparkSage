from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from api.deps import get_current_user
import db

router = APIRouter()

class FAQBase(BaseModel):
    question: str
    answer: str
    match_keywords: str

class FAQCreate(FAQBase):
    pass

class FAQResponse(FAQBase):
    id: int
    guild_id: str
    times_used: int
    created_by: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[FAQResponse])
async def list_faqs(
    user: dict = Depends(get_current_user),
    guild_id: str | None = Query(None, description="Optional: Filter FAQs by guild ID")
):
    faqs = await db.get_faqs(guild_id=guild_id) # Now supports optional guild_id
    return faqs


@router.post("", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    faq: FAQCreate,
    user: dict = Depends(get_current_user),
    guild_id: str = Query(..., description="The ID of the guild to add the FAQ to") # Required query param for guild_id
):
    new_faq_id = await db.add_faq(
        guild_id=guild_id,
        question=faq.question,
        answer=faq.answer,
        match_keywords=faq.match_keywords,
        created_by=user["sub"]
    )
    created_faq = await db.get_faq_by_id(new_faq_id)
    if not created_faq:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created FAQ.")
    return created_faq


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq_endpoint(
    faq_id: int,
    user: dict = Depends(get_current_user),
    guild_id: str = Query(..., description="The ID of the guild the FAQ belongs to") # Required query param for guild_id
):
    existing_faq = await db.get_faq_by_id(faq_id)
    if not existing_faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    # Ensure the FAQ belongs to the specified guild for security
    if existing_faq["guild_id"] != guild_id:
        raise HTTPException(status_code=403, detail="Forbidden: FAQ does not belong to this guild")

    await db.delete_faq(faq_id)
    return