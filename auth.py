import jwt

def generate_jwt(profile_data):
    """
    Generates a JSON Web Token (JWT) for user authentication.

    This function creates a JWT using the provided profile data. The JWT includes the user's profile information and a mock token. The token is encoded using the HS256 algorithm with a secret key.

    Parameters:
    profile_data (dict): A dictionary containing the user's profile information to be included in the JWT.

    Returns:
    str: A JWT string encoded with the user's profile data and a mock token.

    TODO
    In a production environment, the 'secret' used for encoding the JWT should be a secure, environment-specific key and not a hardcoded string. Additionally, the 'mock_jwt_token_from_api' is a placeholder and should be replaced with actual token data as needed.
    """
    return jwt.encode(
        {
            "profile": profile_data,
            "token": "mock_jwt_token_from_api"
        }, 
        "secret", 
        algorithm="HS256"
    )
