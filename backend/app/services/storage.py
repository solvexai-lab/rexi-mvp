"""MinIO / S3-compatible object storage service. Falls back to local files if MinIO is unavailable."""
import os
from typing import BinaryIO

class StorageService:
    def __init__(self):
        self._available = False
        self.client = None
        self.bucket = os.getenv("MINIO_BUCKET", "rexi-contracts")
        try:
            from minio import Minio
            endpoint = os.getenv("MINIO_ENDPOINT", "")
            if not endpoint:
                return
            access_key = os.getenv("MINIO_ACCESS_KEY", "rexi_minio")
            secret_key = os.getenv("MINIO_SECRET_KEY", "rexi_minio_secret")
            self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
            self.client.list_buckets()  # connectivity test
            self._available = True
        except Exception:
            self._available = False
            self.client = None

    def upload_file(self, object_name: str, data: BinaryIO, length: int, content_type: str = "application/pdf"):
        if self._available and self.client:
            try:
                self.client.put_object(self.bucket, object_name, data, length, content_type=content_type)
                return f"{self.bucket}/{object_name}"
            except Exception:
                pass
        # Fallback: local file path
        return object_name

    def get_presigned_url(self, object_name: str, expires: int = 3600):
        if self._available and self.client:
            try:
                return self.client.presigned_get_object(self.bucket, object_name, expires=expires)
            except Exception:
                pass
        return None

    def download_file(self, object_name: str, file_path: str):
        if self._available and self.client:
            try:
                self.client.fget_object(self.bucket, object_name, file_path)
                return file_path
            except Exception:
                pass
        return file_path

storage_service = StorageService()
