from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.tickets.schemas import (
    ServiceNowTicket,
    TicketPage,
    TicketSeverity,
    TicketState,
)

router = APIRouter(prefix="/mock-servicenow", tags=["Dummy ServiceNow"])

CONNECTOR_TOKEN = "local-connector-token"

TICKETS = [
    ServiceNowTicket(
        sys_id=UUID("11111111-1111-1111-1111-111111111111"),
        number="RITM0000001",
        category="AD User Management",
        creation_date=datetime.now(UTC),
        state=TicketState.APPROVED,
        severity=TicketSeverity.LOW,
        assignment_group="Security DI AI India",
        opened_by="customer@example.com",
        short_description="Create an AD user",
        full_description="Create a standard employee AD account.",
        updated_at=datetime.now(UTC),
    )
]


async def verify_connector_token(
    authorization: str | None = Header(default=None),
) -> None:
    expected = f"Bearer {CONNECTOR_TOKEN}"

    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid connector token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/api/now/table/sc_req_item",
    response_model=TicketPage,
    dependencies=[Depends(verify_connector_token)],
)
async def list_tickets(
    state: TicketState | None = Query(default=None),
    assignment_group: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> TicketPage:
    results = TICKETS

    if state:
        results = [ticket for ticket in results if ticket.state == state]

    if assignment_group:
        results = [
            ticket
            for ticket in results
            if ticket.assignment_group.casefold()
            == assignment_group.casefold()
        ]

    return TicketPage(items=results[:limit])