from dataclasses import dataclass

import numpy as np

from card_ocr_service.parser.card_parser import find_card_number, normalize_expiry_ym
from card_ocr_service.preprocessing.image_preprocessor import ImagePreprocessor
from card_ocr_service.schemas.ocr import CardOcrResponse
from card_ocr_service.service.ocr_engine import OcrEngine, OcrTextLine, PaddleOcrEngine


@dataclass(frozen=True)
class OcrAttemptResult:
    card_number: str | None
    expiry_ym: str | None
    confidence: float
    warnings: list[str]


class OcrService:
    FALLBACK_ROTATIONS = (1, 3)

    def __init__(self, ocr_engine: OcrEngine | None = None) -> None:
        self._preprocessor = ImagePreprocessor()
        self._ocr_engine = ocr_engine or PaddleOcrEngine()

    def extract(
        self,
        image_bytes: bytes,
        content_type: str | None,
        filename: str | None,
    ) -> CardOcrResponse:
        try:
            # 업로드 이미지를 decode/resize/grayscale 등 OCR 입력용 이미지로 먼저 변환한다.
            preprocessed_image = self._preprocessor.preprocess(
                image_bytes,
                content_type=content_type,
                filename=filename,
            )
        except ValueError:
            return CardOcrResponse(
                card_number=None,
                expiry_ym=None,
                confidence=0.0,
                warnings=["UNSUPPORTED_IMAGE_FORMAT"],
            )

        try:
            # 전처리된 이미지를 PaddleOCR에 넘기고, OCR text를 카드 도메인 응답으로 바꾼다.
            result = self._extract_with_rotation_fallback(preprocessed_image.image)
        except Exception:
            return CardOcrResponse(
                card_number=None,
                expiry_ym=None,
                confidence=0.0,
                warnings=["OCR_ENGINE_FAILED"],
            )

        return CardOcrResponse(
            card_number=result.card_number,
            expiry_ym=result.expiry_ym,
            confidence=result.confidence,
            warnings=result.warnings,
        )

    def _extract_with_rotation_fallback(self, image: np.ndarray) -> OcrAttemptResult:
        # 정방향 인식이 부족하면 세로로 들어온 카드까지 잡기 위해 90도/270도 회전을 재시도한다.
        result = self._extract_from_image(image)
        if self._is_complete(result):
            return result

        best_result = result
        for rotated_image in self._rotated_fallback_images(image):
            rotated_result = self._extract_from_image(rotated_image)
            if self._is_complete(rotated_result):
                return rotated_result
            if self._score(rotated_result) > self._score(best_result):
                best_result = rotated_result
        return best_result

    def _extract_from_image(self, image: np.ndarray) -> OcrAttemptResult:
        # PaddleOCR이 읽은 여러 줄의 text를 하나로 합쳐 카드번호/유효기간 후보를 찾는다.
        ocr_lines = self._ocr_engine.extract_texts(image)
        ocr_text = " ".join(line.text for line in ocr_lines)
        card_number = find_card_number(ocr_text)
        expiry_ym = normalize_expiry_ym(ocr_text)
        return OcrAttemptResult(
            card_number=card_number,
            expiry_ym=expiry_ym,
            confidence=self._confidence(ocr_lines),
            warnings=self._warnings(card_number, expiry_ym, ocr_lines),
        )

    def _rotated_fallback_images(self, image: np.ndarray) -> list[np.ndarray]:
        return [
            np.ascontiguousarray(np.rot90(image, k=rotation))
            for rotation in self.FALLBACK_ROTATIONS
        ]

    def _is_complete(self, result: OcrAttemptResult) -> bool:
        return result.card_number is not None and result.expiry_ym is not None

    def _score(self, result: OcrAttemptResult) -> float:
        detected_fields = int(result.card_number is not None) + int(result.expiry_ym is not None)
        return detected_fields + result.confidence

    def _warnings(
        self,
        card_number: str | None,
        expiry_ym: str | None,
        ocr_lines: list[OcrTextLine],
    ) -> list[str]:
        warnings: list[str] = []
        if not ocr_lines:
            warnings.append("OCR_TEXT_NOT_DETECTED")
        if card_number is None:
            warnings.append("CARD_NUMBER_NOT_DETECTED")
        if expiry_ym is None:
            warnings.append("EXPIRY_NOT_DETECTED")
        return warnings

    def _confidence(self, ocr_lines: list[OcrTextLine]) -> float:
        if not ocr_lines:
            return 0.0
        return round(max(line.confidence for line in ocr_lines), 4)
