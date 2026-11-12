# entry point: สร้าง app, ผูก router, แปลง AppError → HTTP
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import AppError
from app.projects.router import router as projects_router

app = FastAPI()
app.include_router(projects_router, prefix="/api")


@app.exception_handler(AppError)
def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    # key "detail" เหมือน HTTPException เดิม → frontend ไม่ต้องแก้
    return JSONResponse(status_code=exc.status, content={"detail": str(exc)})
