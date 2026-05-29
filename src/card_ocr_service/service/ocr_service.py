from card_ocr_service.preprocessing.image_preprocessor import ImagePreprocessor
from card_ocr_service.schemas.ocr import CardOcrResponse


class OcrService:
    def __init__(self) -> None:
        self._preprocessor = ImagePreprocessor()

    def extract(self, image_bytes: bytes, content_type: str | None) -> CardOcrResponse:
        if not content_type or content_type not in {"image/jpeg", "image/png"}:
            return CardOcrResponse(
                card_number=None,
                expiry_ym=None,
                confidence=0.0,
                warnings=["UNSUPPORTED_IMAGE_FORMAT"],
            )

        self._preprocessor.validate(image_bytes)
        return CardOcrResponse(
            card_number=None,
            expiry_ym=None,
            confidence=0.0,
            warnings=["OCR_ENGINE_NOT_CONNECTED"],
        )

