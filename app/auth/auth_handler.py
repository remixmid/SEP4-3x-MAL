import time
from typing import Dict

import jwt
from decouple import config

from app.model import UserLoginSchema

JWT_SECRET = config("secret")
JWT_ALGORITHM = config("algorithm")

def token_response(token: str):
    return {
        "access_token": token
    }

#Signing the JWT string:
def signJWT(user_id: str) -> Dict[str, str]:
    payload = {
        "user_id": user_id,
        "expires": time.time() + 900
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token_response(token)

#decoding
def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}
    
#check user exist
users = [];
def check_user(data: UserLoginSchema):
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
    return False