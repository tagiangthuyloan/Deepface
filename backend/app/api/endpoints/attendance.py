from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import shutil, uuid, os, io, time
from datetime import date
import pandas as pd

from app.services.vision import VisionService
from app.services.vector_db import VectorDBService
from app.services.database import DBService
from app.services.storage import StorageService
from app.core.config import settings
from app.schemas.schemas import AttendanceLogOut
from typing import List, Optional

router = APIRouter(prefix="/attendance", tags=["Attendance"])
vision_service = VisionService()
vector_db = VectorDBService()
db_service = DBService()
storage_service = StorageService()

cooldown_cache = {}
COOLDOWN_SECONDS = 60

@router.post("/identify")
async def identify(door_name: str, file: UploadFile = File(...)):
    temp_id = str(uuid.uuid4())
    temp_path = f"/tmp/{temp_id}.jpg"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        embedding = vision_service.get_embedding(temp_path, detector='opencv') 
        
        if not embedding:
            return {"match": False, "message": "Không tìm thấy khuôn mặt", "open_door": False}

        results = vector_db.search(embedding, collection_name=settings.COLLECTION_NAME)
        
        if not results or results[0].score < 0.45:
            db_service.log_attendance(None, door_name, "DENIED", "Người lạ")
            return {"match": False, "message": "Người lạ", "open_door": False, "score": results[0].score if results else 0}

        emp_id = int(results[0].id)
        
        cache_key = f"{emp_id}_{door_name}"
        current_time = time.time()
        if cache_key in cooldown_cache:
            if current_time - cooldown_cache[cache_key] < COOLDOWN_SECONDS:
                user_info = db_service.get_employee_by_id(emp_id)
                return {
                    "match": True, 
                    "employee_name": user_info["full_name"], 
                    "employee_code": user_info["employee_code"],
                    "open_door": True, 
                    "message": "Đã ghi nhận (Cooldown)"
                }

        user_info = db_service.get_employee_by_id(emp_id)
        if not user_info or not user_info["is_active"]:
            db_service.log_attendance(emp_id, door_name, "DENIED", "Tài khoản bị khóa")
            return {"match": False, "message": "Tài khoản bị khóa", "open_door": False}

        is_allowed, msg = db_service.check_access_permission(emp_id, door_name)
        
        snapshot_name = f"snapshots/{date.today()}/{temp_id}.jpg"
        with open(temp_path, "rb") as f:
            storage_service.upload_file(f, snapshot_name)

        db_service.log_attendance(emp_id, door_name, "SUCCESS" if is_allowed else "DENIED", msg, snapshot_name)
        cooldown_cache[cache_key] = current_time

        return {
            "match": True,
            "employee_name": user_info["full_name"],
            "employee_code": user_info["employee_code"],
            "open_door": is_allowed,
            "message": msg
        }
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@router.get("/history", response_model=List[AttendanceLogOut])
async def get_history(limit: int = 100, employee_id: Optional[int] = None):
    return db_service.get_attendance_history(limit, employee_id)

@router.get("/stats/monthly")
async def get_monthly_stats(month: int, year: int):
    data = db_service.get_monthly_report_data(month, year)
    return {
        "month": month,
        "year": year,
        "total_records": len(data),
        "data": data
    }

@router.get("/export/excel")
async def export_attendance_excel(month: int, year: int):
    try:
        raw_data = db_service.get_monthly_report_data(month, year)
        if not raw_data:
            raise HTTPException(status_code=404, detail="Không có dữ liệu trong tháng này")

        df = pd.DataFrame(raw_data)
        df.columns = ['ID Nhân viên', 'Họ Tên', 'Mã NV', 'Ngày', 'Giờ Vào', 'Giờ Ra cuối']
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Attendance')
        
        output.seek(0)

        headers = {
            'Content-Disposition': f'attachment; filename="Attendance_Report_{month}_{year}.xlsx"'
        }
        return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xuất file: {str(e)}")