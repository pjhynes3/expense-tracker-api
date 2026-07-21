from typing import Optional
from pwdlib import PasswordHash
import os
from datetime import datetime, timedelta, timezone
import jwt

password_hash = PasswordHash.recommended()
SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(
        plain_password: str,
        hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )

def create_access_token(subject: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub":subject,
        "exp":expiration,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def decode_access_token(token: str) -> Optional[str]:
    try:
        payload  = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        
        subject = payload.get("sub")

        if subject is None:
            return None
        return subject
    except jwt.InvalidTokenError:
        return None