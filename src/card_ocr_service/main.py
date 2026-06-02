from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from card_ocr_service.api.routes import ocr_service, router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    ocr_service.preload()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="card-ocr-service", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
