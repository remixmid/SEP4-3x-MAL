import time
from datetime import datetime, timedelta, timezone
from typing import Dict
from decouple import config
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.database.db import get_db
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

JWT_SECRET = config("secret")
JWT_ALGORITHM = config("algorithm")

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def token_response(token: str):
    return {
        "access_token": token
    }

#Signing the JWT string:
def signJWT(user_email: str) -> Dict[str, str]:
    expire = datetime.now(timezone.utc) + timedelta(hours=1)

    payload = {
        "sub": user_email,
        "expires": int(expire.timestamp())
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
    

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    user = payload.get("sub")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user