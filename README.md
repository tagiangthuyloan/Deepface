# DeepFace: Hệ thống kiểm soát ra vào cửa và chấm công bằng khuôn mặt
## 1. Use case

### Nhiệm vụ: Hệ thống kiểm soát quá trình ra vào cửa của công ty đồng thời thực hiện chấm công cho nhân viên trong thời gian thực.
'''
Camera tại cửa chụp ảnh realtime 
-> API Backend FastAPI tiếp nhận
-> Trích xuất Embedding khuôn mặt (DeepFace - ArcFace Model)
-> Tìm kiếm khuôn mặt tương tự trong Vector DB (Qdrant) với ngưỡng score > 0.5
-> Nhận diện ID nhân viên 
-> Kiểm tra logic quyền truy cập (PostgreSQL):
     1. Tài khoản có Active không?
     2. Có quyền cá nhân tại cửa này không?
     3. Nếu không, có quyền kế thừa từ Phòng ban tại cửa này không?
     4. Giờ hiện tại có nằm trong khung giờ cho phép không?
-> Trả về kết quả: Mở cửa (SUCCESS) hoặc Từ chối (DENIED + Lý do)
-> Lưu lịch sử nhận diện và kết quả kiểm tra vào PostgreSQL
'''
Hệ thống nhận diện khuôn mặt bằng webcam realtime. Dự án được thiết kế chứa các phần: có frontend nhân viên, frontend quản trị, backend, database, object storage, vector database, queue, Nginx reverse proxy, Docker Compose, monitoring và tài liệu tái hiện. ✨%Chỉnh sửa lại
