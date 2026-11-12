# [HTTP] /api/auth — get_current_user อยู่ที่นี่เพราะผูกกับ OAuth2 header (เรื่อง HTTP)
# feature อื่นที่ต้อง login: from app.auth.router import get_current_user
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo.database import Database

from app.auth import schemas, service
from app.auth.repo import UserRepo
from app.db import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth")


def get_repo(db: Database = Depends(get_db)) -> UserRepo:
    return UserRepo(db)


def get_current_user(token: str = Depends(oauth2_scheme), users: UserRepo = Depends(get_repo)) -> dict:
    return service.current_user(users, token)


Users = Depends(get_repo)
CurrentUser = Depends(get_current_user)


@router.post("/register")
async def register(body: schemas.UserCreate, users: UserRepo = Users):
    return await service.register_user(users, body)


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), users: UserRepo = Users):
    return service.login(users, form.username, form.password)


@router.post("/google-login", response_model=schemas.Token)
def google_login(body: schemas.UserGoogleAuth, users: UserRepo = Users):
    return service.google_login(users, body)


@router.post("/forgot-password")
async def forgot_password(body: schemas.ForgotPasswordRequest, users: UserRepo = Users):
    return await service.forgot_password(users, body)


@router.post("/reset-password")
def reset_password(body: schemas.ResetPasswordRequest, users: UserRepo = Users):
    return service.reset_password(users, body)


@router.post("/verify-email")
def verify_email(body: schemas.VerifyEmailRequest, users: UserRepo = Users):
    return service.verify_email(users, body)


@router.post("/resend-verification")
async def resend_verification(body: schemas.ResendVerificationRequest, users: UserRepo = Users):
    return await service.resend_verification(users, body)


@router.get("/me", response_model=schemas.User)
def read_users_me(user: dict = CurrentUser):
    return user


@router.put("/profile", response_model=schemas.User)
def update_profile(body: schemas.UserUpdate, user: dict = CurrentUser, users: UserRepo = Users):
    return service.update_profile(users, user, body)


@router.post("/change-password")
def change_password(body: schemas.ChangePasswordRequest, user: dict = CurrentUser, users: UserRepo = Users):
    return service.change_password(users, user, body)
