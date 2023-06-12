import jwt

def generate_jwt(profile_data):
    return jwt.encode(
        {
            "profile": profile_data,
            "token": "mock_jwt_token_from_api"
        }, 
        "secret", 
        algorithm="HS256"
    )
