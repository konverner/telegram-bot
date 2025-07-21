import os
from datetime import datetime

# Helper functions
def is_valid_phone_number(phone_number):
    """ Check if the phone number is valid in international format """
    if phone_number.startswith("+") and len(phone_number) > 10:
        return True
    return False


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%d-%m-%Y")
        return True
    except ValueError:
        return False


def create_keyfile_dict() -> dict[str, str]:
    """Create a dictionary with keys for the Google API from environment variables
    Returns:
        Dictionary with keys for the Google API
    Raises:
        ValueError: If any of the environment variables is not set
    """
    variables_keys = {
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
    }
    for key, _ in variables_keys.items():
        if variables_keys[key] is None:
            raise ValueError(f"Environment variable {key} is not set")
    return variables_keys
