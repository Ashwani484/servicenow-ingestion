from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TicketRecord(Base):
    __tablename__ = "service_tickets"

    sys_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
    )
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    assignment_group: Mapped[str] = mapped_column(String(120), nullable=False)
    opened_by: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(String(160), nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)
    work_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_ticket_state_group", "state", "assignment_group"),
    )