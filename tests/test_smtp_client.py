import pytest
from unittest.mock import patch, MagicMock, ANY
from app.utils.smtp_connection import SMTPClient

# Sample test data
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USERNAME = "test@example.com"
SMTP_PASSWORD = "password"
RECIPIENT_EMAIL = "recipient@example.com"
SUBJECT = "Test Subject"
HTML_CONTENT = "<html><body><h1>Test Email</h1></body></html>"

#@pytest.fixture
#def smtp_client():
#    """Fixture to create an SMTPClient instance."""
#    return SMTPClient(SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD)
#
#
#@patch("app.utils.smtp_connection.smtplib.SMTP")
#def test_send_email_success(mock_smtp, smtp_client):
#    """Test email is sent successfully."""
#    # Mock SMTP server behavior
#    mock_server = MagicMock()
#    mock_smtp.return_value = mock_server
#
#    smtp_client.send_email(SUBJECT, HTML_CONTENT, RECIPIENT_EMAIL)
#
#    # Assertions to verify email sending behavior
#    mock_smtp.assert_called_once_with(SMTP_SERVER, SMTP_PORT)
#    mock_server.starttls.assert_called_once()
#    mock_server.login.assert_called_once_with(SMTP_USERNAME, SMTP_PASSWORD)
#    mock_server.sendmail.assert_called_once_with(SMTP_USERNAME, RECIPIENT_EMAIL, ANY)
#
#
#@patch("app.utils.smtp_connection.smtplib.SMTP")
#def test_send_email_failure_login(mock_smtp, smtp_client):
#    """Test failure during SMTP login."""
#    # Simulate login failure
#    mock_server = MagicMock()
#    mock_server.login.side_effect = Exception("Login failed")
#    mock_smtp.return_value = mock_server
#
#    with pytest.raises(Exception, match="Login failed"):
#        smtp_client.send_email(SUBJECT, HTML_CONTENT, RECIPIENT_EMAIL)
#
#    mock_smtp.assert_called_once_with(SMTP_SERVER, SMTP_PORT)
#    mock_server.starttls.assert_called_once()
#    mock_server.login.assert_called_once_with(SMTP_USERNAME, SMTP_PASSWORD)
#    mock_server.sendmail.assert_not_called()
#
#
#@patch("app.utils.smtp_connection.smtplib.SMTP")
#def test_send_email_failure_send(mock_smtp, smtp_client):
#    """Test failure during sending email."""
#    # Simulate email sending failure
#    mock_server = MagicMock()
#    mock_server.sendmail.side_effect = Exception("Failed to send email")
#    mock_smtp.return_value = mock_server
#
#    with pytest.raises(Exception, match="Failed to send email"):
#        smtp_client.send_email(SUBJECT, HTML_CONTENT, RECIPIENT_EMAIL)
#
#    mock_smtp.assert_called_once_with(SMTP_SERVER, SMTP_PORT)
#    mock_server.starttls.assert_called_once()
#    mock_server.login.assert_called_once_with(SMTP_USERNAME, SMTP_PASSWORD)
#    mock_server.sendmail.assert_called_once()
