from builtins import bool, str
from email_validator import validate_email, EmailNotValidError

def validate_email_address(email: str) -> bool:
    """
    Validate the email address using the email-validator library.
    
    Args:
        email (str): Email address to validate.
    
    Returns:
        bool: True if the email is valid, otherwise False.
    """
    if not email:  # Handle None or empty strings
        return False

    try:
        # Validate only the format, not deliverability
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError as e:
        print(f"Invalid email: {e}")
        return False
        