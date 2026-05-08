## 1. Đăng ký khuôn mặt cho nhân viên (`employees.py`, `worker.py`)

### **Mô tả**
Quản trị viên tạo hồ sơ nhân viên mới và đăng ký khuôn mặt cho nhân viên đó.  
Hệ thống AI sẽ kiểm tra chất lượng ảnh, trích xuất đặc trưng khuôn mặt (ArcFace Embedding) và tính toán average embedding để lưu vào vector database.

### **Actor**
- **Chính:** Quản trị viên (Admin)
- **Phụ:** Celery Worker (xử lý AI nền)

### **Mục tiêu**
Tạo hồ sơ nhân viên hợp lệ và vector khuôn mặt sinh trắc học chính xác để phục vụ xác minh sau này.

### **Điều kiện tiên quyết**
- Quản trị viên đã đăng nhập vào hệ thống.
- `department_id` hợp lệ đã tồn tại trong cơ sở dữ liệu.
- Có từ **1 đến 3 ảnh khuôn mặt** của nhân viên.

### **Luồng xử lý chính**
1. Quản trị viên nhập:
   - Tên nhân viên
   - Mã nhân viên
   - ID phòng ban
2. Upload từ 1–3 ảnh khuôn mặt.
3. FastAPI kiểm tra số lượng ảnh hợp lệ.
4. Hệ thống tạo nhân viên mới trong SQL Database.
5. Ảnh được lưu tạm và upload lên MinIO.
6. Hệ thống gửi task `process_face_registration` đến Celery Worker.
7. Worker trích xuất embedding khuôn mặt bằng ArcFace.
8. AI kiểm tra:
   - Chất lượng ảnh
   - Đúng 1 khuôn mặt trong ảnh
9. Tính toán Average Embedding.
10. Lưu vector vào Qdrant Vector Database.

### **Luồng thay thế**
- Upload ít hơn 1 hoặc nhiều hơn 3 ảnh:
  - Hệ thống báo lỗi.
  - Không tạo nhân viên.

### **Điều kiện sau khi thực hiện**
- Hồ sơ nhân viên được lưu trong SQL DB.
- Ảnh gốc được lưu trong MinIO.
- Vector khuôn mặt được lưu trong Qdrant.

### **Các lỗi có thể xảy ra**
- Ảnh quá tối hoặc quá mờ.
- Không tìm thấy khuôn mặt.
- Có nhiều hơn 1 khuôn mặt trong ảnh.
- Lỗi kết nối:
  - PostgreSQL
  - MinIO
  - Qdrant

---
