import asyncio
from concurrent.futures import ThreadPoolExecutor
import cloudinary
from cloudinary.uploader import upload, destroy
from cloudinary.utils import cloudinary_url
from cloudinary.exceptions import Error as CloudinaryError


class CloudinaryService:
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
        url, _ = cloudinary_url(public_id, width=width, height=height, crop="fill")
        return url
