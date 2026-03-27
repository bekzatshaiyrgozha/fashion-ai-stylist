from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api.dependencies import get_current_user

router = APIRouter()


class OutfitGenerateRequest(BaseModel):
    style: Optional[str] = None
    scenario: Optional[str] = None
    sizes: Optional[List[str]] = []
    colors: Optional[List[str]] = []


class OutfitItem(BaseModel):
    product_id: int
    name: str
    category: str


class OutfitResponse(BaseModel):
    items: List[OutfitItem]
    message: Optional[str]


@router.post("/generate", response_model=OutfitResponse)
async def generate_outfit(req: OutfitGenerateRequest, current=Depends(get_current_user)):
    # TODO: call OutfitGenerator service (embeddings + faiss or rules)
    demo = [OutfitItem(product_id=1, name="Demo Shirt", category="tops"), OutfitItem(product_id=3, name="Demo Jeans", category="bottoms")]
    return OutfitResponse(items=demo, message="generated (placeholder)")


@router.get("/history", response_model=List[OutfitResponse])
async def outfit_history(current=Depends(get_current_user)):
    # TODO: fetch history from DB
    return []
