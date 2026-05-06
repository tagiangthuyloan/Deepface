import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

class VectorDBService:
    def __init__(self):
        self.client = QdrantClient(host=os.getenv("QDRANT_HOST", "qdrant"), port=6333)

    def init_collection(self, collection_name: str, vector_size: int):
        collections = self.client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        if not exists:
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def upsert(self, collection_name, vector, employee_id, payload=None):
        # Quan trọng: Dùng chính employee_id từ SQL làm ID của point
        self.client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=employee_id, # Phải là số nguyên hoặc UUID
                    vector=vector,
                    payload=payload or {"employee_id": employee_id}
                )
            ]
        )
    # def upsert(self, collection_name, vector, employee_id, payload=None):
    # # Tạo một ID ngẫu nhiên cho mỗi lần đăng ký ảnh (không bị ghi đè)
    # point_id = str(uuid.uuid4()) 
    
    # self.client.upsert(
    #     collection_name=collection_name,
    #     points=[
    #         PointStruct(
    #             id=point_id, 
    #             vector=vector,
    #             payload=payload or {"user_id": employee_id}
    #         )
    #     ]
    # )

    def search(self, vector, collection_name="employees", limit=1):
        try:
            # Đảm bảo dùng self.client.search
            return self.client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=limit,
                with_payload=True
            )
        except AttributeError:
            # Nếu phiên bản cũ hơn hoặc có thay đổi, thử dùng phương thức thay thế
            print("DEBUG: Thử phương thức query_points thay thế...")
            return self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=limit
            ).points
        except Exception as e:
            print(f"Lỗi tìm kiếm: {e}")[cite: 6]
            return []
        
    def delete_vector(self, collection_name: str, employee_id: int):
        self.client.delete(
            collection_name=collection_name,
            points_selector=[employee_id] # Vì ID trong Qdrant trùng với ID trong SQL
        )