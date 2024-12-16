import pytest
from unittest.mock import AsyncMock, Mock
from app.services.email_service import EmailService
from app.utils.template_manager import TemplateManager
from app.utils.smtp_connection import SMTPClient
from app.models.user_model import User

@pytest.mark.asyncio
async def test_send_user_email_valid_type():
    # Mock dependencies
    template_manager_mock = Mock(spec=TemplateManager)
    smtp_client_mock = Mock(spec=SMTPClient)
    email_service = EmailService(template_manager=template_manager_mock)
    email_service.smtp_client = smtp_client_mock

    # Configure mocks
    template_manager_mock.render_template.return_value = "<html>Email Content</html>"
    smtp_client_mock.send_email.return_value = None

    # Test data
    user_data = {"email": "user@example.com", "name": "Test User"}
    email_type = "email_verification"

    # Call the method
    await email_service.send_user_email(user_data, email_type)

    # Assertions
    template_manager_mock.render_template.assert_called_once_with(email_type, **user_data)
    smtp_client_mock.send_email.assert_called_once_with(
        "Verify Your Account", "<html>Email Content</html>", "user@example.com"
    )


@pytest.mark.asyncio
async def test_send_user_email_invalid_type():
    # Mock dependencies
    template_manager_mock = Mock(spec=TemplateManager)
    email_service = EmailService(template_manager=template_manager_mock)

    # Test data
    user_data = {"email": "user@example.com", "name": "Test User"}
    invalid_email_type = "invalid_type"

    # Expect ValueError
    with pytest.raises(ValueError) as exc_info:
        await email_service.send_user_email(user_data, invalid_email_type)

    assert str(exc_info.value) == "Invalid email type"
