from typing import List, Optional
import os
import time
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from app.api.dependencies import get_current_user
from app.schemas import admin_schemas as schemas

router = APIRouter()


def require_admin(current_user = Depends(get_current_user)):
    # support both dict-like users with 'role' and ORM objects with 'is_admin'
    if not current_user:
        raise HTTPException(status_code=403, detail="Admins only")
    role = getattr(current_user, "role", None)
    is_admin = getattr(current_user, "is_admin", None)
    if role == "admin" or is_admin is True:
        return current_user
    raise HTTPException(status_code=403, detail="Admins only")
    return current_user


# Placeholder in-memory stores (replace with DB calls)
_PRODUCTS: List[dict] = [
    {"id": 1, "name": "Demo Shirt", "description": "Demo", "price": 49.9, "category_id": 1, "sizes": ["S","M"], "colors": ["black"], "stock": True, "images": []}
]
_CATEGORIES: List[dict] = [{"id": 1, "name": "Tops", "slug": "tops"}]
_USERS: List[dict] = [{"id": 1, "email": "user@example.com", "role": "user"}, {"id": 2, "email": "admin@example.com", "role": "admin"}]


@router.get("/products/", response_model=List[schemas.ProductOut])
async def admin_products_list(
    category: Optional[int] = Query(None),
    color: Optional[str] = Query(None),
    size: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    current=Depends(require_admin),
):
    results = _PRODUCTS.copy()
    if category is not None:
        results = [p for p in results if p.get("category_id") == category]
    if color:
        results = [p for p in results if color in p.get("colors", [])]
    if size:
        results = [p for p in results if size in p.get("sizes", [])]
    if min_price is not None:
        results = [p for p in results if p.get("price") >= min_price]
    if max_price is not None:
        results = [p for p in results if p.get("price") <= max_price]
    return results


@router.post("/products/", response_model=schemas.ProductOut)
async def admin_create_product(item: schemas.ProductCreate, current=Depends(require_admin)):
    new_id = max((p["id"] for p in _PRODUCTS), default=0) + 1
    entry = item.model_dump()
    entry.update({"id": new_id, "images": []})
    _PRODUCTS.append(entry)
    return entry


@router.put("/products/{product_id}", response_model=schemas.ProductOut)
async def admin_update_product(product_id: int, item: schemas.ProductUpdate, current=Depends(require_admin)):
    prod = next((p for p in _PRODUCTS if p["id"] == product_id), None)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = item.model_dump(exclude_unset=True)
    prod.update(update_data)
    return prod


@router.delete("/products/{product_id}")
async def admin_delete_product(product_id: int, current=Depends(require_admin)):
    global _PRODUCTS
    _PRODUCTS = [p for p in _PRODUCTS if p["id"] != product_id]
    return {"message": "deleted", "product_id": product_id}


@router.post("/products/{product_id}/image")
async def admin_upload_product_image(product_id: int, file: UploadFile = File(...), current=Depends(require_admin)):
    prod = next((p for p in _PRODUCTS if p["id"] == product_id), None)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    images_dir = os.path.join(os.getcwd(), "static", "images")
    os.makedirs(images_dir, exist_ok=True)
    timestamp = int(time.time())
    filename = f"product_{product_id}_{timestamp}_{file.filename}"
    dest = os.path.join(images_dir, filename)
    with open(dest, "wb") as f:
        f.write(await file.read())
    url = f"/static/images/{filename}"
    prod.setdefault("images", []).append(url)
    return {"url": url}


@router.patch("/products/{product_id}/stock")
async def admin_update_stock(product_id: int, stock: bool, current=Depends(require_admin)):
    prod = next((p for p in _PRODUCTS if p["id"] == product_id), None)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    prod["stock"] = stock
    return {"id": product_id, "stock": stock}


@router.get("/categories/", response_model=List[schemas.CategoryOut])
async def admin_list_categories(current=Depends(require_admin)):
    return _CATEGORIES


@router.post("/categories/", response_model=schemas.CategoryOut)
async def admin_create_category(cat: schemas.CategoryCreate, current=Depends(require_admin)):
    new_id = max((c["id"] for c in _CATEGORIES), default=0) + 1
    entry = {"id": new_id, "name": cat.name, "slug": cat.slug or cat.name.lower().replace(" ", "-")}
    _CATEGORIES.append(entry)
    return entry


@router.put("/categories/{category_id}")
async def admin_rename_category(category_id: int, cat: schemas.CategoryCreate, current=Depends(require_admin)):
    c = next((c for c in _CATEGORIES if c["id"] == category_id), None)
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    c["name"] = cat.name
    c["slug"] = cat.slug or cat.name.lower().replace(" ", "-")
    return c


@router.delete("/categories/{category_id}")
async def admin_delete_category(category_id: int, current=Depends(require_admin)):
    global _CATEGORIES
    _CATEGORIES = [c for c in _CATEGORIES if c["id"] != category_id]
    return {"message": "deleted", "category_id": category_id}


@router.get("/users/", response_model=List[dict])
async def admin_list_users(current=Depends(require_admin)):
    return _USERS


@router.delete("/users/{user_id}")
async def admin_delete_user(user_id: int, current=Depends(require_admin)):
    global _USERS
    _USERS = [u for u in _USERS if u["id"] != user_id]
    return {"message": "deleted", "user_id": user_id}


@router.patch("/users/{user_id}/role")
async def admin_change_user_role(user_id: int, data: schemas.UserRoleUpdate, current=Depends(require_admin)):
    u = next((u for u in _USERS if u["id"] == user_id), None)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u["role"] = data.role
    return u


@router.get("/stats/", response_model=schemas.AdminStats)
async def admin_stats(current=Depends(require_admin)):
    return schemas.AdminStats(total_products=len(_PRODUCTS), total_users=len(_USERS), total_categories=len(_CATEGORIES))
