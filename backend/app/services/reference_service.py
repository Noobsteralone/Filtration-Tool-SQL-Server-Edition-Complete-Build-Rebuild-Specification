"""
Generic reference-list CRUD service (section 28/42/51).

One reusable class manages Add / Edit / Delete / Bulk Paste / Export /
Enable-Disable identically for every one of the seven reference tables --
Personal Domains, Restricted Domains, Spam Domains, Restricted Keywords,
Restricted Titles, Restricted Industries, Allowed TLDs -- since they all
share the exact same shape (ID, Value, IsActive, CreatedAt, UpdatedAt,
CreatedBy).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Type

from sqlalchemy import select
from sqlalchemy.orm import Session


class ReferenceService:
    def __init__(self, model: Type) -> None:
        self.model = model

    def list(self, db: Session, include_inactive: bool = True, search: str | None = None) -> list:
        stmt = select(self.model)
        if not include_inactive:
            stmt = stmt.where(self.model.IsActive == True)  # noqa: E712
        if search:
            stmt = stmt.where(self.model.Value.ilike(f"%{search}%"))
        stmt = stmt.order_by(self.model.Value)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, value: str, is_active: bool = True, created_by: str | None = None):
        value = value.strip()
        existing = db.execute(select(self.model).where(self.model.Value == value)).scalar_one_or_none()
        if existing:
            return existing
        item = self.model(Value=value, IsActive=is_active, CreatedAt=datetime.now(timezone.utc), CreatedBy=created_by)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def bulk_create(self, db: Session, values: list[str], created_by: str | None = None) -> int:
        """Supports pasting thousands of entries at once (section 42);
        de-duplicates against existing values, never creates unwanted
        duplicates (section 63)."""
        cleaned = {v.strip() for v in values if v and v.strip()}
        if not cleaned:
            return 0
        existing_values = {
            row.Value for row in db.execute(select(self.model.Value).where(self.model.Value.in_(cleaned))).all()
        }
        to_insert = cleaned - existing_values
        now = datetime.now(timezone.utc)
        for value in to_insert:
            db.add(self.model(Value=value, IsActive=True, CreatedAt=now, CreatedBy=created_by))
        db.commit()
        return len(to_insert)

    def update(self, db: Session, item_id: int, value: str | None = None, is_active: bool | None = None):
        item = db.get(self.model, item_id)
        if not item:
            return None
        if value is not None:
            item.Value = value.strip()
        if is_active is not None:
            item.IsActive = is_active
        item.UpdatedAt = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return item

    def delete(self, db: Session, item_id: int) -> bool:
        item = db.get(self.model, item_id)
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

    def active_values(self, db: Session) -> list[str]:
        stmt = select(self.model.Value).where(self.model.IsActive == True)  # noqa: E712
        return [row[0] for row in db.execute(stmt).all()]
