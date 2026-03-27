from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()


class Category(BaseModel):
    id: int
    name: str
    description: Optional[str]


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str]


def fake_admin_user():
    return {"id": "admin_1", "role": "admin"}


@router.get("/", response_model=List[Category])
async def list_categories():
    # TODO: fetch from DB
    return [Category(id=1, name="Tops", description="Upper garments")]


@router.post("/", response_model=Category)
async def create_category(cat: CategoryCreate, current=Depends(fake_admin_user)):
    # TODO: insert into DB
    return Category(id=2, name=cat.name, description=cat.description)
