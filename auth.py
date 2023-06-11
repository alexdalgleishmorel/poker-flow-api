import jwt

def generate_jwt(data):
    return jwt.encode(
        {
            "data": data,
            "token": "mock_jwt_token_from_api"
        }, 
        "secret", 
        algorithm="HS256"
    )
