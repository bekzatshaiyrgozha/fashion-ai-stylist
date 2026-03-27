async def test_list_categories(client):
    r = await client.get("/categories/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


async def test_create_category_admin(client, admin_token):
    payload = {"name": "NewCat", "slug": "newcat"}
    # admin_token ensures cookies set
    r = await client.post("/admin/categories/", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "NewCat"
