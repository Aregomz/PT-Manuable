from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

RowStatus = Literal["loaded", "corrected", "rejected", "duplicate"]


class ImportRowResponse(BaseModel):
    row_number: int
    status: RowStatus
    raw_data: dict[str, Any]
    normalized_data: dict[str, Any] | None
    changes: list[str]
    reason: str | None


class ImportSummaryResponse(BaseModel):
    id: int
    filename: str
    status: str
    total_rows: int
    loaded_rows: int
    corrected_rows: int
    rejected_rows: int
    duplicate_rows: int
    created_at: datetime
    already_imported: bool
    rows: list[ImportRowResponse]
