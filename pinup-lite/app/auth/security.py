# [ADAPTER] เรื่อง crypto/token ทั้งหมด: bcrypt, JWT, Google ID token
# รวมไว้ที่เดียว → service อ่านเป็นภาษาธุรกิจ ไม่ต้องรู้จัก jose/passlib/google
import os
from datetime import datetime, timedelta, timezone

from google.auth.transport import requests
from google.oauth2 import id_token
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.errors import AppError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY: str = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(minutes=30)
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)) -> str:
    return jwt.encode({**data, "exp": datetime.now(timezone.utc) + expires_delta}, SECRET_KEY, algorithm=ALGORITHM)


def read_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise AppError("Token has expired")
    except JWTError:
        raise AppError("Invalid token")


def verify_google_token(credential: str) -> dict:
    try:
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID != "your-google-client-id":
            return id_token.verify_oauth2_token(credential, requests.Request(), GOOGLE_CLIENT_ID)
        return id_token.verify_oauth2_token(credential, requests.Request())
    except ValueError as e:
        raise AppError(f"Invalid Google token: {e}", status=401)
