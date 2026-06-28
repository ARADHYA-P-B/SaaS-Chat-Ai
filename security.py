import os
import jwt
import bcrypt
from fastapi import HTTPException,status
from datetime import datetime,timedelta
from passlib.context import CryptContext

SCREAT_KEY = os.getenv("JWT_SCREAT","super_secret_saas_key_change_me_in_production")
ALGORITHM =  "HS256"
pwd_context = CryptContext(schemes=["bcrypt"],deprecated ="auto")

def hash_password(password: str) -> str:
    # Convert string password to bytes, generate salt, and hash it
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')  # Decode back to string for database storage

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Encode both to bytes and use bcrypt's secure evaluation utility
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SCREAT_KEY, algorithm=ALGORITHM)


def verify_access_token(token:str) ->dict:
    try:
        payload  = jwt.decode(token,SCREAT_KEY,algorithms=[ALGORITHM])
        user_id:int = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token payload"

            )
        return {"user_id": user_id,  "email" :payload.get("emial")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="your session has expire.  Please log in again "
        )
    except jwt.PyJWKError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not valid credentials"
        )
    