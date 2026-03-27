from __future__ import annotations

from typing import Dict, List, Optional


_CATEGORIES: List[dict] = [
    {"id": 1, "name": "Tops", "slug": "tops"},
    {"id": 2, "name": "Bottoms", "slug": "bottoms"},
    {"id": 3, "name": "Shoes", "slug": "shoes"},
    {"id": 4, "name": "Accessories", "slug": "accessories"},
]

_PRODUCTS: List[dict] = [
    {
        "id": 1,
        "name": "Demo Shirt",
        "description": "Basic casual shirt",
        "price": 49.9,
        "category_id": 1,
        "sizes": ["S", "M"],
        "colors": ["black"],
        "stock": True,
        "images": [],
        "style_tags": ["casual"],
        "scenarios": ["daily", "office"],
    },
    {
        "id": 2,
        "name": "Sport Joggers",
        "description": "Comfortable sporty pants",
        "price": 59.9,
        "category_id": 2,
        "sizes": ["M", "L"],
        "colors": ["black", "gray"],
        "stock": True,
        "images": [],
        "style_tags": ["sport", "casual"],
        "scenarios": ["daily", "gym"],
    },
    {
        "id": 3,
        "name": "White Sneakers",
        "description": "Universal sneakers",
        "price": 89.9,
        "category_id": 3,
        "sizes": ["40", "41", "42"],
        "colors": ["white"],
        "stock": True,
        "images": [],
        "style_tags": ["sport", "casual"],
        "scenarios": ["daily", "travel"],
    },
]

_USERS: List[dict] = [
    {"id": 1, "email": "user@example.com", "role": "user"},
    {"id": 2, "email": "admin@example.com", "role": "admin"},
]


def list_categories() -> List[dict]:
    return _CATEGORIES


def create_category(name: str, slug: Optional[str]) -> dict:
    new_id = max((c["id"] for c in _CATEGORIES), default=0) + 1
    entry = {"id": new_id, "name": name, "slug": slug or name.lower().replace(" ", "-")}
    _CATEGORIES.append(entry)
    return entry


def update_category(category_id: int, name: str, slug: Optional[str]) -> Optional[dict]:
    row = next((c for c in _CATEGORIES if c["id"] == category_id), None)
    if not row:
        return None
    row["name"] = name
    row["slug"] = slug or name.lower().replace(" ", "-")
    return row


def delete_category(category_id: int) -> bool:
    global _CATEGORIES
    before = len(_CATEGORIES)
    _CATEGORIES = [c for c in _CATEGORIES if c["id"] != category_id]
    return len(_CATEGORIES) < before


def list_products(
    category_id: Optional[int] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[dict]:
    rows = _PRODUCTS.copy()
    if category_id is not None:
        rows = [p for p in rows if p.get("category_id") == category_id]
    if color:
        rows = [p for p in rows if color in p.get("colors", [])]
    if size:
        rows = [p for p in rows if size in p.get("sizes", [])]
    if min_price is not None:
        rows = [p for p in rows if p.get("price", 0) >= min_price]
    if max_price is not None:
        rows = [p for p in rows if p.get("price", 0) <= max_price]
    return rows


def get_product(product_id: int) -> Optional[dict]:
    return next((p for p in _PRODUCTS if p["id"] == product_id), None)


def create_product(data: dict) -> dict:
    new_id = max((p["id"] for p in _PRODUCTS), default=0) + 1
    row = data.copy()
    row["id"] = new_id
    row.setdefault("images", [])
    row.setdefault("style_tags", [])
    row.setdefault("scenarios", [])
    _PRODUCTS.append(row)
    return row


def update_product(product_id: int, data: dict) -> Optional[dict]:
    row = get_product(product_id)
    if not row:
        return None
    row.update(data)
    return row


def delete_product(product_id: int) -> bool:
    global _PRODUCTS
    before = len(_PRODUCTS)
    _PRODUCTS = [p for p in _PRODUCTS if p["id"] != product_id]
    return len(_PRODUCTS) < before


def list_users() -> List[dict]:
    return _USERS


def delete_user(user_id: int) -> bool:
    global _USERS
    before = len(_USERS)
    _USERS = [u for u in _USERS if u["id"] != user_id]
    return len(_USERS) < before


def update_user_role(user_id: int, role: str) -> Optional[dict]:
    row = next((u for u in _USERS if u["id"] == user_id), None)
    if not row:
        return None
    row["role"] = role
    return row


def stats() -> dict:
    return {
        "total_products": len(_PRODUCTS),
        "total_users": len(_USERS),
        "total_categories": len(_CATEGORIES),
    }


def categories_map() -> Dict[int, str]:
    return {c["id"]: c["slug"] for c in _CATEGORIES}
