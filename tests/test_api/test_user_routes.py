import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from httpx import AsyncClient
from urllib.parse import urlencode
from sqlalchemy.sql import text  # Import the text function
from fastapi import HTTPException
from datetime import timedelta
from faker import Faker
from app.models.user_model import User, UserRole
from app.services.user_service import UserService
from app.services.jwt_service import decode_token, create_access_token
from app.dependencies import get_settings
from app.schemas.user_schemas import UserResponse, UserListResponse
from app.schemas.pagination_schema import EnhancedPagination
from fastapi.testclient import TestClient
from app.dependencies import get_settings
from app.routers.user_routes import login
from faker import Faker

fake = Faker()  # Initialize Faker

settings = get_settings()

@pytest.mark.asyncio
async def test_update_user_invalid_data(async_client, admin_token, admin_user):
    """Test updating a user with invalid data."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    updated_data = {"email": "notanemail"}  # Invalid email
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_user_not_found(async_client, admin_token):
    """Test deleting a non-existent user."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    non_existent_user_id = uuid4()  # Random UUID
    response = await async_client.delete(f"/users/{non_existent_user_id}", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_list_users_no_users(async_client, admin_token, db_session):
    """Test listing users when no users exist."""
    # Use the `text` function to mark raw SQL explicitly
    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()  # Commit the transaction to apply changes
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get("items", [])) == 0

@pytest.mark.asyncio
async def test_register_duplicate_email(async_client, verified_user):
    """Test registering a user with a duplicate email."""
    user_data = {
        "email": verified_user.email,  # Use existing user's email
        "password": "ValidPassword123!",
        "nickname": "test_nick123",
        "role": "AUTHENTICATED"  # Add required role field
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 400  # The expected status code for duplicate email
    assert "Email already exists" in response.json().get("detail", "")



@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client):
    """Test login with invalid credentials."""
    form_data = {
        "username": "nonexistentuser@example.com",
        "password": "InvalidPassword123!"
    }
    response = await async_client.post(
        "/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_verify_email_invalid_token(async_client, verified_user):
    """Test verifying email with an invalid token."""
    invalid_token = "invalidtoken123"
    response = await async_client.get(f"/verify-email/{verified_user.id}/{invalid_token}")
    assert response.status_code == 400
    assert "Invalid or expired verification token" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_list_users_pagination(async_client, admin_token, users_with_same_role_50_users):
    """Test listing users with pagination."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response_page_1 = await async_client.get("/users/?skip=0&limit=10", headers=headers)
    response_page_2 = await async_client.get("/users/?skip=10&limit=10", headers=headers)
    assert response_page_1.status_code == 200
    assert response_page_2.status_code == 200
    assert len(response_page_1.json().get("items", [])) == 10
    assert len(response_page_2.json().get("items", [])) == 10


@pytest.mark.asyncio
async def test_create_user_invalid_nickname(async_client, admin_token):
    """Test creating a user with an invalid nickname."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_data = {
        "email": "newuser@example.com",
        "password": "ValidPassword123!",
        "nickname": "invalid nickname!"  # Invalid nickname
    }
    response = await async_client.post("/users/", json=user_data, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_verify_email_success(async_client, verified_user, admin_token, db_session):
    """Test verifying a user's email with a valid token."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    token = verified_user.verification_token
    if not token:  # Ensure a valid token is set
        verified_user.verification_token = "valid_token_example"
        await db_session.commit()  # Ensure changes are saved

    response = await async_client.get(f"/verify-email/{verified_user.id}/{verified_user.verification_token}", headers=headers)
    assert response.status_code == 200, response.json()
    assert response.json()["message"] == "Email verified successfully"


@pytest.mark.asyncio
async def test_update_user_invalid_email_format(async_client, admin_user, admin_token):
    """Test updating a user with an invalid email format."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    updated_data = {"email": "invalidemail"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 422, response.json()
    assert any(
        "The email address is not valid" in detail["msg"]
        for detail in response.json()["detail"]
    ), "Error message should indicate invalid email format"

@pytest.mark.asyncio
async def test_delete_user_non_existent(async_client, admin_token):
    """Test deleting a user that does not exist."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.delete("/users/00000000-0000-0000-0000-000000000000", headers=headers)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_user_existing_email(async_client, admin_token, verified_user):
    """Test creating a user with an existing email."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_data = {
        "email": verified_user.email,  # Use an existing user's email
        "password": "ValidPassword123!",
        "nickname": "new_unique_nickname",
        "role": "AUTHENTICATED"  # Add the required role field
    }
    response = await async_client.post("/users/", json=user_data, headers=headers)
    assert response.status_code == 400, response.json()
    assert "Email already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_internal_error(mocker, async_client, admin_token):
    """Test user creation when an internal error occurs."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_data = {
        "email": fake.email(),
        "password": "ValidPassword123!",
        "nickname": "valid_nickname",
        "role": "AUTHENTICATED"  # Add the required role field
    }

    # Mock UserService.create to simulate an internal error
    mocker.patch("app.services.user_service.UserService.create", return_value=None)

    response = await async_client.post("/users/", json=user_data, headers=headers)
    assert response.status_code == 500, response.json()
    assert "Failed to create user" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_invalid_input(async_client, admin_token):
    """Test creating a user with invalid input."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_data = {
        "email": "invalidemail",  # Invalid email format
        "password": "short",  # Weak password
        "nickname": "invalid nickname!"  # Invalid nickname format
    }
    response = await async_client.post("/users/", json=user_data, headers=headers)
    assert response.status_code == 422, response.json()
    assert "value is not a valid email address" in str(response.json()["detail"])

@pytest.mark.asyncio
async def test_login_account_locked(mocker):
    """Test login failure due to account being locked."""
    mock_session = AsyncMock()
    mocker.patch("app.services.user_service.UserService.is_account_locked", return_value=True)

    form_data = AsyncMock(username="locked_user", password="password")

    with pytest.raises(HTTPException) as exc_info:
        await login(form_data, session=mock_session)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Account locked due to too many failed login attempts."

@pytest.mark.asyncio
async def test_login_success(async_client, mocker, db_session, verified_user):
    """Test successful login."""
    form_data = {"username": verified_user.nickname, "password": "CorrectPassword123!"}
    
    # Mock UserService methods
    mocker.patch("app.services.user_service.UserService.is_account_locked", return_value=False)
    mocker.patch("app.services.user_service.UserService.login_user", return_value=verified_user)

    # Calculate expected token expiry
    settings = get_settings()  # Use get_settings to fetch settings
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expected_token = create_access_token(
        data={"sub": verified_user.email, "role": str(verified_user.role.name)},
        expires_delta=expires_delta
    )

    response = await async_client.post(
        "/login/",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["access_token"] == expected_token
    assert response_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_incorrect_credentials(mocker):
    """Test login failure due to incorrect credentials."""
    mock_session = AsyncMock()
    mocker.patch("app.services.user_service.UserService.is_account_locked", return_value=False)
    mocker.patch("app.services.user_service.UserService.login_user", return_value=None)

    form_data = AsyncMock(username="wrong_user", password="wrong_password")

    with pytest.raises(HTTPException) as exc_info:
        await login(form_data, session=mock_session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Incorrect email or password."

@pytest.mark.asyncio
async def test_login_unexpected_error(mocker):
    """Test login failure due to an unexpected error."""
    mock_session = AsyncMock()
    mocker.patch("app.services.user_service.UserService.is_account_locked", side_effect=Exception("Unexpected error"))

    form_data = AsyncMock(username="test@example.com", password="password")

    with pytest.raises(HTTPException) as exc_info:
        await login(form_data, session=mock_session)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "An unexpected error occurred."


@pytest.mark.asyncio
async def test_list_users_with_results(async_client, admin_token, users_with_same_role_50_users):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/?skip=0&limit=10", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 51
    assert len(response_data["items"]) == 10

@pytest.mark.asyncio
async def test_list_users_empty(async_client, admin_token, db_session):
    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/?skip=0&limit=10", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 0
    assert len(response_data["items"]) == 0

@pytest.mark.asyncio
async def test_list_users_without_permission(async_client, user_token):
    """Test listing users with insufficient permissions."""
    headers = {"Authorization": f"Bearer {user_token}"}  # Token for a regular user
    response = await async_client.get("/users/", headers=headers)
    assert response.status_code == 403  # Forbidden
    assert "detail" in response.json()
    assert response.json()["detail"] == "Operation not permitted"  # Match actual message


@pytest.mark.asyncio
async def test_list_users_partial_page(async_client, admin_token, users_with_same_role_50_users):
    """Test listing users when only a partial page of results is available."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/?skip=40&limit=20", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["items"]) == 11  # Corrected expectation
    assert response_data["total"] == 51  # Ensure total matches


@pytest.mark.asyncio
async def test_list_users_valid_pagination(async_client, admin_token, users_with_same_role_50_users):
    """Test listing users with valid pagination parameters."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Fetch the first page
    response_page_1 = await async_client.get("/users/?skip=0&limit=10", headers=headers)
    assert response_page_1.status_code == 200
    response_data_page_1 = response_page_1.json()
    assert len(response_data_page_1["items"]) == 10
    assert response_data_page_1["total"] == 51  # Corrected expected total

@pytest.mark.asyncio
async def test_list_users_empty_db(async_client, admin_token, db_session):
    """Test listing users when no users exist in the database."""
    # Clear users table
    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/?skip=0&limit=10", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 0
    assert len(response_data["items"]) == 0

from app.utils.security import hash_password  # Ensure you import your password hashing utility

@pytest.mark.asyncio
async def test_user_response_model_validation(async_client, admin_token, db_session):
    # Create sample users in the database
    user_data = [
        {
            "email": "user1@example.com",
            "nickname": "user1",
            "role": UserRole.AUTHENTICATED,
            "hashed_password": hash_password("Password123!"),
        },
        {
            "email": "user2@example.com",
            "nickname": "user2",
            "role": UserRole.MANAGER,
            "hashed_password": hash_password("Password123!"),
        },
    ]
    for user in user_data:
        db_user = User(**user)
        db_session.add(db_user)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/?skip=0&limit=10", headers=headers)

    # Validate response
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == len(user_data) + 1
    assert all("id" in user for user in data["items"])


@pytest.mark.asyncio
async def test_pagination_links(async_client, admin_token, db_session):
    # Insert dummy users into the database
    for i in range(25):  # Create 25 users
        db_session.add(
            User(
                email=f"user{i}@example.com",
                nickname=f"user{i}",
                hashed_password=hash_password("Password123!"),  # Use hashed_password
                role=UserRole.AUTHENTICATED,
            )
        )
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/?skip=10&limit=5", headers=headers)

    # Validate pagination links
    assert response.status_code == 200
    data = response.json()
    links = data["links"]
    assert len(links) > 0
    assert any(link["rel"] == "self" for link in links)
    assert any(link["rel"] == "next" for link in links)
    assert any(link["rel"] == "prev" for link in links)


@pytest.mark.asyncio
async def test_create_user_existing_email_check(async_client, admin_token, db_session):
    # Create an existing user
    existing_user = User(
        email="duplicate@example.com",
        nickname="duplicate",
        hashed_password=hash_password("Password123!"),  # Use hashed_password
        role=UserRole.AUTHENTICATED,
    )
    db_session.add(existing_user)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    user_data = {
        "email": "duplicate@example.com",
        "nickname": "new_nickname",
        "password": "Password123!",  # This will be hashed in the actual app logic
        "role": UserRole.AUTHENTICATED.name,
    }
    response = await async_client.post("/users/", json=user_data, headers=headers)

    # Verify the duplicate email error
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"

@pytest.mark.asyncio
async def test_generate_pagination_links_partial_page(async_client, admin_token, users_with_same_role_50_users):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/?skip=40&limit=20", headers=headers)

    assert response.status_code == 200
    data = response.json()
    links = data["links"]

    # Validate pagination links for the partial page
    assert len(links) > 0
    assert any(link["rel"] == "self" for link in links)
    assert any(link["rel"] == "prev" for link in links)
    assert not any(link["rel"] == "next" for link in links)  # No 'next' link for the last page

@pytest.mark.asyncio
async def test_pagination_links_zero_users(async_client, admin_token, db_session):
    # Ensure the database is empty
    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/?skip=0&limit=10", headers=headers)

    # Validate response
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0
    assert "links" in data
    assert len(data["links"]) == 3  # Should only have self, first, last

@pytest.mark.asyncio
async def test_advanced_search_pagination_links(async_client, admin_token, users_with_same_role_50_users):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.post(
        "/users-advanced-search",
        json={"skip": 10, "limit": 10, "role": UserRole.AUTHENTICATED.name},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    links = data["links"]

    # Validate the presence of pagination links
    assert len(links) > 0
    assert any(link["rel"] == "self" for link in links)
    assert any(link["rel"] == "next" for link in links)
    assert any(link["rel"] == "prev" for link in links)

@pytest.mark.asyncio
async def test_create_user_success(async_client, admin_token):
    """Test successful user creation."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_data = {
        "email": fake.email(),
        "password": "ValidPassword123!",
        "nickname": "valid_nickname",
        "role": "ANONYMOUS"  # Add the required role field
    }
    response = await async_client.post("/users/", json=user_data, headers=headers)
    assert response.status_code == 201, response.json()
    response_data = response.json()
    assert response_data["email"] == user_data["email"]
    assert response_data["nickname"] == user_data["nickname"]
    assert response_data["role"] == user_data["role"]
    