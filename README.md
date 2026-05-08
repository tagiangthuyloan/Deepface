# FaceAccess AI - Hệ thống Kiểm soát truy cập & chấm công sử dụng khuôn mặt

Hệ thống **FaceAccess AI** là giải pháp kiểm soát cửa ra vào và chấm công thông minh sử dụng công nghệ nhận diện khuôn mặt.
Hệ thống tích hợp xử lý Vector Database để đảm bảo độ chính xác và khả năng phân quyền truy cập đa tầng theo thời gian thực.

## 🌟 Tính năng nổi bật

**Đăng ký khuôn mặt đa mẫu**: Hỗ trợ đăng ký từ 1 đến 5 ảnh cho mỗi nhân viên để tối ưu hóa độ chính xác của mẫu sinh trắc học.
**Kiểm định chất lượng (AI Quality Check)**: Tự động kiểm tra độ rõ nét, góc nghiêng và ánh sáng trước khi lưu mẫu.
**Nhận diện & Xác thực tức thì**: Sử dụng Qdrant để so khớp vector 512 chiều với ngưỡng tin cậy (threshold) là 0.5.
**Phân quyền truy cập linh hoạt**:
    **Kế thừa (Inheritance)**: Nhân viên tự động nhận quyền truy cập từ phòng ban trực thuộc.
    **Đặc cách (Override)**: Thiết lập quyền riêng cho cá nhân để ghi đè hoặc bổ sung vào quyền phòng ban.
**Kiểm soát khung giờ (Time-based Access)**: Giới hạn thời gian ra vào theo cấu hình bắt đầu và kết thúc.
**Xử lý bất đồng bộ (Async Task)**: Sử dụng Celery để trích xuất Embedding khuôn mặt, giúp hệ thống không bị treo khi có nhiều người đăng ký cùng lúc.
