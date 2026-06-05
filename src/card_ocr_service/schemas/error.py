from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    timestamp: str
    status: int
    error: str
    code: str
    reason: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    correlation_id: str | None = Field(default=None, serialization_alias="correlationId")
    path: str

    model_config = {"populate_by_name": True}
