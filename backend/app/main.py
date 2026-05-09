from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.endpoints import employees, attendance, doors, departments, admin
from app.services.vector_db import VectorDBService
from app.services.storage import StorageService
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    StorageService()._ensure_bucket_exists()
    VectorDBService().init_collection(collection_name=settings.COLLECTION_NAME, vector_size=512)
    yield

app = FastAPI(title="FaceAccess AI System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(doors.router)
app.include_router(departments.router)
app.include_router(admin.router)  # <--- BẮT BUỘC THÊM DÒNG NÀY

@app.get("/health")
def health():
    return {"status": "healthy"}