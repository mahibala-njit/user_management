import pytest
from httpx import AsyncClient
from datetime import datetime
from app.models.user_model import UserRole

BASE_URL = "/users-search"
ADVANCED_SEARCH_URL = "/users-advanced-search"

@pytest.mark.asyncio
async def test_basic_search_users(async_client: AsyncClient, admin_token: str):
    params = {
        "username": "john_doe",
        "email": "john.doe@example.com",
        "role": "ADMIN",
        "is_locked": False,
        "skip": 0,
        "limit": 10
    }
    response = await async_client.get(
        BASE_URL,
        params=params,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "links" in data


@pytest.mark.asyncio
async def test_basic_search_success(async_client: AsyncClient, admin_token: str):
    response = await async_client.get(
        f"{BASE_URL}?username=john_doe&email=john.doe@example.com&role=ADMIN&is_locked=false&skip=0&limit=10",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 0
    assert data["page"] == 1
    assert data["size"] <= 10

@pytest.mark.asyncio
async def test_basic_search_no_results(async_client: AsyncClient, admin_token: str):
    response = await async_client.get(
        f"{BASE_URL}?username=nonexistent_user&email=nonexistent@example.com",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []

@pytest.mark.asyncio
async def test_basic_search_validation_error(async_client: AsyncClient, admin_token: str):
    response = await async_client.get(
        f"{BASE_URL}?skip=-1&limit=200",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_advanced_search_success(async_client: AsyncClient, admin_token: str):
    search_criteria = {
        "username": "john_doe",
        "email": "john.doe@example.com",
        "role": "ADMIN",
        "is_locked": False,
        "created_from": "2024-01-01T00:00:00",
        "created_to": "2024-12-31T23:59:59",
        "skip": 0,
        "limit": 10
    }
    response = await async_client.post(
        ADVANCED_SEARCH_URL,
        json=search_criteria,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 0
    assert data["page"] == 1
    assert data["size"] <= 10

@pytest.mark.asyncio
async def test_advanced_search_no_results(async_client: AsyncClient, admin_token: str):
    search_criteria = {
        "username": "nonexistent_user",
        "email": "nonexistent@example.com",
        "role": "ADMIN",
        "is_locked": False,
        "skip": 0,
        "limit": 10
    }
    response = await async_client.post(
        ADVANCED_SEARCH_URL,
        json=search_criteria,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []

@pytest.mark.asyncio
async def test_advanced_search_invalid_criteria(async_client: AsyncClient, admin_token: str):
    search_criteria = {
        "username": "john_doe",
        "email": "invalid_email",
        "skip": -10,
        "limit": 0
    }
    response = await async_client.post(
        ADVANCED_SEARCH_URL,
        json=search_criteria,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_advanced_search_with_filters(async_client: AsyncClient, admin_token: str):
    search_criteria = {
        "username": "john_doe",
        "email": "john.doe@example.com",
        "role": "ADMIN",
        "is_locked": False,
        "created_from": "2024-01-01T00:00:00",
        "created_to": "2024-12-31T23:59:59",
        "skip": 0,
        "limit": 10
    }
    response = await async_client.post(
        ADVANCED_SEARCH_URL,
        json=search_criteria,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    # Check the overall response structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "links" in data
    assert "filters" in data

    # Validate filters are returned as part of the response
    assert data["filters"] == search_criteria

    # Validate pagination links structure
    assert len(data["links"]) > 0
    assert all("rel" in link and "href" in link for link in data["links"])


@pytest.mark.asyncio
async def test_advanced_search_pagination_links(async_client: AsyncClient, admin_token: str):
    search_criteria = {
        "username": "john_doe",
        "email": "john.doe@example.com",
        "role": "ADMIN",
        "is_locked": False,
        "skip": 0,
        "limit": 10
    }
    response = await async_client.post(
        ADVANCED_SEARCH_URL,
        json=search_criteria,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    # Validate that pagination links include the correct `skip` and `limit` values
    links = data["links"]
    next_link = next((link for link in links if link["rel"] == "next"), None)
    first_link = next((link for link in links if link["rel"] == "first"), None)

    if next_link:
        assert f"skip={search_criteria['skip'] + search_criteria['limit']}" in next_link["href"]
        assert f"limit={search_criteria['limit']}" in next_link["href"]

    if first_link:
        assert "skip=0" in first_link["href"]
        assert f"limit={search_criteria['limit']}" in first_link["href"]


@pytest.mark.asyncio
async def test_advanced_search_empty_filters(async_client: AsyncClient, admin_token: str):
    search_criteria = {
        "skip": 0,
        "limit": 10
    }
    response = await async_client.post(
        ADVANCED_SEARCH_URL,
        json=search_criteria,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    # Ensure the response does not fail when filters are minimal
    assert "items" in data
    assert "filters" in data

    # Validate that the response filters include at least the provided criteria
    for key, value in search_criteria.items():
        assert data["filters"][key] == value


@pytest.mark.asyncio
async def test_advanced_search_invalid_filters(async_client: AsyncClient, admin_token: str):
    search_criteria = {
        "username": "john_doe",
        "email": "invalid-email-format",
        "created_from": "invalid-date",
        "created_to": "2024-12-31T23:59:59",
        "skip": -5,
        "limit": 0
    }
    response = await async_client.post(
        ADVANCED_SEARCH_URL,
        json=search_criteria,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
    data = response.json()

    # Validate that the validation error is returned
    assert "detail" in data
    assert any(error["loc"] == ["body", "created_from"] for error in data["detail"])
    assert any(error["loc"] == ["body", "email"] for error in data["detail"])


@pytest.mark.asyncio
async def test_advanced_search_no_results_with_filters(async_client: AsyncClient, admin_token: str):
    search_criteria = {
        "username": "nonexistent_user",
        "email": "nonexistent@example.com",
        "role": "ADMIN",
        "is_locked": True,
        "skip": 0,
        "limit": 10
    }
    response = await async_client.post(
        ADVANCED_SEARCH_URL,
        json=search_criteria,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    # Ensure no results are returned for unmatched filters
    assert data["total"] == 0
    assert data["items"] == []

    # Validate that the response filters include at least the provided criteria
    for key, value in search_criteria.items():
        assert data["filters"][key] == value

@pytest.mark.asyncio
async def test_advanced_search_users(async_client: AsyncClient, admin_token: str):
    filters = {
        "username": "john_doe",
        "email": "john.doe@example.com",
        "role": "ADMIN",
        "is_locked": False,
        "created_from": "2024-01-01T00:00:00",
        "created_to": "2024-12-31T23:59:59",
        "skip": 0,
        "limit": 10
    }
    response = await async_client.post(
        ADVANCED_SEARCH_URL,
        json=filters,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["filters"]["username"] == filters["username"]

@pytest.mark.asyncio
async def test_advanced_search_invalid_filters(async_client: AsyncClient, admin_token: str):
    filters = {
        "email": "invalid-email-format",
        "created_from": "invalid-date",
        "created_to": "2024-12-31T23:59:59",
        "skip": -5,
        "limit": 0
    }
    response = await async_client.post(
        ADVANCED_SEARCH_URL,
        json=filters,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any(error["loc"] == ["body", "email"] for error in data["detail"])
