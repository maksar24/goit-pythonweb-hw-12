import pytest
from unittest.mock import patch
from cloudinary.exceptions import Error as CloudinaryError

from src.services.cloudinary_service import CloudinaryService


@pytest.fixture
def cloudinary_service():
    return CloudinaryService("test_cloud", "test_key", "test_secret", max_workers=2)


@pytest.mark.asyncio
@patch("src.services.cloudinary_service.upload")
@patch("src.services.cloudinary_service.cloudinary_url")
async def test_upload_file_success(
    mock_cloudinary_url, mock_upload, cloudinary_service
):
    mock_upload.return_value = {"version": 123}
    mock_cloudinary_url.return_value = ("http://cloudinary.com/test.jpg", None)

    class FileMock:
        file = "fake_file_data"

    result = await cloudinary_service.upload_file(FileMock(), "public_id_test")

    mock_upload.assert_called_once_with(
        "fake_file_data", public_id="public_id_test", overwrite=True
    )
    mock_cloudinary_url.assert_called_once_with(
        "public_id_test", width=250, height=250, crop="fill", version=123
    )
    assert result == "http://cloudinary.com/test.jpg"


@pytest.mark.asyncio
@patch(
    "src.services.cloudinary_service.upload",
    side_effect=CloudinaryError("Upload failed"),
)
async def test_upload_file_failure(mock_upload, cloudinary_service):
    class FileMock:
        file = "fake_file_data"

    with pytest.raises(Exception) as exc_info:
        await cloudinary_service.upload_file(FileMock(), "public_id_test")

    assert "Помилка при завантаженні файлу" in str(exc_info.value)


@pytest.mark.asyncio
@patch("src.services.cloudinary_service.destroy")
async def test_delete_file_success(mock_destroy, cloudinary_service):
    mock_destroy.return_value = {"result": "ok"}

    result = await cloudinary_service.delete_file("public_id_test")

    mock_destroy.assert_called_once_with("public_id_test")
    assert result == {"result": "ok"}


@pytest.mark.asyncio
@patch(
    "src.services.cloudinary_service.destroy",
    side_effect=CloudinaryError("Delete failed"),
)
async def test_delete_file_failure(mock_destroy, cloudinary_service):
    with pytest.raises(Exception) as exc_info:
        await cloudinary_service.delete_file("public_id_test")

    assert "Помилка при видаленні файлу" in str(exc_info.value)


@pytest.mark.asyncio
async def test_build_url(cloudinary_service):
    with patch(
        "src.services.cloudinary_service.cloudinary_url",
        return_value=("http://cloudinary.com/test.jpg", None),
    ) as mock_cloudinary_url:
        url = await cloudinary_service.build_url(
            "public_id_test", width=300, height=300
        )
        mock_cloudinary_url.assert_called_once_with(
            "public_id_test", width=300, height=300, crop="fill"
        )
        assert url == "http://cloudinary.com/test.jpg"
