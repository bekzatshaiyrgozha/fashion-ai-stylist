import pytest


async def test_register_success(client):
    payload = {"first_name": "A", "last_name": "B", "email": "a@example.com", "password": "pass"}
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 201


async def test_register_duplicate_email(client):
    payload = {"first_name": "A", "last_name": "B", "email": "dup@example.com", "password": "pass"}
    r1 = await client.post("/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/auth/register", json=payload)
    assert r2.status_code == 400


async def test_login_success(client):
    payload = {"first_name": "L", "last_name": "I", "email": "login@example.com", "password": "mypwd"}
    await client.post("/auth/register", json=payload)
    r = await client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert r.status_code == 200


async def test_login_wrong_password(client):
    payload = {"first_name": "W", "last_name": "P", "email": "wp@example.com", "password": "right"}
    await client.post("/auth/register", json=payload)
    r = await client.post("/auth/login", json={"email": payload["email"], "password": "wrong"})
    assert r.status_code == 400


async def test_get_profile_authorized(client):
    payload = {"first_name": "P", "last_name": "U", "email": "profile@example.com", "password": "pwd"}
    await client.post("/auth/register", json=payload)
    await client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    r = await client.get("/auth/profile")
    assert r.status_code == 200


async def test_get_profile_unauthorized(client):
    r = await client.get("/auth/profile")
    assert r.status_code == 401
