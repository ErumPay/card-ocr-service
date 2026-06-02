from dataclasses import dataclass
from typing import Any, Protocol

import cv2
import numpy as np


@dataclass(frozen=True)
class OcrTextLine:
    # PaddleOCR의 한 줄 인식 결과를 서비스 내부에서 쓰기 쉬운 형태로 줄인 값이다.
    text: str
    confidence: float


class OcrEngine(Protocol):
    def extract_texts(self, image: np.ndarray) -> list[OcrTextLine]:
        pass


class PaddleOcrEngine:
    def __init__(self) -> None:
        self._ocr_client: Any | None = None

    def preload(self) -> None:
        # 서버 시작 시 모델을 미리 로딩해 첫 OCR 요청 지연을 줄인다.
        self._client()

    def extract_texts(self, image: np.ndarray) -> list[OcrTextLine]:
        # PaddleOCR에 넘기기 직전에 grayscale 이미지를 BGR 3채널 이미지로 맞춘다.
        ocr_input = self._to_paddle_input(image)

        # PaddleOCR이 이미지에서 텍스트 박스와 인식 text/confidence를 추출한다.
        result = self._client().ocr(ocr_input, cls=False)

        # PaddleOCR raw result는 중첩 list 구조라 우리 서비스 DTO로 정규화한다.
        return self._parse_result(result)

    def _client(self) -> Any:
        if self._ocr_client is None:
            from paddleocr import PaddleOCR

            # PaddleOCR 모델 객체를 생성한다. 기본 실행에서는 FastAPI lifespan에서 미리 호출한다.
            self._ocr_client = PaddleOCR(
                use_angle_cls=False,
                lang="en",
                show_log=False,
                det_limit_side_len=512,
            )
        return self._ocr_client

    def _to_paddle_input(self, image: np.ndarray) -> np.ndarray:
        # 전처리 pipeline 결과가 단일 채널이면 PaddleOCR 입력용 3채널 이미지로 변환한다.
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        return image

    def _parse_result(self, result: Any) -> list[OcrTextLine]:
        # PaddleOCR 결과 중 텍스트와 confidence만 꺼내 서비스 내부 표준 형태로 변환한다.
        lines: list[OcrTextLine] = []
        for entry in self._flatten_result(result):
            parsed_line = self._parse_line(entry)
            if parsed_line is not None:
                lines.append(parsed_line)
        return lines

    def _flatten_result(self, result: Any) -> list[Any]:
        # PaddleOCR 버전/입력 방식에 따라 결과가 [line, ...] 또는 [[line, ...]] 형태로 온다.
        if not isinstance(result, list):
            return []
        if not result:
            return []
        if self._parse_line(result[0]) is not None:
            return result

        flattened: list[Any] = []
        for page in result:
            if isinstance(page, list):
                flattened.extend(page)
        return flattened

    def _parse_line(self, entry: Any) -> OcrTextLine | None:
        # 일반적인 PaddleOCR line 구조: [box, (text, confidence)].
        if not isinstance(entry, list | tuple) or len(entry) < 2:
            return None

        text_score = entry[1]
        if not isinstance(text_score, list | tuple) or len(text_score) < 2:
            return None

        text, score = text_score[0], text_score[1]
        if not isinstance(text, str):
            return None

        try:
            confidence = float(score)
        except (TypeError, ValueError):
            confidence = 0.0

        return OcrTextLine(text=text, confidence=confidence)
