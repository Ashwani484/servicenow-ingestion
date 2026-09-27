from dataclasses import dataclass

from app.connectors.servicenow import ServiceNowConnector
from app.database.repository import TicketRepository


@dataclass(frozen=True)
class IngestionResult:
    fetched: int
    persisted: int


class TicketIngestionService:
    def __init__(
        self,
        servicenow: ServiceNowConnector,
        repository: TicketRepository,
    ) -> None:
        self.servicenow = servicenow
        self.repository = repository

    async def execute(
        self,
        assignment_group: str,
        limit: int = 100,
    ) -> IngestionResult:
        page = await self.servicenow.fetch_approved_tickets(
            assignment_group=assignment_group,
            limit=limit,
        )

        persisted = await self.repository.upsert_many(page.items)

        return IngestionResult(
            fetched=len(page.items),
            persisted=persisted,
        )