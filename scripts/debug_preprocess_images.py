import argparse
from pathlib import Path

from card_ocr_service.preprocessing.image_preprocessor import ImagePreprocessor

SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


def main() -> None:
    # ImagePreprocessor 결과를 파일로 저장하기 위한 디버그 진입점입니다.
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    preprocessor = ImagePreprocessor(
        sharpen_amount=args.sharpen_amount,
        sharpen_blur_kernel_size=args.sharpen_blur_kernel_size,
    )
    processed_count = 0
    variants = args.variants or ImagePreprocessor.COMPARISON_VARIANTS

    # 지원 확장자 파일만 읽어서 variant별 ImagePreprocessor 결과를 그대로 저장합니다.
    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        image_bytes = path.read_bytes()
        for variant in variants:
            result = preprocessor.preprocess(
                image_bytes,
                filename=path.name,
                variant=variant,
            )
            suffix = path.suffix.lower().lstrip(".")
            output_path = output_dir / f"{path.stem}_{suffix}_{variant}.jpg"
            output_path.write_bytes(result.jpeg_bytes)
            processed_count += 1

            print(
                f"{path.name} [{variant}] -> {output_path} "
                f"{result.original_width}x{result.original_height} -> "
                f"{result.width}x{result.height}, {len(result.jpeg_bytes)} bytes"
            )

    if processed_count == 0:
        print(f"No supported images found in {input_dir}")


def parse_args() -> argparse.Namespace:
    # 입력/출력 폴더만 바꿀 수 있게 최소 옵션만 둡니다.
    parser = argparse.ArgumentParser(description="Save ImagePreprocessor output images.")
    parser.add_argument("--input-dir", default="data")
    parser.add_argument("--output-dir", default="data/processed")
    parser.add_argument("--sharpen-amount", type=float, default=ImagePreprocessor.SHARPEN_AMOUNT)
    parser.add_argument(
        "--sharpen-blur-kernel-size",
        type=int,
        default=ImagePreprocessor.SHARPEN_BLUR_KERNEL_SIZE,
    )
    parser.add_argument(
        "--variants",
        choices=ImagePreprocessor.COMPARISON_VARIANTS,
        nargs="*",
        help="비교 저장할 전처리 variant 목록. 생략하면 전체 variant를 저장합니다.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
