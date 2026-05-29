# card-ocr-service

Card OCR service for ErumPay.

## Run

```powershell
pixi run dev
```

## API

```text
GET  /actuator/health
POST /api/v1/cards/ocr
```

This service only extracts OCR candidates. Card registration remains in `card-service`.

