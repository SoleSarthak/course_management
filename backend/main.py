from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import create_table

from backend.routers import (
    auth,
    courses,
    enrollments,
    modules,
    lessons,
    progress,
    certificates,)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    yield

app = FastAPI(
    title="Course Management API",
    lifespan=lifespan,
)

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR.parent / "static"),
    name="static",)

@app.get("/")
def home():
    return FileResponse(BASE_DIR.parent / "static" / "index.html")

app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(enrollments.router)
app.include_router(modules.router)
app.include_router(lessons.router)
app.include_router(progress.router)
app.include_router(certificates.router)

