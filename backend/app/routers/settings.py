from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.settings import SettingOut, SettingUpdateRequest
from app.services import settings_service
from app.services.activity_log_service import log_activity
from app.services.auth_service import require_admin

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=list[SettingOut])
def get_settings_list(db: Session = Depends(get_db)):
    return settings_service.get_all(db)


@router.put("/{key}", response_model=SettingOut)
def update_setting(key: str, payload: SettingUpdateRequest, db: Session = Depends(get_db), user=Depends(require_admin)):
    setting = settings_service.set_value(db, key, payload.value, updated_by=user.Username)
    log_activity(db, "SETTINGS_CHANGE", user=user, entity_type="Setting", entity_id=key, message=payload.value)
    return setting
