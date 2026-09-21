from datetime import datetime

from pydantic import BaseModel


class ReferenceItemOut(BaseModel):
    ID: int
    Value: str
    IsActive: bool
    CreatedAt: datetime
    UpdatedAt: datetime | None
    CreatedBy: str | None

    model_config = {"from_attributes": True}


class ReferenceItemCreate(BaseModel):
    value: str
    is_active: bool = True


class ReferenceItemUpdate(BaseModel):
    value: str | None = None
    is_active: bool | None = None


class BulkPasteRequest(BaseModel):
    values: list[str]
