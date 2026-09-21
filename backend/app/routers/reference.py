"""
Reference Lists endpoints (sections 28, 42, 51, 56). A single factory
function builds an identical set of REST routes for each of the seven
reference tables, so Add/Edit/Delete/Bulk-Paste/Export/Enable-Disable
behaviour is guaranteed identical across all of them.
"""
from __future__ import annotations

import csv
import io
from typing import Type

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reference import (
    AllowedTLD,
    PersonalEmailDomain,
    RestrictedDomain,
    RestrictedIndustry,
    RestrictedKeyword,
    RestrictedTitle,
    SpamDomain,
)
from app.schemas.reference import BulkPasteRequest, ReferenceItemCreate, ReferenceItemOut, ReferenceItemUpdate
from app.services.activity_log_service import log_activity
from app.services.auth_service import require_admin
from app.services.reference_service import ReferenceService

router = APIRouter(prefix="/api/reference", tags=["reference"])


def _build_reference_routes(path_segment: str, model: Type, display_name: str) -> None:
    service = ReferenceService(model)

    @router.get(f"/{path_segment}", response_model=list[ReferenceItemOut], name=f"list_{path_segment}")
    def list_items(search: str | None = None, include_inactive: bool = True, db: Session = Depends(get_db)):
        return service.list(db, include_inactive=include_inactive, search=search)

    @router.post(f"/{path_segment}", response_model=ReferenceItemOut, name=f"create_{path_segment}")
    def create_item(payload: ReferenceItemCreate, db: Session = Depends(get_db), user=Depends(require_admin)):
        item = service.create(db, payload.value, payload.is_active, created_by=user.Username)
        log_activity(db, "REFERENCE_LIST_CHANGE", user=user, entity_type=display_name, entity_id=item.ID)
        return item

    @router.post(f"/{path_segment}/bulk", name=f"bulk_create_{path_segment}")
    def bulk_create(payload: BulkPasteRequest, db: Session = Depends(get_db), user=Depends(require_admin)):
        count = service.bulk_create(db, payload.values, created_by=user.Username)
        log_activity(
            db, "REFERENCE_LIST_CHANGE", user=user, entity_type=display_name,
            message=f"Bulk added {count} new value(s)",
        )
        return {"added": count}

    @router.put(f"/{path_segment}/{{item_id}}", response_model=ReferenceItemOut, name=f"update_{path_segment}")
    def update_item(item_id: int, payload: ReferenceItemUpdate, db: Session = Depends(get_db), user=Depends(require_admin)):
        item = service.update(db, item_id, payload.value, payload.is_active)
        if not item:
            raise HTTPException(status_code=404, detail=f"{display_name} entry not found")
        log_activity(db, "REFERENCE_LIST_CHANGE", user=user, entity_type=display_name, entity_id=item_id)
        return item

    @router.delete(f"/{path_segment}/{{item_id}}", name=f"delete_{path_segment}")
    def delete_item(item_id: int, db: Session = Depends(get_db), user=Depends(require_admin)):
        ok = service.delete(db, item_id)
        if not ok:
            raise HTTPException(status_code=404, detail=f"{display_name} entry not found")
        log_activity(db, "REFERENCE_LIST_CHANGE", user=user, entity_type=display_name, entity_id=item_id)
        return {"deleted": True}

    @router.get(f"/{path_segment}/export", name=f"export_{path_segment}")
    def export_items(db: Session = Depends(get_db)):
        items = service.list(db)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Value", "IsActive"])
        for item in items:
            writer.writerow([item.Value, item.IsActive])
        return Response(content=buf.getvalue(), media_type="text/csv")


_REFERENCE_TABLES: list[tuple[str, Type, str]] = [
    ("personal-domains", PersonalEmailDomain, "Personal Domain"),
    ("restricted-domains", RestrictedDomain, "Restricted Domain"),
    ("spam-domains", SpamDomain, "Spam Domain"),
    ("keywords", RestrictedKeyword, "Restricted Keyword"),
    ("titles", RestrictedTitle, "Restricted Title"),
    ("industries", RestrictedIndustry, "Restricted Industry"),
    ("allowed-tlds", AllowedTLD, "Allowed TLD"),
]

for _segment, _model, _display in _REFERENCE_TABLES:
    _build_reference_routes(_segment, _model, _display)
