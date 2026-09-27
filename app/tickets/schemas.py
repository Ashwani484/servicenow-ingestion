from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TicketState(StrEnum):
    NEW = "new"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class TicketSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceNowTicket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sys_id: UUID
    number: str = Field(pattern=r"^RITM\d{7}$")
    category: str
    creation_date: datetime
    state: TicketState
    severity: TicketSeverity
    assignment_group: str
    opened_by: str
    short_description: str = Field(min_length=3, max_length=160)
    full_description: str = Field(min_length=3, max_length=4000)
    work_notes: str = ""
    updated_at: datetime


class TicketPage(BaseModel):
    items: list[ServiceNowTicket]
    next_cursor: str | None = None