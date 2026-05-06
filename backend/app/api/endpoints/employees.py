from fastapi import APIRouter, File, UploadFile, HTTPException, Body
from typing import List
import shutil, uuid, os
from app.services.database import DBService
from app.services.storage import StorageService
from app.services.vision import VisionService
from app.worker import celery_app
from app.schemas.schemas import EmployeeOut, EmployeeCreate, PermissionUpdate

router = APIRouter(prefix="/employees", tags=["Employees"])
db_service = DBService()
storage_service = StorageService()
vision_service = VisionService()

@router.post("/register", response_model=EmployeeOut)
async def register(full_name: str, employee_code: str, department_id: int, files: List[UploadFile] = File(...)):
    # 1. Kiểm tra số lượng ảnh (UC 1: 3-5 ảnh)
    if not (1 <= len(files) <= 5):
        raise HTTPException(status_code=400, detail="Vui lòng gửi từ 1 đến 5 ảnh.")

    # 2. Tạo nhân viên trong DB
    new_user = db_service.create_employee(full_name, employee_code, department_id)
    user_id = new_user.id  # Sửa từ new_user["id"] thành new_user.id
    
    object_names = []
    for file in files:
        temp_path = f"/tmp/{uuid.uuid4()}.jpg"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 3. Kiểm tra chất lượng từng ảnh (UC 1)
        is_ok, msg = vision_service.check_image_quality(temp_path)
        if not is_ok:
            os.remove(temp_path)
            raise HTTPException(status_code=400, detail=f"Ảnh lỗi: {msg}")
        
        # 4. Upload lên MinIO
        obj_name = f"avatars/{user_id}/{uuid.uuid4()}.jpg"
        with open(temp_path, "rb") as f: # Dùng context manager cho an toàn
            storage_service.upload_file(f, obj_name)
        object_names.append(obj_name)
        if os.path.exists(temp_path): os.remove(temp_path)    
    # 5. Gửi task cho Celery xử lý Average Embedding
    celery_app.send_task("process_face_registration", args=[user_id, object_names])
    return new_user

@router.get("/", response_model=List[EmployeeOut])
async def list_employees():
    return db_service.get_all_employees() # Bạn cần thêm hàm này trong database.py

@router.patch("/{id}/status")
async def update_status(id: int, is_active: bool):
    return db_service.update_employee_status(id, is_active) # Thêm hàm trong database.py

@router.put("/{id}/permissions")
async def update_permissions(id: int, perm: PermissionUpdate):
    return db_service.set_permission(id, perm.door_id, perm.allowed_start_time, perm.allowed_end_time)
@router.delete("/{id}")
async def delete_employee(id: int):
    # 1. Xóa trong SQL
    success = db_service.delete_employee(id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên để xóa")
    
    # 2. Xóa trong Qdrant
    from app.services.vector_db import VectorDBService
    from app.core.config import settings
    VectorDBService().delete_vector(settings.COLLECTION_NAME, id)
    
    return {"status": "success", "message": f"Đã xóa nhân viên ID {id} khỏi hệ thống"}
@router.get("/search", response_model=List[EmployeeOut])
async def search_employees(query: str):
    """Tìm kiếm nhân viên theo tên hoặc mã để lấy ID"""
    return db_service.search_employees(query)