from pydantic import BaseModel, Field


class CardOcrResponse(BaseModel):
    card_number: str | None = Field(default=None, serialization_alias="cardNumber")
    expiry_ym: str | None = Field(default=None, serialization_alias="expiryYm")
    confidence: float
    warnings: list[str]

    model_config = {"populate_by_name": True}
