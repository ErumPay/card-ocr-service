from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np

PreprocessingStep = Callable[[np.ndarray], np.ndarray]
PreprocessingVariant = str


@dataclass(frozen=True)
class PreprocessedImage:
    image: np.ndarray
    jpeg_bytes: bytes
    original_width: int
    original_height: int
    width: int
    height: int
    output_content_type: str = "image/jpeg"
    output_extension: str = ".jpg"


class ImagePreprocessor:
    DEFAULT_VARIANT = "hist_equalize"
    COMPARISON_VARIANTS = (
        "clahe",
        "hist_equalize",
        "clahe_sharpen",
        "hist_equalize_sharpen",
    )
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
    MAX_LONG_SIDE = 1024
    JPEG_QUALITY = 85
    CLAHE_CLIP_LIMIT = 2.0
    CLAHE_TILE_GRID_SIZE = (8, 8)
    SHARPEN_AMOUNT = 1.0
    SHARPEN_BLUR_KERNEL_SIZE = 3
    SUPPORTED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/heic", "image/heif"}
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
    HEIC_CONTENT_TYPES = {"image/heic", "image/heif"}
    HEIC_EXTENSIONS = {".heic", ".heif"}

    def __init__(
        self,
        sharpen_amount: float = SHARPEN_AMOUNT,
        sharpen_blur_kernel_size: int = SHARPEN_BLUR_KERNEL_SIZE,
    ) -> None:
        self.sharpen_amount = sharpen_amount
        self.sharpen_blur_kernel_size = sharpen_blur_kernel_size

    # 업로드 이미지를 OCR 입력 배열과 디버그용 JPEG bytes로 변환한다.
    def preprocess(
        self,
        image_bytes: bytes,
        content_type: str | None = None,
        filename: str | None = None,
        variant: PreprocessingVariant = DEFAULT_VARIANT,
    ) -> PreprocessedImage:
        self._validate_size(image_bytes)
        self._validate_image_type(content_type, filename)

        image = self._decode(image_bytes, content_type, filename)
        original_height, original_width = image.shape[:2]
        processed_image = self._apply_preprocessing_pipeline(image, variant)
        jpeg_bytes = self._encode_jpeg(processed_image)
        height, width = processed_image.shape[:2]

        return PreprocessedImage(
            image=processed_image,
            jpeg_bytes=jpeg_bytes,
            original_width=original_width,
            original_height=original_height,
            width=width,
            height=height,
        )

    # 빈 파일과 5MB 초과 파일은 OCR 처리 전에 차단한다.
    def _validate_size(self, image_bytes: bytes) -> None:
        if not image_bytes:
            raise ValueError("image file is empty")
        if len(image_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise ValueError("image file is too large")

    # Content-Type 또는 파일 확장자가 지원 범위인지 확인한다.
    def _validate_image_type(self, content_type: str | None, filename: str | None) -> None:
        normalized_content_type = self._normalize_content_type(content_type)
        suffix = self._suffix(filename)

        if normalized_content_type in self.SUPPORTED_CONTENT_TYPES:
            return
        if suffix in self.SUPPORTED_EXTENSIONS:
            return
        raise ValueError("unsupported image format")

    # HEIC/HEIF는 Pillow, JPEG/PNG는 OpenCV로 디코딩한다.
    def _decode(
        self,
        image_bytes: bytes,
        content_type: str | None,
        filename: str | None,
    ) -> np.ndarray:
        if self._is_heic(content_type, filename):
            return self._decode_heic(image_bytes)
        return self._decode_with_opencv(image_bytes)

    # JPEG/PNG bytes를 OpenCV 이미지 배열로 변환하고 디코딩 불가 파일은 차단한다.
    def _decode_with_opencv(self, image_bytes: bytes) -> np.ndarray:
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("unsupported image format")
        return image

    # iPhone HEIC/HEIF 이미지를 RGB로 열고 OpenCV가 쓰는 BGR 배열로 변환한다.
    def _decode_heic(self, image_bytes: bytes) -> np.ndarray:
        from PIL import Image
        from pillow_heif import register_heif_opener

        register_heif_opener()
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                rgb_image = image.convert("RGB")
                rgb_array = np.array(rgb_image)
                return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        except Exception as exception:
            raise ValueError("unsupported image format") from exception

    # 여러 전처리 기법을 순서대로 적용하는 공통 pipeline이다.
    def _apply_preprocessing_pipeline(
        self,
        image: np.ndarray,
        variant: PreprocessingVariant,
    ) -> np.ndarray:
        processed_image = image.copy()
        for step in self._preprocessing_steps(variant):
            processed_image = step(processed_image)
        return processed_image

    # 전처리 기법을 추가할 때 이 tuple에 메서드를 순서대로 넣는다.
    def _preprocessing_steps(self, variant: PreprocessingVariant) -> tuple[PreprocessingStep, ...]:
        base_steps = (self._resize_long_side, self._to_grayscale)
        match variant:
            case "clahe":
                return (*base_steps, self._apply_clahe)
            case "hist_equalize":
                return (*base_steps, self._apply_histogram_equalization)
            case "clahe_sharpen":
                return (*base_steps, self._apply_clahe, self._apply_sharpening)
            case "hist_equalize_sharpen":
                return (
                    *base_steps,
                    self._apply_histogram_equalization,
                    self._apply_sharpening,
                )
            case _:
                raise ValueError(f"unsupported preprocessing variant: {variant}")

    # 긴 변이 기준값보다 큰 이미지만 비율을 유지한 채 축소한다.
    def _resize_long_side(self, image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]
        long_side = max(width, height)
        if long_side <= self.MAX_LONG_SIDE:
            return image

        scale = self.MAX_LONG_SIDE / long_side
        next_size = (int(width * scale), int(height * scale))
        return cv2.resize(image, next_size, interpolation=cv2.INTER_AREA)

    # grayscale 이미지로 변환
    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # grayscale 이미지의 CLAHE 적용
    def _apply_clahe(self, image: np.ndarray) -> np.ndarray:
        if image.ndim != 2:
            raise ValueError("CLAHE requires grayscale image")
        clahe = cv2.createCLAHE(
            clipLimit=self.CLAHE_CLIP_LIMIT,
            tileGridSize=self.CLAHE_TILE_GRID_SIZE,
        )
        return clahe.apply(image)

    # 전체 밝기 분포를 균등화해서 CLAHE와 다른 대비 보정 결과를 비교한다.
    def _apply_histogram_equalization(self, image: np.ndarray) -> np.ndarray:
        if image.ndim != 2:
            raise ValueError("histogram equalization requires grayscale image")
        return cv2.equalizeHist(image)

    # unsharp mask 방식으로 글자 경계를 강조한다. amount 값을 조절해 강도를 바꿀 수 있다.
    def _apply_sharpening(self, image: np.ndarray) -> np.ndarray:
        if image.ndim != 2:
            raise ValueError("sharpening requires grayscale image")
        if self.sharpen_amount <= 0:
            return image

        kernel_size = self._odd_kernel_size(self.sharpen_blur_kernel_size)
        blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        return cv2.addWeighted(
            image,
            1.0 + self.sharpen_amount,
            blurred,
            -self.sharpen_amount,
            0,
        )

    def _odd_kernel_size(self, kernel_size: int) -> int:
        if kernel_size < 3:
            return 3
        if kernel_size % 2 == 0:
            return kernel_size + 1
        return kernel_size

    # 디버그 저장과 후속 OCR 입력 포맷 확인을 위해 JPEG bytes로 고정한다.
    def _encode_jpeg(self, image: np.ndarray) -> bytes:
        success, encoded = cv2.imencode(
            ".jpg",
            image,
            [cv2.IMWRITE_JPEG_QUALITY, self.JPEG_QUALITY],
        )
        if not success:
            raise ValueError("failed to encode image")
        return encoded.tobytes()

    def _is_heic(self, content_type: str | None, filename: str | None) -> bool:
        return (
            self._normalize_content_type(content_type) in self.HEIC_CONTENT_TYPES
            or self._suffix(filename) in self.HEIC_EXTENSIONS
        )

    def _normalize_content_type(self, content_type: str | None) -> str | None:
        if content_type is None:
            return None
        return content_type.lower().split(";")[0].strip()

    def _suffix(self, filename: str | None) -> str | None:
        if not filename:
            return None
        return Path(filename).suffix.lower()
