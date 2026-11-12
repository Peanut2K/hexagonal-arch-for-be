# [CORE] สมัคร / login / ยืนยันอีเมล / รีเซ็ตรหัส
# ห้าม import: fastapi, pymongo, bson. crypto อยู่ใน security.py, ส่งเมลอยู่ใน email.py
from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from app.auth import schemas
from app.auth.email import send_forgot_password_email, send_verification_email
from app.auth.security import (
    ACCESS_TOKEN_EXPIRE,
    create_access_token,
    get_password_hash,
    read_token,
    verify_google_token,
    verify_password,
)
from app.errors import AppError, Forbidden, NotFound, Unauthorized

if TYPE_CHECKING:
    from app.auth.repo import UserRepo

RESEND_MESSAGE = "If that email exists, a verification link has been sent."


def _verification_token(email: str) -> str:
    return create_access_token({"sub": email, "type": "verification"}, timedelta(hours=24))


def _email_from(token: str, token_type: str) -> str:
    payload = read_token(token)
    if payload.get("sub") is None or payload.get("type") != token_type:
        raise AppError("Invalid token")
    return payload["sub"]


def _must_get(users: UserRepo, email: str) -> dict:
    user = users.find_by_email(email)
    if not user:
        raise NotFound("User not found")
    return user


# ---------- ส่งเมล → async ----------
# ponytail: pymongo ใน async def block event loop ชั่วครู่ (query เดียวต่อ request) — ย้ายไป motor ถ้าเป็นคอขวด

async def register_user(users: UserRepo, req: schemas.UserCreate) -> dict:
    if users.find_by_email(req.email):
        raise AppError("Email already registered")
    users.insert({
        "email": req.email,
        "hashed_password": get_password_hash(req.password),
        "full_name": req.full_name,
        "province": req.province,
        "is_active": True,
        "is_verified": False,
        "google_id": None,
        "profile_picture": None,
    })
    await send_verification_email(req.email, _verification_token(req.email))
    return {"message": "Registration successful. Please check your email to verify your account."}


async def forgot_password(users: UserRepo, req: schemas.ForgotPasswordRequest) -> dict:
    user = _must_get(users, req.email)
    token = create_access_token({"sub": user["email"], "type": "reset"}, timedelta(minutes=15))
    await send_forgot_password_email(req.email, token)
    return {"message": "Password reset email sent"}


async def resend_verification(users: UserRepo, req: schemas.ResendVerificationRequest) -> dict:
    user = users.find_by_email(req.email)
    if not user:
        return {"message": RESEND_MESSAGE}  # ไม่บอกว่ามี email นี้ไหม (กัน email enumeration)
    if user.get("is_verified", False):
        raise AppError("Email is already verified")
    await send_verification_email(req.email, _verification_token(user["email"]))
    return {"message": RESEND_MESSAGE}


# ---------- ไม่ส่งเมล → sync ----------

def login(users: UserRepo, email: str, password: str) -> dict:
    user = users.find_by_email(email)
    if not user or not verify_password(password, user.get("hashed_password")):
        raise Unauthorized("Incorrect username or password")
    if user.get("is_verified", True) is False:
        raise Forbidden("Email not verified")
    return {
        "access_token": create_access_token({"sub": user["email"]}, ACCESS_TOKEN_EXPIRE),
        "token_type": "bearer",
        "user": {"id": user["id"], "full_name": user["full_name"], "profile_picture": user.get("profile_picture")},
    }


def google_login(users: UserRepo, req: schemas.UserGoogleAuth) -> dict:
    info = verify_google_token(req.credential)
    email = info.get("email")
    if not email:
        raise AppError("Google token does not contain email")

    user = users.find_by_email(email)
    if not user:
        users.insert({
            "email": email,
            "full_name": info.get("name"),
            "google_id": info.get("sub"),
            "profile_picture": info.get("picture"),
            "is_active": True,
            "hashed_password": None,
            "province": None,
        })
    elif user.get("google_id") is None:
        users.update(email, {"google_id": info.get("sub"), "profile_picture": info.get("picture")})

    return {"access_token": create_access_token({"sub": email}, ACCESS_TOKEN_EXPIRE), "token_type": "bearer"}


def reset_password(users: UserRepo, req: schemas.ResetPasswordRequest) -> dict:
    email = _email_from(req.token, "reset")
    _must_get(users, email)
    users.update(email, {"hashed_password": get_password_hash(req.new_password)})
    return {"message": "Password updated successfully"}


def verify_email(users: UserRepo, req: schemas.VerifyEmailRequest) -> dict:
    email = _email_from(req.token, "verification")
    _must_get(users, email)
    users.update(email, {"is_verified": True})
    return {"message": "Email verified successfully"}


def update_profile(users: UserRepo, user: dict, req: schemas.UserUpdate) -> dict:
    fields = {k: v for k, v in req.model_dump(exclude_unset=True).items() if v is not None}
    if not fields:
        return user
    updated = users.update(user["email"], fields)
    if not updated:
        raise NotFound("User not found")
    return updated


def change_password(users: UserRepo, user: dict, req: schemas.ChangePasswordRequest) -> dict:
    if not verify_password(req.current_password, user.get("hashed_password")):
        raise AppError("Current password is incorrect")
    users.update(user["email"], {"hashed_password": get_password_hash(req.new_password)})
    return {"message": "Password updated successfully"}


def current_user(users: UserRepo, token: str) -> dict:
    """ใช้เป็น dependency ของทุก route ที่ต้อง login (ผ่าน auth/router.get_current_user)"""
    try:
        payload = read_token(token)
    except AppError:
        payload = {}
    email = payload.get("sub")
    user = users.find_by_email(email) if email and payload.get("type") not in ("reset", "verification") else None
    if user is None:
        raise Unauthorized("Could not validate credentials")
    return user
