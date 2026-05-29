from fastapi import FastAPI

from card_ocr_service.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="card-ocr-service", version="0.1.0")
    app.include_router(router)
    return app


app = create_app()
