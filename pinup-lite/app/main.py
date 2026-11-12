from dotenv import load_dotenv

load_dotenv()  # ต้องมาก่อน import app.* เพราะ config.py อ่าน env ตอน import

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from app.admin.router import router as admin  # noqa: E402
from app.ai_chat.router import router as ai_chat  # noqa: E402
from app.auth.router import router as auth  # noqa: E402
from app.bdi.router import router as bdi  # noqa: E402
from app.errors import AppError, Unauthorized  # noqa: E402
from app.places.router import router as places  # noqa: E402
from app.projects.router import router as projects  # noqa: E402
from app.search.router import router as search  # noqa: E402
from app.sites.router import router as sites  # noqa: E402
from app.transit.router import router as transit  # noqa: E402

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (admin, auth, bdi, projects, sites, places, ai_chat, transit):
    app.include_router(r, prefix="/api")
app.include_router(search, prefix="/api/search")


@app.exception_handler(AppError)
def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    # key "detail" เหมือน HTTPException เดิม → frontend ไม่ต้องแก้
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, Unauthorized) else None
    return JSONResponse(status_code=exc.status, content={"detail": str(exc)}, headers=headers)


@app.get("/")
def root():
    return {"message": "Welcome to Bangkok Zoning API"}
