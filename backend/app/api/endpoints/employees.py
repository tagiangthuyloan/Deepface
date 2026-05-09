from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import List
import shutil, uuid, os
from app.services.database import DBService
from app.services.storage import StorageService
from app.services.vision import VisionService
from app.worker import celery_app
from app.schemas.schemas import EmployeeOut, PermissionUpdate

router = APIRouter(prefix="/employees", tags=["Employees"])
db_service = DBService()
storage_service = StorageService()
vision_service = VisionService()

@router.post("/register", response_model=EmployeeOut)
async def register(
    full_name: str = Form(...), 
    employee_code: str = Form(...), 
    department_name: str = Form(...), 
    files: List[UploadFile] = File(...)
):
    if not (1 <= len(files) <= 5):
        raise HTTPException(status_code=400, detail="Vui lòng gửi từ 1 đến 5 ảnh.")

    new_user = db_service.create_employee(full_name, employee_code, department_name)
    user_id = new_user.id
    
    object_names = []
    for file in files:
        temp_path = f"/tmp/{uuid.uuid4()}.jpg"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        is_ok, msg = vision_service.check_image_quality(temp_path)
        if not is_ok:
            os.remove(temp_path)
            db_service.delete_employee(user_id) 
            raise HTTPException(status_code=400, detail=f"Ảnh lỗi: {msg}")
        
        obj_name = f"avatars/{user_id}/{uuid.uuid4()}.jpg"
        with open(temp_path, "rb") as f:
            storage_service.upload_file(f, obj_name)
        object_names.append(obj_name)
        if os.path.exists(temp_path): os.remove(temp_path)    
        
    celery_app.send_task("process_face_registration", args=[user_id, object_names])
    return new_user

@router.get("/", response_model=List[EmployeeOut])
async def list_employees():
    return db_service.get_all_employees()

@router.patch("/{id}/status")
async def update_status(id: int, is_active: bool):
    return db_service.update_employee_status(id, is_active)

@router.put("/{id}/permissions")
async def update_permissions(id: int, perm: PermissionUpdate):
    return db_service.set_permission(id, perm.door_id, perm.allowed_start_time, perm.allowed_end_time)

@router.delete("/{id}")
async def delete_employee(id: int):
    success = db_service.delete_employee(id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên để xóa")
    
    from app.services.vector_db import VectorDBService
    from app.core.config import settings
    VectorDBService().delete_vector(settings.COLLECTION_NAME, id)
    
    return {"status": "success", "message": f"Đã xóa nhân viên ID {id} khỏi hệ thống"}

@router.get("/search", response_model=List[EmployeeOut])
async def search_employees(query: str):
    return db_service.search_employees(query)