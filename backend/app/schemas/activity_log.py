from datetime import datetime

from pydantic import BaseModel


class ActivityLogOut(BaseModel):
    LogID: int
    Username: str | None
    Action: str
    JobID: int | None
    EntityType: str | None
    EntityId: str | None
    Status: str
    Message: str | None
    CreatedAt: datetime

    model_config = {"from_attributes": True}
