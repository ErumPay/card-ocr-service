# card-ocr-service

Card OCR service for ErumPay.

## Run

```powershell
pixi run dev
```

## Debug Preprocessing

Put sample images under `data/`, then run:

```powershell
pixi run debug-preprocess
```

Processed JPEG files are written to `data/processed/`.

## Debug OCR Texts

Print raw PaddleOCR text output for one local image:

```powershell
pixi run debug-ocr-texts --image data/IMG_3875.HEIC
```

## API

```text
GET  /actuator/health
POST /api/v1/cards/ocr
```

This service only extracts OCR candidates. Card registration remains in `card-service`.
