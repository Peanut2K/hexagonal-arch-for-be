from typing import Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    province: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserGoogleAuth(BaseModel):
    credential: str  # The Google ID token received from frontend


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    province: Optional[str] = None


class User(UserBase):
    id: str
    is_active: bool
    is_verified: bool = False
    google_id: Optional[str] = None
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True
