import time
from datetime import datetime, timedelta
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
    schemes=["bcrypt"],
    deprecated="auto"
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def token_response(token: str):
    return {
        "access_token": token
    }

#Signing the JWT string:
def signJWT(user_email: str) -> Dict[str, str]:
    payload = {
        "user_id": user_email,
        "expires": datetime.utcnow() + timedelta(minutes=30)
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
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user_id

    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")