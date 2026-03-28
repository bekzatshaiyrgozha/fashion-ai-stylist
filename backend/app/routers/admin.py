from typing import List, Optional
import os
import time
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from app.api.dependencies import get_current_user
from app.schemas import admin_schemas as schemas
from app.services import catalog_store_db as catalog_store

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


@router.get("/products/", response_model=List[schemas.ProductOut])
async def admin_products_list(
    category: Optional[int] = Query(None),
    color: Optional[str] = Query(None),
    size: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    current=Depends(require_admin),
):
    return await catalog_store.list_products(
        category_id=category,
        color=color,
        size=size,
        min_price=min_price,
        max_price=max_price,
    )


@router.post("/products/", response_model=schemas.ProductOut)
async def admin_create_product(item: schemas.ProductCreate, current=Depends(require_admin)):
    return await catalog_store.create_product(item.model_dump())


@router.put("/products/{product_id}", response_model=schemas.ProductOut)
async def admin_update_product(product_id: int, item: schemas.ProductUpdate, current=Depends(require_admin)):
    prod = await catalog_store.get_product(product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return await catalog_store.update_product(product_id, item.model_dump(exclude_unset=True))


@router.delete("/products/{product_id}")
async def admin_delete_product(product_id: int, current=Depends(require_admin)):
    await catalog_store.delete_product(product_id)
    return {"message": "deleted", "product_id": product_id}


@router.post("/products/{product_id}/image")
async def admin_upload_product_image(product_id: int, file: UploadFile = File(...), current=Depends(require_admin)):
    prod = await catalog_store.get_product(product_id)
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
    images = list(prod.get("images") or [])
    images.append(url)
    await catalog_store.update_product(product_id, {"images": images})
    return {"url": url}


@router.patch("/products/{product_id}/stock")
async def admin_update_stock(product_id: int, stock: bool, current=Depends(require_admin)):
    prod = await catalog_store.get_product(product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    await catalog_store.update_product(product_id, {"stock": stock})
    return {"id": product_id, "stock": stock}


@router.get("/categories/", response_model=List[schemas.CategoryOut])
async def admin_list_categories(current=Depends(require_admin)):
    return await catalog_store.list_categories()


@router.post("/categories/", response_model=schemas.CategoryOut)
async def admin_create_category(cat: schemas.CategoryCreate, current=Depends(require_admin)):
    return await catalog_store.create_category(cat.name, cat.slug)


@router.put("/categories/{category_id}")
async def admin_rename_category(category_id: int, cat: schemas.CategoryCreate, current=Depends(require_admin)):
    c = await catalog_store.update_category(category_id, cat.name, cat.slug)
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    return c


@router.delete("/categories/{category_id}")
async def admin_delete_category(category_id: int, current=Depends(require_admin)):
    await catalog_store.delete_category(category_id)
    return {"message": "deleted", "category_id": category_id}


@router.get("/users/", response_model=List[dict])
async def admin_list_users(current=Depends(require_admin)):
    return await catalog_store.list_users()


@router.delete("/users/{user_id}")
async def admin_delete_user(user_id: int, current=Depends(require_admin)):
    await catalog_store.delete_user(user_id)
    return {"message": "deleted", "user_id": user_id}


@router.patch("/users/{user_id}/role")
async def admin_change_user_role(user_id: int, data: schemas.UserRoleUpdate, current=Depends(require_admin)):
    u = await catalog_store.update_user_role(user_id, data.role)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


@router.get("/stats/", response_model=schemas.AdminStats)
async def admin_stats(current=Depends(require_admin)):
    st = await catalog_store.stats()
    return schemas.AdminStats(
        total_products=st["total_products"],
        total_users=st["total_users"],
        total_categories=st["total_categories"],
    )
