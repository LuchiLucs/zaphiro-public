import pytest


@pytest.mark.anyio
async def test_alogin_flow_success(client):
    response = await client.post(
        "/auth/token", data={"username": "user", "password": "user", "scope": "user"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.anyio
async def test_alogin_flow_manager_with_descalated_user_scope(client):
    response = await client.post(
        "/auth/token",
        data={"username": "manager", "password": "manager", "scope": "user"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.anyio
async def test_alogin_flow_invalid_scope(client):
    response = await client.post(
        "/auth/token", data={"username": "user", "password": "user", "scope": "foobar"}
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_alogin_flow_invalid_password(client):
    response = await client.post(
        "/auth/token", data={"username": "user", "password": "foobar", "scope": "user"}
    )
    assert response.status_code == 401
