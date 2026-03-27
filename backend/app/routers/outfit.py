from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.services import OutfitGenerator
from app.services import catalog_store_db as catalog_store

router = APIRouter()
generator = OutfitGenerator()
_HISTORY: dict[str, List[dict]] = {}


class OutfitGenerateRequest(BaseModel):
    style: Optional[str] = None
    scenario: Optional[str] = None
    sizes: Optional[List[str]] = []
    colors: Optional[List[str]] = []


class OutfitItem(BaseModel):
    id: int
    name: str
    price: float


class OutfitResponse(BaseModel):
    outfit: dict[str, Optional[OutfitItem]]
    ai_explanation: str
    total_price: float


@router.post("/generate", response_model=OutfitResponse)
async def generate_outfit(req: OutfitGenerateRequest, current=Depends(get_current_user)):
    products = await catalog_store.list_products()
    cat_map = await catalog_store.categories_map()

    payload = await generator.generate_with_ai(
        products=products,
        categories_map=cat_map,
        style=req.style,
        scenario=req.scenario,
        sizes=req.sizes,
        colors=req.colors,
    )

    user_id = str(getattr(current, "id", "anonymous"))
    _HISTORY.setdefault(user_id, []).append(payload)
    return OutfitResponse(**payload)


@router.get("/history", response_model=List[OutfitResponse])
async def outfit_history(current=Depends(get_current_user)):
    user_id = str(getattr(current, "id", "anonymous"))
    rows = _HISTORY.get(user_id, [])
    return [OutfitResponse(**row) for row in rows]
