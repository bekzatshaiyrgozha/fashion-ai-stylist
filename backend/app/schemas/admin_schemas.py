from typing import List, Optional, Literal
from pydantic import BaseModel, constr


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: int
    sizes: Optional[List[str]] = []
    colors: Optional[List[str]] = []
    stock: bool = True


class ProductOut(ProductCreate):
    id: int


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    sizes: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    stock: Optional[bool] = None


class CategoryCreate(BaseModel):
    name: constr(min_length=1)
    slug: Optional[constr(min_length=1)]


class CategoryOut(CategoryCreate):
    id: int


class UserRoleUpdate(BaseModel):
    role: Literal["user", "admin"]


class AdminStats(BaseModel):
    total_products: int
    total_users: int
    total_categories: int
