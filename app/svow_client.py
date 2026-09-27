
import httpx
import asyncio

class ServiceNowClient:
    def __init__(self, user, password):
        self.client = httpx.AsyncClient(auth=(user, password), timeout=10.0)