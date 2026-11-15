import os
import uuid
import mimetypes
from typing import Dict, Any, Optional
from app.config import settings

class StorageService:
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.local_dir = settings.STORAGE_LOCAL_DIR
        os.makedirs(self.local_dir, exist_ok=True)

    def save_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        mime_type: Optional[str] = None,
        owner_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        Saves file to local disk or remote object storage (S3/Supabase/Cloudinary).
        Returns metadata dict containing file_url, file_name, file_size, and mime_type.
        """
        ext = os.path.splitext(original_filename)[1]
        if not ext:
            ext = ".bin"
        unique_name = f"{uuid.uuid4().hex}_{original_filename.replace(' ', '_')}"
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(original_filename)
            mime_type = mime_type or "application/octet-stream"

        file_size = len(file_bytes)

        # 1. Cloudinary fallback/choice if configured
        if self.storage_type == "cloudinary" and settings.CLOUDINARY_URL:
            try:
                import cloudinary
                import cloudinary.uploader
                # Configure cloudinary from CLOUDINARY_URL
                upload_res = cloudinary.uploader.upload(
                    file_bytes,
                    public_id=f"vayocare/{owner_id}/{unique_name}",
                    resource_type="auto"
                )
                return {
                    "file_url": upload_res.get("secure_url", upload_res.get("url")),
                    "file_name": unique_name,
                    "file_size": file_size,
                    "mime_type": mime_type,
                    "storage_provider": "cloudinary"
                }
            except Exception:
                pass  # Fall back to local storage seamlessly

        # 2. S3/Supabase fallback/choice if configured
        if self.storage_type in ("s3", "supabase") and settings.S3_BUCKET and settings.S3_ACCESS_KEY:
            try:
                import boto3
                s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_KEY,
                    region_name=settings.S3_REGION
                )
                key = f"uploads/{owner_id}/{unique_name}"
                s3_client.put_object(
                    Bucket=settings.S3_BUCKET,
                    Key=key,
                    Body=file_bytes,
                    ContentType=mime_type
                )
                file_url = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{key}"
                return {
                    "file_url": file_url,
                    "file_name": unique_name,
                    "file_size": file_size,
                    "mime_type": mime_type,
                    "storage_provider": "s3"
                }
            except Exception:
                pass  # Fall back to local storage

        # 3. Local storage (Default & reliable local development / tests)
        local_path = os.path.join(self.local_dir, unique_name)
        with open(local_path, "wb") as f:
            f.write(file_bytes)

        file_url = f"{settings.PUBLIC_BASE_URL}/uploads/{unique_name}"
        return {
            "file_url": file_url,
            "file_name": unique_name,
            "file_size": file_size,
            "mime_type": mime_type,
            "storage_provider": "local",
            "local_path": local_path
        }

storage_service = StorageService()
