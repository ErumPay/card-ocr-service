# card-ocr-service

ErumPay 카드 OCR 전용 서비스입니다.

카드 이미지에서 카드번호와 유효기간 후보를 추출해 프론트에 반환합니다. 카드 등록, 카드 상품 검증, billing-key 발급은 이 서비스의 책임이 아니며, OCR 결과를 사용자가 확인/수정한 뒤 `card-service`의 카드 등록 API로 전달하는 흐름을 기준으로 합니다.

## 실행

로컬 개발 서버:

```powershell
pixi run dev
```

운영/컨테이너용 실행:

```powershell
pixi run start
```

기본 포트는 `8086`입니다.

## Docker

이미지 빌드:

```powershell
docker build -t card-ocr-service:local .
```

인프라 compose에서 실행:

```powershell
cd C:\Users\zzang\Desktop\workspace\VScode\erumpay\erumpay-infra
docker compose up -d --build card-ocr-service
```

상태 확인:

```powershell
curl http://localhost:8086/actuator/health
```

## API

### Health Check

```http
GET /actuator/health
```

응답:

```json
{
  "status": "UP"
}
```

### 카드 OCR

```http
POST /api/v1/cards/ocr
Content-Type: multipart/form-data
```

요청 필드:

| 필드 | 타입 | 필수 | 설명 |
|---|---|---:|---|
| `image` | file | Y | 카드 이미지 |

지원 형식:

- `image/jpeg`, `.jpg`, `.jpeg`
- `image/png`, `.png`
- `image/heic`, `.heic`
- `image/heif`, `.heif`

응답 예시:

```json
{
  "cardNumber": "8600021234567890",
  "expiryYm": "202912",
  "confidence": 0.91,
  "warnings": []
}
```

인식 실패도 기본적으로 `200 OK`로 응답하고, 누락된 필드는 `null`로 내려갑니다.

```json
{
  "cardNumber": null,
  "expiryYm": null,
  "confidence": 0.0,
  "warnings": [
    "CARD_NUMBER_NOT_DETECTED",
    "EXPIRY_NOT_DETECTED"
  ]
}
```

## OCR 처리 흐름

현재 프론트는 카드 촬영 후 카드 프레임 기준으로 crop하고, 긴 변을 1024px 이하로 맞춘 JPEG를 전송하는 흐름을 기준으로 합니다.

서버 기본 전처리:

```text
decode
-> grayscale
-> CLAHE
-> sharpen
-> PaddleOCR 입력 직전 BGR 3채널 변환
-> PaddleOCR 실행
-> 카드번호/유효기간 후보 정규화
```

서버에서는 기본 경로에서 별도 resize를 하지 않습니다. 기본 전처리 variant는 `clahe_sharpen`입니다.

정방향 OCR 결과가 불완전하면 90도, 270도 회전 이미지를 추가로 OCR합니다. 따라서 인식이 잘 안 되는 이미지에서는 OCR 호출이 최대 3회 발생할 수 있습니다.

## 유효기간 검증

OCR로 추출한 유효기간은 `YYYYMM` 형식으로 정규화합니다.

예:

```text
12/29 -> 202912
```

아래 값은 유효기간 후보에서 제외합니다.

- 이미 만료된 월
- 현재 연도 기준 10년을 초과하는 미래 연도

예를 들어 `07/77`처럼 잘못 인식된 값은 `expiryYm: null`로 반환됩니다.

## Warning

현재 반환 가능한 warning:

| warning | 의미 |
|---|---|
| `UNSUPPORTED_IMAGE_FORMAT` | 지원하지 않는 이미지 형식 |
| `OCR_ENGINE_FAILED` | OCR 엔진 호출 실패 |
| `OCR_TEXT_NOT_DETECTED` | OCR 텍스트가 감지되지 않음 |
| `CARD_NUMBER_NOT_DETECTED` | 카드번호 후보를 찾지 못함 |
| `EXPIRY_NOT_DETECTED` | 유효기간 후보를 찾지 못함 |

## 디버그: 전처리 이미지 저장

전처리 결과를 임시로 저장하려면 환경변수를 켭니다.

```yaml
CARD_OCR_DEBUG_SAVE_PREPROCESSED: "true"
CARD_OCR_DEBUG_DIR: /app/data/debug
```

저장 파일 예시:

```text
data/debug/preprocessed-20260602T084500828378Z-8f22852a.jpg
```

로컬 저장 목록 확인:

```powershell
Get-ChildItem ..\card-ocr-service\data\debug
```

탐색기에서 열기:

```powershell
explorer ..\card-ocr-service\data\debug
```

주의: 전처리 이미지에도 카드번호가 포함될 수 있습니다. 로컬 디버그가 끝나면 `CARD_OCR_DEBUG_SAVE_PREPROCESSED`를 끄고, 저장된 파일을 삭제하세요.

## 디버그 스크립트

### 전처리 결과 저장

`data/` 아래에 샘플 이미지를 넣고 실행합니다.

```powershell
pixi run debug-preprocess
```

결과는 기본적으로 `data/processed/`에 저장됩니다.

옵션 예시:

```powershell
pixi run debug-preprocess --input-dir data --output-dir data/processed --variants clahe_sharpen
```

### PaddleOCR raw text 확인

이미지 1장의 PaddleOCR raw text와 confidence를 출력합니다.

```powershell
pixi run debug-ocr-texts --image data/sample.jpg
```

전처리 저장 파일을 넣어 확인할 수도 있습니다.

```powershell
pixi run debug-ocr-texts --image data/debug/preprocessed-20260602T084500828378Z-8f22852a.jpg
```

단, `debug-ocr-texts`는 입력 이미지를 다시 전처리한 뒤 PaddleOCR에 전달합니다. 실제 촬영 원본이 있으면 원본 이미지로 확인하는 편이 더 정확합니다.

## 테스트와 린트

```powershell
pixi run test
pixi run lint
```

## 책임 범위

이 서비스의 책임:

- 이미지 업로드 수신
- 이미지 전처리
- PaddleOCR 실행
- 카드번호 후보 추출
- 유효기간 후보 추출
- confidence와 warning 반환

이 서비스의 비책임:

- 카드 등록
- 카드 상품/BIN 검증
- billing-key 발급
- auth-service 사용자 조회
- CVC 추출
- 카드 비밀번호 처리
- 카드 원본 정보 저장

## 보안 주의사항

- 원본 카드 이미지는 저장하지 않습니다.
- OCR raw text는 기본 로그에 남기지 않습니다.
- 디버그 전처리 이미지는 로컬 확인 목적으로만 사용합니다.
- CVC와 카드 비밀번호 2자리는 OCR 대상이 아니며 사용자가 직접 입력해야 합니다.
