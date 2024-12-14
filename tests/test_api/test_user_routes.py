import pytest
from uuid import uuid4
from httpx import AsyncClient
from app.models.user_model import User
from app.services.jwt_service import decode_token
from urllib.parse import urlencode
from sqlalchemy.sql import text  # Import the text function
from faker import Faker

fake = Faker()

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