import pytest


async def test_get_all_products(client):
    r = await client.get("/products/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


async def test_get_product_by_id(client):
    r = await client.get("/products/1")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1 or data.get("id") == 1


async def test_get_product_not_found(client):
    r = await client.get("/products/9999")
    assert r.status_code == 404


async def test_filter_by_category(client):
    r = await client.get("/products/?category=tops")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
