"""File storage service — GCS for production, local for development."""

import os
import shutil
import uuid
from pathlib import Path

from app.config import settings

LOCAL_STORAGE_DIR = Path("uploads")


async def upload_file(file_data: bytes, filename: str, content_type: str | None = None) -> str:
    """Upload file and return storage path.

    Uses GCS in production, local filesystem in development.
    """
    file_id = str(uuid.uuid4())
    ext = Path(filename).suffix
    storage_key = f"{file_id}{ext}"

    if settings.gcs_bucket and settings.gcs_credentials_path:
        return await _upload_gcs(file_data, storage_key, content_type)
    else:
        return await _upload_local(file_data, storage_key)


async def _upload_local(file_data: bytes, storage_key: str) -> str:
    """Save file to local filesystem (development)."""
    LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    file_path = LOCAL_STORAGE_DIR / storage_key
    file_path.write_bytes(file_data)
    return str(file_path)


async def _upload_gcs(file_data: bytes, storage_key: str, content_type: str | None) -> str:
    """Upload file to Google Cloud Storage."""
    from google.cloud import storage

    client = storage.Client.from_service_account_json(settings.gcs_credentials_path)
    bucket = client.bucket(settings.gcs_bucket)
    blob = bucket.blob(f"documents/{storage_key}")
    blob.upload_from_string(file_data, content_type=content_type)
    return f"gs://{settings.gcs_bucket}/documents/{storage_key}"


async def get_local_path(storage_path: str) -> str:
    """Get a local file path for Cognee processing.

    If file is on GCS, downloads to temp location first.
    """
    if storage_path.startswith("gs://"):
        return await _download_from_gcs(storage_path)
    return storage_path


async def _download_from_gcs(gcs_path: str) -> str:
    """Download file from GCS to a local temp path."""
    from google.cloud import storage

    parts = gcs_path.replace("gs://", "").split("/", 1)
    bucket_name, blob_name = parts[0], parts[1]

    client = storage.Client.from_service_account_json(settings.gcs_credentials_path)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    tmp_dir = Path("/tmp/zettelcognee")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    local_path = tmp_dir / Path(blob_name).name
    blob.download_to_filename(str(local_path))
    return str(local_path)
