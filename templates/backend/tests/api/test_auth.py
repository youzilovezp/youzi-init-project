"""认证相关接口测试示例。

使用 fixture `admin_credentials` 从 settings 读取——避免硬编码。
需要真实 dev DB 已 seed admin（如未 seed，先启动一次后端）。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_credentials: dict[str, str]):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": admin_credentials["username"],
            "password": admin_credentials["password"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "nobody", "password": "wrong"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] != 0
