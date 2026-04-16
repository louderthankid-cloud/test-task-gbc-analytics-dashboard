from pydantic import BaseModel, Field


class AddressSchema(BaseModel):
    city: str | None = "Не указан"


class DeliverySchema(BaseModel):
    address: AddressSchema | None = None


class CustomFieldsSchema(BaseModel):
    utm_source: str | None = "direct"


class OrderSchema(BaseModel):
    id: int
    totalSumm: float = 0.0
    status: str | None = "new"
    delivery: DeliverySchema | None = None
    customFields: CustomFieldsSchema | None = None
    items: list[dict] = Field(default_factory=list)
