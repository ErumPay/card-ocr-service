from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from card_ocr_service.api.routes import ocr_service, router
from card_ocr_service.exception_handler import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    ocr_service.preload()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="card-ocr-service", version="0.1.0", lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()
