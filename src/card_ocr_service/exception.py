from dataclasses import dataclass
from enum import Enum

from card_ocr_service.schemas.error import ErrorDetail


@dataclass(frozen=True)
class ErrorCodeSpec:
    status: int
    code: str
    reason: str
    message: str


class ErrorCode(Enum):
    INVALID_REQUEST = ErrorCodeSpec(
        status=400,
        code="OCR-REQ-001",
        reason="INVALID_REQUEST",
        message="잘못된 요청입니다.",
    )
    OCR_ENGINE_FAILED = ErrorCodeSpec(
        status=500,
        code="OCR-OCR-900",
        reason="OCR_ENGINE_FAILED",
        message="OCR 처리 중 오류가 발생했습니다.",
    )
    INTERNAL_SERVER_ERROR = ErrorCodeSpec(
        status=500,
        code="OCR-SYS-900",
        reason="INTERNAL_SERVER_ERROR",
        message="알 수 없는 내부 오류가 발생했습니다.",
    )

    @property
    def status(self) -> int:
        return self.value.status

    @property
    def code(self) -> str:
        return self.value.code

    @property
    def reason(self) -> str:
        return self.value.reason

    @property
    def message(self) -> str:
        return self.value.message


class OcrException(Exception):
    def __init__(
        self,
        error_code: ErrorCode,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(error_code.message)
        self.error_code = error_code
        self.details = details or []
