#!/usr/bin/env python3
"""Initialize MinIO buckets for Cloud Storage."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.utils.minio_client import get_minio_client
from app.config import settings


def init():
    client = get_minio_client()
    for bucket in [settings.MINIO_FILES_BUCKET, settings.MINIO_THUMBNAILS_BUCKET]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"Created bucket: {bucket}")
        else:
            print(f"Bucket already exists: {bucket}")


if __name__ == "__main__":
    init()
