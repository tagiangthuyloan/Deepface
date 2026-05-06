from pydantic import BaseModel
from datetime import datetime, time
from typing import List, Optional

# --- Departments (Phòng ban) ---
class DepartmentBase(BaseModel):
    name: str

class DepartmentOut(DepartmentBase):
    id: int
    class Config:
        from_attributes = True

# --- Department Permissions (Quyền theo phòng ban) ---
class DeptPermissionCreate(BaseModel):
    department_id: int
    door_id: int
    allowed_start_time: Optional[time] = None
    allowed_end_time: Optional[time] = None

class DeptPermissionOut(DeptPermissionCreate):
    id: int
    class Config:
        from_attributes = True

# --- Employees (Nhân viên) ---
class EmployeeBase(BaseModel):
    full_name: str
    employee_code: str
    department_id: int  # Bổ sung để bắt buộc chọn phòng ban khi đăng ký
    role: str = "user"

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeOut(EmployeeBase):
    id: int
    is_active: bool
    class Config: 
        from_attributes = True

# --- Permissions (Quyền cá nhân/ngoại lệ) ---
class PermissionBase(BaseModel):
    employee_id: int
    door_id: int
    allowed_start_time: Optional[time] = None
    allowed_end_time: Optional[time] = None

class PermissionUpdate(BaseModel):
    door_id: int
    allowed_start_time: Optional[time] = None
    allowed_end_time: Optional[time] = None

class PermissionOut(PermissionBase):
    id: int
    class Config: 
        from_attributes = True

# --- Doors (Cửa/Khu vực) ---
class DoorBase(BaseModel):
    name: str
    description: Optional[str] = None

class DoorOut(DoorBase):
    id: int
    class Config: 
        from_attributes = True

# --- Attendance (Điểm danh & Log) ---
class AttendanceLogOut(BaseModel):
    id: int
    employee_id: Optional[int]
    door_id: Optional[int]
    checkin_at: datetime
    status: str
    reason: Optional[str]
    image_snapshot: Optional[str] = None
    class Config: 
        from_attributes = True

class IdentifyRequest(BaseModel):
    door_name: str