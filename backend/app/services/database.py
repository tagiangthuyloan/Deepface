from sqlalchemy.orm import Session, sessionmaker
from app.models.models import Base, Employee, AttendanceLog, AccessPermission, Door, DepartmentPermission, Department
import os
from sqlalchemy import create_engine, and_
from datetime import datetime, time

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:123@db:5432/attendance")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DBService:
    def __init__(self):
        Base.metadata.create_all(bind=engine)

    # --- NHÓM QUẢN LÝ NHÂN VIÊN ---

    def create_employee(self, full_name: str, employee_code: str, department_id: int):
        db = SessionLocal()
        try:
            # Chỉ tạo nhân viên, không cần copy quyền (quyền sẽ được kế thừa từ phòng ban khi check)
            new_emp = Employee(
                full_name=full_name, 
                employee_code=employee_code, 
                department_id=department_id
            )
            db.add(new_emp)
            db.commit()
            db.refresh(new_emp)
            return new_emp
        finally:
            db.close()

    def get_employee_by_id(self, employee_id: int):
        db = SessionLocal()
        try:
            emp = db.query(Employee).filter(Employee.id == employee_id).first()
            if emp:
                return {
                    "id": emp.id, 
                    "full_name": emp.full_name, 
                    "is_active": emp.is_active,
                    "employee_code": emp.employee_code,
                    "department_id": emp.department_id
                }
            return None
        finally:
            db.close()

    def get_all_employees(self):
        db = SessionLocal()
        try:
            return db.query(Employee).all()
        finally:
            db.close()

    def update_employee_status(self, employee_id: int, is_active: bool):
        db = SessionLocal()
        try:
            emp = db.query(Employee).filter(Employee.id == employee_id).first()
            if emp:
                emp.is_active = is_active
                db.commit()
                db.refresh(emp)
                return emp
            return None
        finally:
            db.close()

    def delete_employee(self, employee_id: int):
        db = SessionLocal()
        try:
            emp = db.query(Employee).filter(Employee.id == employee_id).first()
            if emp:
                # Xóa log và quyền cá nhân liên quan
                db.query(AttendanceLog).filter_by(employee_id=employee_id).delete()
                db.query(AccessPermission).filter_by(employee_id=employee_id).delete()
                db.delete(emp)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def search_employees(self, query: str):
        db = SessionLocal()
        try:
            return db.query(Employee).filter(
                (Employee.full_name.ilike(f"%{query}%")) | 
                (Employee.employee_code.ilike(f"%{query}%"))
            ).all()
        finally:
            db.close()

    # --- NHÓM PHÒNG BAN & THIẾT LẬP ---

    def create_department(self, name: str):
        db = SessionLocal()
        try:
            dept = Department(name=name)
            db.add(dept)
            db.commit()
            db.refresh(dept)
            return dept
        finally:
            db.close()

    def get_all_departments(self):
        db = SessionLocal()
        try:
            return db.query(Department).all()
        finally:
            db.close()

    def set_department_permission(self, dept_id: int, door_id: int, start_t: time, end_t: time):
        db = SessionLocal()
        try:
            perm = db.query(DepartmentPermission).filter_by(
                department_id=dept_id, door_id=door_id
            ).first()
            
            if not perm:
                perm = DepartmentPermission(department_id=dept_id, door_id=door_id)
                db.add(perm)
            
            perm.allowed_start_time = start_t
            perm.allowed_end_time = end_t
            db.commit()
            db.refresh(perm)
            return perm
        finally:
            db.close()

    # --- NHÓM CỬA & QUYỀN TRUY CẬP ---

    def create_door(self, name: str, description: str = None):
        db = SessionLocal()
        try:
            door = Door(name=name, description=description)
            db.add(door)
            db.commit()
            db.refresh(door)
            return door
        finally:
            db.close()

    def get_all_doors(self):
        db = SessionLocal()
        try:
            return db.query(Door).all()
        finally:
            db.close()

    def set_permission(self, employee_id: int, door_id: int, start: time, end: time):
        db = SessionLocal()
        try:
            perm = db.query(AccessPermission).filter_by(employee_id=employee_id, door_id=door_id).first()
            if not perm:
                perm = AccessPermission(employee_id=employee_id, door_id=door_id)
                db.add(perm)
            perm.allowed_start_time = start
            perm.allowed_end_time = end
            db.commit()
            return {"status": "success"}
        finally:
            db.close()

    def check_access_permission(self, employee_id: int, door_name: str):
        db = SessionLocal()
        try:
            emp = db.query(Employee).filter(Employee.id == employee_id).first()
            door = db.query(Door).filter(Door.name == door_name).first()
            
            if not emp: return False, "Nhân viên không tồn tại"
            if not door: return False, "Cửa không tồn tại"
            
            current_time = datetime.now().time()

            # 1. Kiểm tra quyền cá nhân trước (Đặc cách)
            perm = db.query(AccessPermission).filter_by(
                employee_id=employee_id, door_id=door.id
            ).first()
            
            # 2. Nếu không có quyền cá nhân, kiểm tra quyền phòng ban (Kế thừa)
            if not perm:
                perm = db.query(DepartmentPermission).filter_by(
                    department_id=emp.department_id, door_id=door.id
                ).first()

            if not perm:
                return False, "Không có quyền truy cập cửa này"

            # 3. Kiểm tra khung giờ
            if perm.allowed_start_time and perm.allowed_end_time:
                if not (perm.allowed_start_time <= current_time <= perm.allowed_end_time):
                    return False, f"Ngoài giờ (Cho phép: {perm.allowed_start_time}-{perm.allowed_end_time})"

            return True, "Hợp lệ"
        finally:
            db.close()

    # --- NHÓM ĐIỂM DANH & LOG ---

    def log_attendance(self, employee_id: int, door_name: str, status: str, reason: str = None, image_path: str = None):
        db = SessionLocal()
        try:
            door = db.query(Door).filter(Door.name == door_name).first()
            door_id = door.id if door else None

            new_log = AttendanceLog(
                employee_id=employee_id,
                door_id=door_id,
                status=status,
                reason=reason,
                image_snapshot=image_path
            )
            db.add(new_log)
            db.commit()
            return new_log
        finally:
            db.close()

    def get_attendance_history(self, limit: int = 100):
        db = SessionLocal()
        try:
            return db.query(AttendanceLog).order_by(AttendanceLog.checkin_at.desc()).limit(limit).all()
        finally:
            db.close()