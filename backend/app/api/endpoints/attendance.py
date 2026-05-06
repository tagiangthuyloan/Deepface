from fastapi import APIRouter, File, UploadFile
import shutil, uuid, os
from app.services.vision import VisionService
from app.services.vector_db import VectorDBService
from app.services.database import DBService
from app.core.config import settings
from app.schemas.schemas import AttendanceLogOut
from typing import List

router = APIRouter(prefix="/attendance", tags=["Attendance"])
vision_service = VisionService()
vector_db = VectorDBService()
db_service = DBService()

@router.post("/identify")
async def identify(door_name: str, file: UploadFile = File(...)):
    temp_path = f"/tmp/{uuid.uuid4()}.jpg"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        embedding = vision_service.get_embedding(temp_path)
        results = vector_db.search(embedding, collection_name=settings.COLLECTION_NAME)
        if not results or results[0].score < 0.5:
            db_service.log_attendance(None, door_name, "DENIED", "Không nhận diện được")
            return {"match": False, "message": "Người lạ", "open_door": False, 'score':results[0].score}

        emp_id = int(results[0].id)
        user_info = db_service.get_employee_by_id(emp_id)

        # Kiểm tra Active (UC 3)
        if not user_info or not user_info["is_active"]:
            db_service.log_attendance(emp_id, door_name, "DENIED", "Tài khoản bị khóa")
            return {"match": False, "message": "Tài khoản bị khóa", "open_door": False}

        # Kiểm tra Quyền & Giờ (UC 2)
        is_allowed, msg = db_service.check_access_permission(emp_id, door_name)
        
        db_service.log_attendance(emp_id, door_name, "SUCCESS" if is_allowed else "DENIED", msg)

        return {
            "match": True,
            "employee_name": user_info["full_name"],
            "open_door": is_allowed,
            "message": msg
        }
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@router.get("/history", response_model=List[AttendanceLogOut])
async def get_history(limit: int = 100):
    return db_service.get_attendance_history(limit)