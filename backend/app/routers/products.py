from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from app.services import catalog_store_db as catalog_store
from app.api.dependencies import get_current_user

router = APIRouter()


class ProductBase(BaseModel):
    name: str
    description: Optional[str]
    price: float
    sizes: Optional[List[str]] = []
    colors: Optional[List[str]] = []
    category: Optional[str]


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int


@router.get("/", response_model=List[Product])
async def list_products(category: Optional[str] = Query(None)):
    rows = await catalog_store.list_products()
    cat_map = await catalog_store.categories_map()
    data = []
    for p in rows:
        category_slug = cat_map.get(p.get("category_id"), "other")
        if category and category_slug != category:
            continue
        data.append(
            Product(
                id=p["id"],
                name=p["name"],
                description=p.get("description"),
                price=p.get("price", 0),
                sizes=p.get("sizes", []),
                colors=p.get("colors", []),
                category=category_slug,
            )
        )
    return data


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: int):
    p = await catalog_store.get_product(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    cat_map = await catalog_store.categories_map()
    return Product(
        id=p["id"],
        name=p["name"],
        description=p.get("description"),
        price=p.get("price", 0),
        sizes=p.get("sizes", []),
        colors=p.get("colors", []),
        category=cat_map.get(p.get("category_id"), "other"),
    )


@router.post("/", response_model=Product)
async def create_product(item: ProductCreate, current_user=Depends(get_current_user)):
    # Check if user is admin
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    cat_map = await catalog_store.categories_map()
    # map external category slug -> category_id fallback 1
    reverse = {v: k for k, v in cat_map.items()}
    row = await catalog_store.create_product(
        {
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "sizes": item.sizes or [],
            "colors": item.colors or [],
            "stock": True,
            "category_id": reverse.get(item.category or "tops", 1),
            "style_tags": [item.category or "casual"],
            "scenarios": ["daily"],
        }
    )
    return Product(id=row["id"], **item.dict())


@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: int, item: ProductCreate, current_user=Depends(get_current_user)):
    # Check if user is admin
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    p = await catalog_store.get_product(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    await catalog_store.update_product(
        product_id,
        {
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "sizes": item.sizes or [],
            "colors": item.colors or [],
        },
    )
    return Product(id=product_id, **item.dict())


@router.delete("/{product_id}")
async def delete_product(product_id: int, current_user=Depends(get_current_user)):
    # Check if user is admin
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    await catalog_store.delete_product(product_id)
    return {"message": "deleted", "product_id": product_id}
