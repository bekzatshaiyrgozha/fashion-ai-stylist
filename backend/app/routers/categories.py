from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from app.db.db_config import async_session_maker
from app.db.models.category import Category as CategoryModel
from app.api.dependencies import get_current_user

router = APIRouter()


class Category(BaseModel):
    id: int
    name: str
    slug: str


class CategoryCreate(BaseModel):
    name: str
    slug: str


@router.get("/", response_model=List[Category])
async def list_categories():
    """Fetch all categories from database"""
    async with async_session_maker() as session:
        result = await session.execute(select(CategoryModel))
        rows = result.scalars().all()
        return [Category(id=r.id, name=r.name, slug=r.slug) for r in rows]


@router.post("/", response_model=Category, status_code=201)
async def create_category(cat: CategoryCreate, current_user=Depends(get_current_user)):
    """Create new category (admin only)"""
    # Check if user is admin
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    async with async_session_maker() as session:
        # Check if slug already exists
        existing = await session.execute(
            select(CategoryModel).where(CategoryModel.slug == cat.slug)
        )
        if existing.scalars().first():
            raise HTTPException(status_code=409, detail="Category slug already exists")
        
        # Insert new category
        new_cat = CategoryModel(name=cat.name, slug=cat.slug)
        session.add(new_cat)
        await session.commit()
        await session.refresh(new_cat)
        return Category(id=new_cat.id, name=new_cat.name, slug=new_cat.slug)
