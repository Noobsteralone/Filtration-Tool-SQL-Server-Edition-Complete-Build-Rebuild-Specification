from pydantic import BaseModel


class SettingOut(BaseModel):
    SettingKey: str
    SettingValue: str | None

    model_config = {"from_attributes": True}


class SettingUpdateRequest(BaseModel):
    value: str
