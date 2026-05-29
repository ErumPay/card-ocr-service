import argparse
from pathlib import Path

from card_ocr_service.preprocessing.image_preprocessor import ImagePreprocessor
from card_ocr_service.service.ocr_engine import PaddleOcrEngine


def main() -> None:
    # PaddleOCR이 실제로 읽은 text와 confidence를 콘솔에 출력하는 로컬 디버그 스크립트입니다.
    args = parse_args()
    image_path = Path(args.image)
    if not image_path.exists():
        raise SystemExit(f"Image file does not exist: {image_path}")

    preprocessed_image = ImagePreprocessor().preprocess(
        image_path.read_bytes(),
        filename=image_path.name,
    )
    lines = PaddleOcrEngine().extract_texts(preprocessed_image.image)

    print(
        f"{image_path} "
        f"{preprocessed_image.original_width}x{preprocessed_image.original_height} -> "
        f"{preprocessed_image.width}x{preprocessed_image.height}"
    )
    if not lines:
        print("No OCR text detected")
        return

    for index, line in enumerate(lines, start=1):
        print(f"{index:02d}. {line.confidence:.4f} | {line.text}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print raw PaddleOCR text output.")
    parser.add_argument("--image", default="data/IMG_3875.HEIC")
    return parser.parse_args()


if __name__ == "__main__":
    main()
