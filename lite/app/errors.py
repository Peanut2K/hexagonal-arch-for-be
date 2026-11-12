# [CORE] error ของ business — service raise ตัวนี้ แทน fastapi.HTTPException
# ไม่ import fastapi → service ที่ใช้ไฟล์นี้ test ได้โดยไม่ต้องมี HTTP
# handler ที่แปลงเป็น HTTP response อยู่ใน main.py


class AppError(Exception):
    status = 400


class NotFound(AppError):
    status = 404
