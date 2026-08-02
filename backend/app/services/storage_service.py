"""
File storage abstraction. Swap backends via STORAGE_BACKEND env var
without changing calling code.
"""
import os
import uuid
from abc import ABC, abstractmethod

from app.core.config import settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, file_bytes: bytes, filename: str, subdir: str = "resumes") -> str:
        """Persist file bytes; return a storage path/key."""

    @abstractmethod
    def get_local_path(self, storage_path: str) -> str:
        """Return a filesystem path usable for local parsing (download if remote)."""

    @abstractmethod
    def delete(self, storage_path: str) -> None:
        ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def save(self, file_bytes: bytes, filename: str, subdir: str = "resumes") -> str:
        dir_path = os.path.join(self.base_path, subdir)
        os.makedirs(dir_path, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        full_path = os.path.join(dir_path, unique_name)
        with open(full_path, "wb") as f:
            f.write(file_bytes)
        return os.path.join(subdir, unique_name)

    def get_local_path(self, storage_path: str) -> str:
        return os.path.join(self.base_path, storage_path)

    def delete(self, storage_path: str) -> None:
        full_path = os.path.join(self.base_path, storage_path)
        if os.path.exists(full_path):
            os.remove(full_path)


class S3StorageBackend(StorageBackend):
    """
    AWS S3 backend. Requires boto3 and valid credentials.
    Downloads to a local tmp file for parsing since PyMuPDF/pdfplumber
    need a filesystem path (or BytesIO, which could be used instead
    to avoid the disk round-trip — left as an optimization).
    """

    def __init__(self, bucket: str, region: str):
        import boto3  # local import so boto3 is optional unless S3 is used

        self.bucket = bucket
        self.client = boto3.client("s3", region_name=region)

    def save(self, file_bytes: bytes, filename: str, subdir: str = "resumes") -> str:
        key = f"{subdir}/{uuid.uuid4().hex}_{filename}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=file_bytes)
        return key

    def get_local_path(self, storage_path: str) -> str:
        tmp_path = f"/tmp/{uuid.uuid4().hex}_{os.path.basename(storage_path)}"
        self.client.download_file(self.bucket, storage_path, tmp_path)
        return tmp_path

    def delete(self, storage_path: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_path)


def get_storage_backend() -> StorageBackend:
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageBackend(bucket=settings.S3_BUCKET_NAME, region=settings.S3_REGION)
    # Supabase Storage is S3-compatible; SupabaseStorageBackend can reuse
    # S3StorageBackend pointed at Supabase's S3-compatible endpoint, or be
    # implemented with the supabase-py client. Defaulting to local for now.
    return LocalStorageBackend(base_path=settings.LOCAL_STORAGE_PATH)
