from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import delete, func, select, update

from app.db.db_config import async_session_maker
from app.db.models import Category, Product, User


async def ensure_seed_data() -> None:
    """Seed minimal catalog for first start / tests.

    Safe to call many times.
    """
    async with async_session_maker() as session:
        count_categories = await session.scalar(select(func.count()).select_from(Category))
        count_products = await session.scalar(select(func.count()).select_from(Product))
        # if any catalog data exists, don't reseed to avoid PK conflicts
        if (count_categories or 0) > 0 or (count_products or 0) > 0:
            return

        categories = [
            Category(id=1, name="Tops", slug="tops"),
            Category(id=2, name="Bottoms", slug="bottoms"),
            Category(id=3, name="Shoes", slug="shoes"),
            Category(id=4, name="Accessories", slug="accessories"),
        ]
        session.add_all(categories)
        session.add_all(
            [
                Product(
                    id=1,
                    name="Demo Shirt",
                    description="Basic casual shirt",
                    price=49.9,
                    category_id=1,
                    sizes=["S", "M"],
                    colors=["black"],
                    stock=True,
                    images=[],
                    style_tags=["casual"],
                    scenarios=["daily", "office"],
                ),
                Product(
                    id=2,
                    name="Sport Joggers",
                    description="Comfortable sporty pants",
                    price=59.9,
                    category_id=2,
                    sizes=["M", "L"],
                    colors=["black", "gray"],
                    stock=True,
                    images=[],
                    style_tags=["sport", "casual"],
                    scenarios=["daily", "gym"],
                ),
                Product(
                    id=3,
                    name="White Sneakers",
                    description="Universal sneakers",
                    price=89.9,
                    category_id=3,
                    sizes=["40", "41", "42"],
                    colors=["white"],
                    stock=True,
                    images=[],
                    style_tags=["sport", "casual"],
                    scenarios=["daily", "travel"],
                ),
            ]
        )
        await session.commit()


async def list_categories() -> List[dict]:
    await ensure_seed_data()
    async with async_session_maker() as session:
        rows = (await session.execute(select(Category))).scalars().all()
        return [{"id": c.id, "name": c.name, "slug": c.slug} for c in rows]


async def create_category(name: str, slug: Optional[str]) -> dict:
    async with async_session_maker() as session:
        row = Category(name=name, slug=slug or name.lower().replace(" ", "-"))
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return {"id": row.id, "name": row.name, "slug": row.slug}


async def update_category(category_id: int, name: str, slug: Optional[str]) -> Optional[dict]:
    async with async_session_maker() as session:
        row = await session.get(Category, category_id)
        if not row:
            return None
        row.name = name
        row.slug = slug or name.lower().replace(" ", "-")
        await session.commit()
        return {"id": row.id, "name": row.name, "slug": row.slug}


async def delete_category(category_id: int) -> bool:
    async with async_session_maker() as session:
        res = await session.execute(delete(Category).where(Category.id == category_id))
        await session.commit()
        return (res.rowcount or 0) > 0


def _product_to_dict(row: Product) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "price": row.price,
        "category_id": row.category_id,
        "sizes": row.sizes or [],
        "colors": row.colors or [],
        "style_tags": row.style_tags or [],
        "scenarios": row.scenarios or [],
        "images": row.images or [],
        "stock": row.stock,
    }


async def list_products(
    category_id: Optional[int] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[dict]:
    await ensure_seed_data()
    async with async_session_maker() as session:
        rows = (await session.execute(select(Product))).scalars().all()
        data = [_product_to_dict(r) for r in rows]
        if category_id is not None:
            data = [p for p in data if p.get("category_id") == category_id]
        if color:
            data = [p for p in data if color in p.get("colors", [])]
        if size:
            data = [p for p in data if size in p.get("sizes", [])]
        if min_price is not None:
            data = [p for p in data if (p.get("price") or 0) >= min_price]
        if max_price is not None:
            data = [p for p in data if (p.get("price") or 0) <= max_price]
        return data


async def get_product(product_id: int) -> Optional[dict]:
    await ensure_seed_data()
    async with async_session_maker() as session:
        row = await session.get(Product, product_id)
        if not row:
            return None
        return _product_to_dict(row)


async def create_product(data: dict) -> dict:
    async with async_session_maker() as session:
        row = Product(
            name=data["name"],
            description=data.get("description"),
            price=data.get("price") or 0,
            category_id=data.get("category_id") or 1,
            sizes=data.get("sizes") or [],
            colors=data.get("colors") or [],
            style_tags=data.get("style_tags") or [],
            scenarios=data.get("scenarios") or [],
            images=data.get("images") or [],
            stock=bool(data.get("stock", True)),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return _product_to_dict(row)


async def update_product(product_id: int, data: dict) -> Optional[dict]:
    async with async_session_maker() as session:
        row = await session.get(Product, product_id)
        if not row:
            return None
        for key, value in data.items():
            setattr(row, key, value)
        await session.commit()
        await session.refresh(row)
        return _product_to_dict(row)


async def delete_product(product_id: int) -> bool:
    async with async_session_maker() as session:
        res = await session.execute(delete(Product).where(Product.id == product_id))
        await session.commit()
        return (res.rowcount or 0) > 0


async def list_users() -> List[dict]:
    async with async_session_maker() as session:
        rows = (await session.execute(select(User))).scalars().all()
        return [{"id": u.id, "email": u.email, "role": "admin" if u.is_admin else "user"} for u in rows]


async def delete_user(user_id: int) -> bool:
    async with async_session_maker() as session:
        res = await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
        return (res.rowcount or 0) > 0


async def update_user_role(user_id: int, role: str) -> Optional[dict]:
    async with async_session_maker() as session:
        row = await session.get(User, user_id)
        if not row:
            return None
        row.is_admin = role == "admin"
        await session.commit()
        return {"id": row.id, "email": row.email, "role": "admin" if row.is_admin else "user"}


async def stats() -> dict:
    async with async_session_maker() as session:
        total_products = await session.scalar(select(func.count()).select_from(Product))
        total_users = await session.scalar(select(func.count()).select_from(User))
        total_categories = await session.scalar(select(func.count()).select_from(Category))
        return {
            "total_products": int(total_products or 0),
            "total_users": int(total_users or 0),
            "total_categories": int(total_categories or 0),
        }


async def categories_map() -> Dict[int, str]:
    await ensure_seed_data()
    async with async_session_maker() as session:
        rows = (await session.execute(select(Category))).scalars().all()
        return {c.id: c.slug for c in rows}
