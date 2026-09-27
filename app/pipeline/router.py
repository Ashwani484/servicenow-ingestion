from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import Identity, require_roles

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/servicenow")
async def ingest_servicenow_tickets(
    assignment_group: Annotated[
        str,
        Query(min_length=3, max_length=120),
    ] = "Security DI AI India",
    identity: Identity = Depends(
        require_roles("engineer", "admin")
    ),
) -> dict:
    service = build_ingestion_service()

    result = await service.execute(
        assignment_group=assignment_group
    )

    return {
        "requested_by": identity.subject,
        "fetched": result.fetched,
        "persisted": result.persisted,
    }