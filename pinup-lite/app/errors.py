# [CORE] error ของ business — service raise ตัวนี้ แทน fastapi.HTTPException
# ไม่ import fastapi → service test ได้โดยไม่ต้องมี HTTP. handler อยู่ใน main.py


class AppError(Exception):
    status = 400

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status or self.status


class NotFound(AppError):
    status = 404


class Unauthorized(AppError):
    status = 401


class Forbidden(AppError):
    status = 403
