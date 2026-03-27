from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

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


def fake_admin_user():
    # TODO: replace with real auth + role check
    return {"id": "admin_1", "role": "admin"}


@router.get("/", response_model=List[Product])
async def list_products():
    # TODO: fetch from DB, pagination
    return [Product(id=1, name="Demo Shirt", description="A demo", price=49.9, sizes=["S","M"], colors=["black"], category="tops")]


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: int):
    # TODO: fetch real product
    if product_id != 1:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(id=1, name="Demo Shirt", description="A demo", price=49.9, sizes=["S","M"], colors=["black"], category="tops")


@router.post("/", response_model=Product)
async def create_product(item: ProductCreate, current=Depends(fake_admin_user)):
    # TODO: insert into DB
    return Product(id=2, **item.dict())


@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: int, item: ProductCreate, current=Depends(fake_admin_user)):
    # TODO: update DB record
    return Product(id=product_id, **item.dict())


@router.delete("/{product_id}")
async def delete_product(product_id: int, current=Depends(fake_admin_user)):
    # TODO: delete from DB
    return {"message": "deleted", "product_id": product_id}
