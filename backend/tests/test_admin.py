import pytest


async def test_admin_create_product(client, admin_token):
    payload = {"name": "P1", "description": "d", "price": 10.0, "category_id": 1, "sizes": [], "colors": [], "stock": True}
    r = await client.post("/admin/products/", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "P1"


async def test_admin_create_product_no_auth(client):
    payload = {"name": "P2", "description": "d", "price": 11.0, "category_id": 1}
    r = await client.post("/admin/products/", json=payload)
    assert r.status_code == 401 or r.status_code == 403


async def test_admin_create_product_user_role(client, auth_token):
    payload = {"name": "P3", "description": "d", "price": 12.0, "category_id": 1}
    r = await client.post("/admin/products/", json=payload)
    assert r.status_code == 403 or r.status_code == 401


async def test_admin_update_product(client, admin_token):
    # create first
    payload = {"name": "P4", "description": "d", "price": 13.0, "category_id": 1}
    r = await client.post("/admin/products/", json=payload)
    assert r.status_code == 200
    pid = r.json().get("id")
    up = {"price": 15.0}
    r2 = await client.put(f"/admin/products/{pid}", json=up)
    assert r2.status_code == 200


async def test_admin_delete_product(client, admin_token):
    payload = {"name": "P5", "description": "d", "price": 14.0, "category_id": 1}
    r = await client.post("/admin/products/", json=payload)
    pid = r.json().get("id")
    r2 = await client.delete(f"/admin/products/{pid}")
    assert r2.status_code == 200


async def test_admin_update_stock(client, admin_token):
    payload = {"name": "P6", "description": "d", "price": 15.0, "category_id": 1}
    r = await client.post("/admin/products/", json=payload)
    pid = r.json().get("id")
    r2 = await client.patch(f"/admin/products/{pid}/stock", params={"stock": False})
    assert r2.status_code == 200


async def test_admin_get_stats(client, admin_token):
    r = await client.get("/admin/stats/")
    assert r.status_code == 200
    data = r.json()
    assert "total_products" in data


async def test_admin_create_category(client, admin_token):
    payload = {"name": "CNew", "slug": "cnew"}
    r = await client.post("/admin/categories/", json=payload)
    assert r.status_code == 200


async def test_admin_delete_category(client, admin_token):
    payload = {"name": "CDel", "slug": "cdel"}
    r = await client.post("/admin/categories/", json=payload)
    cid = r.json().get("id")
    r2 = await client.delete(f"/admin/categories/{cid}")
    assert r2.status_code == 200


async def test_admin_get_users(client, admin_token):
    r = await client.get("/admin/users/")
    assert r.status_code == 200


async def test_admin_change_user_role(client, admin_token):
    # create a user then change role
    payload = {"first_name": "R", "last_name": "U", "email": "role@example.com", "password": "pw"}
    await client.post("/auth/register", json=payload)
    # fetch users
    r = await client.get("/admin/users/")
    users = r.json()
    uid = users[0]["id"] if users else 1
    r2 = await client.patch(f"/admin/users/{uid}/role", json={"role": "admin"})
    assert r2.status_code == 200
