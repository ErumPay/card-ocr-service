class ImagePreprocessor:
    def validate(self, image_bytes: bytes) -> None:
        if not image_bytes:
            raise ValueError("image file is empty")

