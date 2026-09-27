import asyncio
import random
from typing import Any

import httpx

from app.tickets.schemas import TicketPage, TicketState


class ServiceNowConnectorError(Exception):
    pass


class ServiceNowAuthenticationError(ServiceNowConnectorError):
    pass


class ServiceNowRateLimitError(ServiceNowConnectorError):
    pass


class ServiceNowConnector:
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout_seconds: float = 10,
        maximum_attempts: int = 3,
    ) -> None:
        self.maximum_attempts = maximum_attempts

        timeout = httpx.Timeout(
            connect=5,
            read=timeout_seconds,
            write=timeout_seconds,
            pool=5,
        )

        limits = httpx.Limits(
            max_connections=50,
            max_keepalive_connections=20,
        )

        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            limits=limits,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )

    async def __aenter__(self) -> "ServiceNowConnector":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_approved_tickets(
        self,
        assignment_group: str,
        limit: int = 100,
    ) -> TicketPage:
        parameters = {
            "state": TicketState.APPROVED.value,
            "assignment_group": assignment_group,
            "limit": limit,
        }

        response = await self._request(
            "GET",
            "/api/now/table/sc_req_item",
            params=parameters,
        )

        return TicketPage.model_validate(response.json())

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        for attempt in range(1, self.maximum_attempts + 1):
            try:
                response = await self._client.request(
                    method,
                    path,
                    **kwargs,
                )

                if response.status_code in {401, 403}:
                    raise ServiceNowAuthenticationError(
                        "ServiceNow authentication failed"
                    )

                if response.status_code == 429:
                    if attempt == self.maximum_attempts:
                        raise ServiceNowRateLimitError(
                            "ServiceNow rate limit exceeded"
                        )
                    await self._sleep(attempt)
                    continue

                if response.status_code in self.RETRYABLE_STATUS_CODES:
                    if attempt == self.maximum_attempts:
                        response.raise_for_status()
                    await self._sleep(attempt)
                    continue

                response.raise_for_status()
                return response

            except (
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
            ) as exc:
                if attempt == self.maximum_attempts:
                    raise ServiceNowConnectorError(
                        "ServiceNow is unavailable"
                    ) from exc

                await self._sleep(attempt)

        raise ServiceNowConnectorError("Connector retry loop exhausted")

    @staticmethod
    async def _sleep(attempt: int) -> None:
        delay = min(2 ** (attempt - 1), 8)
        jitter = random.uniform(0, 0.5)
        await asyncio.sleep(delay + jitter)