import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from app.dependencies import (
    get_settings,
    get_email_service,
    get_db,
    get_current_user,
    require_role,
)
from app.utils.template_manager import TemplateManager
from app.services.email_service import EmailService
from sqlalchemy.ext.asyncio import AsyncSession


# Test get_settings
def test_get_settings():
    settings = get_settings()
    assert settings is not None
    assert hasattr(settings, "database_url")  # Replace "database_url" with an actual valid attribute in your Settings class
    assert isinstance(settings.database_url, str)  # Optional validation

# Test get_email_service
def test_get_email_service():
    email_service = get_email_service()
    assert isinstance(email_service, EmailService)
    assert isinstance(email_service.template_manager, TemplateManager)

# Test get_current_user - invalid token
@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mocker):
    mock_token = "invalid_token"
    mocker.patch("app.services.jwt_service.decode_token", return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(mock_token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_require_role_valid(mocker):
    mock_user = {"user_id": "user_id", "role": "ADMIN"}
    mocker.patch("app.dependencies.get_current_user", return_value=mock_user)

    role_checker = require_role(["ADMIN", "MANAGER"])
    result = role_checker(current_user=mock_user)  # Pass the mocked user explicitly
    assert result == mock_user


@pytest.mark.asyncio
async def test_require_role_invalid(mocker):
    mock_user = {"user_id": "user_id", "role": "USER"}
    mocker.patch("app.dependencies.get_current_user", return_value=mock_user)

    role_checker = require_role(["ADMIN", "MANAGER"])
    with pytest.raises(HTTPException) as exc_info:
        role_checker(current_user=mock_user)  # Pass the mocked user explicitly

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Operation not permitted"