import io
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.storage_service import StorageError, StorageService


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.put_object.return_value = None
    response_mock = MagicMock()
    response_mock.read.return_value = b"file content"
    response_mock.close.return_value = None
    response_mock.release_conn.return_value = None
    client.get_object.return_value = response_mock
    client.remove_object.return_value = None
    client.presigned_get_object.return_value = "https://minio.local/file"
    client.presigned_put_object.return_value = "https://minio.local/upload"
    client.stat_object.return_value = MagicMock(size=1024, content_type="text/plain", etag="abc", last_modified=None)
    client.copy_object.return_value = None
    return client


@pytest.fixture
def storage(mock_client):
    return StorageService(client=mock_client)


def test_upload_returns_key(storage):
    key = storage.upload_file(b"content", "test/key", "text/plain")
    assert key == "test/key"


def test_download_returns_bytes(storage):
    data = storage.download_file("test/key")
    assert data == b"file content"


def test_delete_file(storage, mock_client):
    storage.delete_file("test/key")
    mock_client.remove_object.assert_called_once()


def test_presigned_download_url(storage):
    url = storage.get_presigned_download_url("test/key")
    assert url.startswith("https://")


def test_presigned_upload_url(storage):
    url = storage.get_presigned_upload_url("test/key")
    assert url.startswith("https://")


def test_upload_with_metadata(storage, mock_client):
    storage.upload_file(b"content", "test/key", metadata={"hash": "abc123"})
    call_kwargs = mock_client.put_object.call_args
    assert call_kwargs is not None


def test_connection_error(mock_client):
    mock_client.get_object.side_effect = Exception("Connection refused")
    storage = StorageService(client=mock_client)
    with pytest.raises(StorageError, match="Storage connection error"):
        storage.download_file("test/key")


def test_file_not_found(mock_client):
    from minio.error import S3Error
    mock_client.get_object.side_effect = S3Error("NoSuchKey", "NoSuchKey", resource="test", request_id="1", host_id="1", response="err")
    storage = StorageService(client=mock_client)
    with pytest.raises(StorageError, match="File not found"):
        storage.download_file("test/key")


def test_copy_object(storage, mock_client):
    storage.copy_object("source/key", "dest/key")
    mock_client.copy_object.assert_called_once()


def test_get_object_metadata(storage):
    meta = storage.get_object_metadata("test/key")
    assert "size" in meta
    assert "content_type" in meta
