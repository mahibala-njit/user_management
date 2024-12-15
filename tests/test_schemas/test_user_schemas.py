import uuid
from uuid import uuid4
import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.user_schemas import UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse, LoginRequest, UserRole

# Fixtures for common test data
@pytest.fixture
def user_base_data():
    return {
        "nickname": "john_doe_123",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "AUTHENTICATED",
        "bio": "I am a software engineer with over 5 years of experience.",
        "profile_picture_url": "https://example.com/profile_pictures/john_doe.jpg",
        "linkedin_profile_url": "https://linkedin.com/in/johndoe",
        "github_profile_url": "https://github.com/johndoe"
    }

@pytest.fixture
def user_create_data(user_base_data):
    return {**user_base_data, "password": "SecurePassword123!"}

@pytest.fixture
def user_update_data():
    return {
        "email": "john.doe.new@example.com",
        "nickname": "j_doe",
        "first_name": "John",
        "last_name": "Doe",
        "bio": "I specialize in backend development with Python and Node.js.",
        "profile_picture_url": "https://example.com/profile_pictures/john_doe_updated.jpg"
    }

@pytest.fixture
def user_response_data(user_base_data):
    return {
        "id": uuid.uuid4(),
        "nickname": user_base_data["nickname"],
        "first_name": user_base_data["first_name"],
        "last_name": user_base_data["last_name"],
        "role": user_base_data["role"],
        "email": user_base_data["email"],
        # "last_login_at": datetime.now(),
        # "created_at": datetime.now(),
        # "updated_at": datetime.now(),
        "links": []
    }

@pytest.fixture
def login_request_data():
    return {"email": "john_doe_123@emai.com", "password": "SecurePassword123!"}

# Tests for UserBase
def test_user_base_valid(user_base_data):
    user = UserBase(**user_base_data)
    assert user.nickname == user_base_data["nickname"]
    assert user.email == user_base_data["email"]

# Tests for UserCreate
def test_user_create_valid(user_create_data):
    user = UserCreate(**user_create_data)
    assert user.nickname == user_create_data["nickname"]
    assert user.password == user_create_data["password"]

# Tests for UserUpdate
def test_user_update_valid(user_update_data):
    user_update = UserUpdate(**user_update_data)
    assert user_update.email == user_update_data["email"]
    assert user_update.first_name == user_update_data["first_name"]

# Tests for UserResponse
def test_user_response_valid():
    user_response_data = {
        "id": uuid4(),
        "email": "john.doe@example.com",
        "nickname": "john_doe",
        "first_name": "John",
        "last_name": "Doe",
        "bio": "Experienced developer",
        "profile_picture_url": "https://example.com/profile.jpg",
        "linkedin_profile_url": "https://linkedin.com/in/johndoe",
        "github_profile_url": "https://github.com/johndoe",
        "role": "ADMIN",
        "is_professional": False,
        "is_locked": False,
        "created_at": datetime.utcnow(),  # Added created_at field
        "links": [],  # Include an empty list or mock links
    }

    user = UserResponse(**user_response_data)
    assert user.id == user_response_data["id"]
    assert user.email == user_response_data["email"]
    assert user.created_at == user_response_data["created_at"]

# Tests for LoginRequest
def test_login_request_valid(login_request_data):
    login = LoginRequest(**login_request_data)
    assert login.email == login_request_data["email"]
    assert login.password == login_request_data["password"]

# Parametrized tests for nickname and email validation
@pytest.mark.parametrize("nickname", ["test_user", "test-user", "testuser123", "123test"])
def test_user_base_nickname_valid(nickname, user_base_data):
    user_base_data["nickname"] = nickname
    user = UserBase(**user_base_data)
    assert user.nickname == nickname

@pytest.mark.parametrize("nickname", ["test user", "test?user", "", "us"])
def test_user_base_nickname_invalid(nickname):
    with pytest.raises(ValidationError) as exc_info:
        UserBase(email="test@example.com", nickname=nickname)
    error_message = str(exc_info.value)
    assert (
        "Nickname must start with a letter" in error_message
        or "String should have at least 3 characters" in error_message
    )

# Parametrized tests for URL validation
@pytest.mark.parametrize("url", ["http://valid.com/profile.jpg", "https://valid.com/profile.png", None])
def test_user_base_url_valid(url, user_base_data):
    user_base_data["profile_picture_url"] = url
    user = UserBase(**user_base_data)
    assert user.profile_picture_url == url

@pytest.mark.parametrize("url", ["ftp://invalid.com/profile.jpg", "http//invalid", "https//invalid"])
def test_user_base_url_invalid(url, user_base_data):
    user_base_data["profile_picture_url"] = url
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)

# Tests for nickname

# Test valid nicknames for UserBase
@pytest.mark.parametrize("nickname", ["validName", "valid_name123", "valid-Name", "JohnDoe", "Alpha123"])
def test_user_base_nickname_valid(nickname):
    user = UserBase(email="test@example.com", nickname=nickname, role=UserRole.AUTHENTICATED)
    assert user.nickname == nickname

# Test valid nicknames for UserCreate
@pytest.mark.parametrize("nickname", ["validName", "valid_name123", "valid-Name"])
def test_user_create_nickname_valid(nickname):
    user = UserCreate(email="validuser@example.com", password="Secure1234!", nickname=nickname, role=UserRole.AUTHENTICATED)
    assert user.nickname == nickname

# Test invalid nicknames for UserCreate
@pytest.mark.parametrize("nickname", ["!invalidname", "invalid name", "ab", "toolongnickname12345678901234567890"])
def test_user_create_nickname_invalid(nickname):
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(email="validuser@example.com", password="Secure1234!", nickname=nickname, role=UserRole.AUTHENTICATED)
    assert "Nickname must start with a letter" in str(exc_info.value)

# Test valid nicknames for UserUpdate
@pytest.mark.parametrize("nickname", ["JohnDoe123", "nickname_1", "John-Doe", None])
def test_user_update_nickname_valid(nickname):
    if nickname is not None:
        user_update = UserUpdate(nickname=nickname, role=UserRole.AUTHENTICATED)
        assert user_update.nickname == nickname
    else:
        # If None, we shouldn't trigger validation
        with pytest.raises(ValidationError):
            UserUpdate(nickname=nickname)

# Test invalid nicknames for UserUpdate
@pytest.mark.parametrize("nickname", ["", "12invalid", "@badname", "toolongnickname12345678901234567890"])
def test_user_update_nickname_invalid(nickname):
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate(nickname=nickname, role=UserRole.AUTHENTICATED)
    error_message = str(exc_info.value)
    assert (
        "Nickname must start with a letter" in error_message
        or "At least one field must be provided for update" in error_message
        or "String should have at least 3 characters" in error_message
    )

# Test missing fields in UserUpdate (ensuring at least one field is provided)
def test_user_update_no_fields():
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate()
    assert "At least one field must be provided for update" in str(exc_info.value)
