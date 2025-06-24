import asyncio
from concurrent.futures import ThreadPoolExecutor
import cloudinary
from cloudinary.uploader import upload, destroy
from cloudinary.utils import cloudinary_url
from cloudinary.exceptions import Error as CloudinaryError


class CloudinaryService:
    """
    Service class to interact asynchronously with Cloudinary API for uploading,
    deleting, and building URLs for media files.

    Args:
        cloud_name (str): Cloudinary cloud name.
        api_key (str): Cloudinary API key.
        api_secret (str): Cloudinary API secret.
        max_workers (int): Maximum number of worker threads for async execution.
    """

    def __init__(
        self, cloud_name: str, api_key: str, api_secret: str, max_workers: int = 5
    ):
        cloudinary.config(
            cloud_name=cloud_name, api_key=api_key, api_secret=api_secret, secure=True
        )
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def upload_file(
        self, file, public_id: str, width: int = 250, height: int = 250
    ) -> str:
        """
        Upload a file asynchronously to Cloudinary.

        Args:
            file: File object to upload (expects an object with a .file attribute).
            public_id (str): Public identifier to assign to the uploaded file.
            width (int, optional): Width for the resulting image URL (default 250).
            height (int, optional): Height for the resulting image URL (default 250).

        Returns:
            str: URL of the uploaded image with specified transformations.

        Raises:
            Exception: If Cloudinary upload fails.
        """

        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                self.executor,
                lambda: upload(file.file, public_id=public_id, overwrite=True),
            )

            url, _ = cloudinary_url(
                public_id,
                width=width,
                height=height,
                crop="fill",
                version=result.get("version"),
            )
            return url

        except CloudinaryError as e:
            raise Exception(f"Помилка при завантаженні файлу в Cloudinary: {e}")

    async def delete_file(self, public_id: str) -> dict:
        """
        Delete a file asynchronously from Cloudinary.

        Args:
            public_id (str): Public identifier of the file to delete.

        Returns:
            dict: Result from Cloudinary API deletion call.

        Raises:
            Exception: If Cloudinary deletion fails.
        """

        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                self.executor, lambda: destroy(public_id)
            )
            return result

        except CloudinaryError as e:
            raise Exception(f"Помилка при видаленні файлу з Cloudinary: {e}")

    async def build_url(
        self, public_id: str, width: int = 250, height: int = 250
    ) -> str:
        """
        Build a Cloudinary URL for a given public_id with specified transformations.

        Args:
            public_id (str): Public identifier of the file.
            width (int, optional): Width for the image (default 250).
            height (int, optional): Height for the image (default 250).

        Returns:
            str: URL string to access the file.
        """
        url, _ = cloudinary_url(public_id, width=width, height=height, crop="fill")
        return url
