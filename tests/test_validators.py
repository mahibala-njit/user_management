import pytest
from app.utils.validators import validate_email_address

@pytest.mark.parametrize("email,expected", [
    ("valid.email@example.com", True),  # Valid email
    ("user.name+tag+sorting@example.com", True),  # Valid email with plus sign and tag
    ("plainaddress", False),  # Missing domain
    ("@missingusername.com", False),  # Missing username
    ("username@.com", False),  # Missing domain name
    ("username@domain", False),  # Missing TLD
    ("username@domain..com", False),  # Double dot in domain
    ("username@domain-.com", False),  # Invalid domain with trailing hyphen
    ("username@-domain.com", False),  # Invalid domain with leading hyphen
    ("", False),  # Empty string
    (" ", False),  # Space only
    (None, False),  # None input
])
def test_validate_email_address(email, expected):
    """Test the validate_email_address function with various inputs."""
    assert validate_email_address(email) == expected
