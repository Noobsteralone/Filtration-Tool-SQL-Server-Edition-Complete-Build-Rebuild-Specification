from datetime import datetime

from pydantic import BaseModel


class MasterEmailOut(BaseModel):
    MasterID: int
    Email: str
    Name: str | None
    Title: str | None
    Company: str | None
    Industry: str | None
    Country: str | None
    LinkedIn: str | None
    SourceFile: str | None
    SourceJobID: int | None
    CreatedAt: datetime

    model_config = {"from_attributes": True}


class OtherTLDMasterOut(BaseModel):
    OtherTLDID: int
    Email: str
    TLD: str | None
    Name: str | None
    Title: str | None
    Company: str | None
    Industry: str | None
    Country: str | None
    LinkedIn: str | None
    SourceFile: str | None
    SourceJobID: int | None
    CreatedAt: datetime

    model_config = {"from_attributes": True}


class MasterFileOut(BaseModel):
    MasterFileID: int
    FileName: str
    SourceJobID: int | None
    TargetTable: str
    RowsAdded: int
    RowsDuplicate: int
    CreatedAt: datetime
    IsDeleted: bool

    model_config = {"from_attributes": True}


class MasterMergeRequest(BaseModel):
    job_id: int
