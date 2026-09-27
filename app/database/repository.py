from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import TicketRecord
from app.tickets.schemas import ServiceNowTicket


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_many(
        self,
        tickets: list[ServiceNowTicket],
    ) -> int:
        if not tickets:
            return 0

        rows = [
            {
                "sys_id": ticket.sys_id,
                "number": ticket.number,
                "category": ticket.category,
                "state": ticket.state.value,
                "severity": ticket.severity.value,
                "assignment_group": ticket.assignment_group,
                "opened_by": ticket.opened_by,
                "short_description": ticket.short_description,
                "full_description": ticket.full_description,
                "work_notes": ticket.work_notes,
                "source_updated_at": ticket.updated_at,
            }
            for ticket in tickets
        ]

        statement = insert(TicketRecord).values(rows)

        statement = statement.on_conflict_do_update(
            index_elements=[TicketRecord.sys_id],
            set_={
                "state": statement.excluded.state,
                "severity": statement.excluded.severity,
                "assignment_group": statement.excluded.assignment_group,
                "short_description": statement.excluded.short_description,
                "full_description": statement.excluded.full_description,
                "work_notes": statement.excluded.work_notes,
                "source_updated_at": statement.excluded.source_updated_at,
            },
        )

        await self.session.execute(statement)
        await self.session.commit()

        return len(rows)