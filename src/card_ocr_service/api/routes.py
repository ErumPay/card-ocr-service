from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from card_ocr_service.schemas.ocr import CardOcrResponse
from card_ocr_service.service.ocr_service import OcrService

router = APIRouter()
ocr_service = OcrService()


@router.get("/actuator/health")
def health() -> dict[str, str]:
    return {"status": "UP"}


@router.post("/api/v1/cards/ocr", response_model=CardOcrResponse)
async def extract_card(image: Annotated[UploadFile, File(...)]) -> CardOcrResponse:
    image_bytes = await image.read()
    return ocr_service.extract(
        image_bytes=image_bytes,
        content_type=image.content_type,
        filename=image.filename,
    )
