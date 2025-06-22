from fastapi import Request
from src.services.cloudinary_service import CloudinaryService


def get_cloudinary_service(request: Request) -> CloudinaryService:
    return request.app.state.cloudinary_service
