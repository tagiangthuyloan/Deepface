import cv2
import numpy as np
from deepface import DeepFace

class VisionService:
    def __init__(self):
        # THAY ĐỔI QUAN TRỌNG: 
        # ArcFace là model mạnh nhất hiện nay trong DeepFace (512 dimensions)
        # Nó vượt trội hơn VGG-Face về khả năng nhận diện góc nghiêng và ánh sáng phức tạp.
        self.model_name = "ArcFace"  
        self.detector = "retinaface"  # Giữ nguyên vì đây đã là detector mạnh nhất

    def check_image_quality(self, image_path: str):
        """Kiểm tra chất lượng ảnh (Giữ nguyên logic của bạn vì nó rất tốt)"""
        img = cv2.imread(image_path)
        if img is None:
            return False, "Không thể đọc file ảnh."

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Kiểm tra độ sáng
        brightness = gray.mean()
        if brightness < 40: return False, "Ảnh quá tối."
        if brightness > 220: return False, "Ảnh quá chói."

        # Kiểm tra độ nhòe
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 70: return False, "Ảnh quá nhòe."

        try:
            # Sử dụng retinaface để đếm mặt
            faces = DeepFace.extract_faces(
                img_path=image_path,
                detector_backend=self.detector,
                enforce_detection=False
            )
            
            face_count = len(faces)
            if face_count == 0: return False, "Không tìm thấy khuôn mặt."
            if face_count > 1: return False, f"Tìm thấy {face_count} người."
            
            return True, "Chất lượng ảnh đạt yêu cầu."
        except Exception as e:
            return False, f"Lỗi AI: {str(e)}"

    def get_embedding(self, image_path: str):
        try:
            objs = DeepFace.represent(
                img_path=image_path, 
                model_name=self.model_name,
                enforce_detection=True, # Bật True để đảm bảo có mặt mới lấy vector
                detector_backend=self.detector,
                align=False,
                normalization="base" # Dùng "base" (0-1) cho ổn định nhất
            )
            if not objs: return None
            
            embedding = np.array(objs[0]["embedding"])
            # Luôn luôn chuẩn hóa L2 ngay tại đây để đảm bảo vector ra khỏi hàm này là chuẩn 100%
            norm = np.linalg.norm(embedding)
            return (embedding / norm).tolist()
        except Exception as e:
            raise ValueError(f"Lỗi: {str(e)}")