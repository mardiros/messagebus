import asyncio
from collections.abc import Mapping
from typing import Any

from celery import Celery

from messagebus import AsyncAbstractEventstreamTransport


class EventstreamTransport(AsyncAbstractEventstreamTransport):
    """
    Transport a message to the event stream.
    """

    def __init__(self, app: Celery):
        self.celery_client = app

    async def send_message_serialized(self, message: Mapping[str, Any]) -> None:
        """Publish a serialized message to the messagestream."""
        loop = asyncio.get_event_loop()

        def send_message():
            self.celery_client.send_task("send_message", kwargs={"message": message})

        await loop.run_in_executor(None, send_message)
