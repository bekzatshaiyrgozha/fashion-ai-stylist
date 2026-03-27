import pytest


async def test_generate_outfit_casual(client, auth_token):
    r = await client.post("/outfit/generate", json={"style": "casual"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


async def test_generate_outfit_office(client, auth_token):
    r = await client.post("/outfit/generate", json={"style": "office"})
    assert r.status_code == 200


async def test_generate_outfit_no_auth(client):
    r = await client.post("/outfit/generate", json={"style": "casual"})
    assert r.status_code == 401


async def test_get_outfit_history(client, auth_token):
    r = await client.get("/outfit/history")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
