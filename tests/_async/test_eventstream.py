from collections.abc import Mapping, MutableSequence
from typing import Any

from messagebus.service._async.eventstream import (
    AsyncAbstractEventstreamTransport,
    AsyncEventstreamPublisher,
)
from messagebus.service.eventstream import MessageSerializer
from tests.conftest import DummyCommand, DummyEvent


class AsyncDummyEventstreamTransport(AsyncAbstractEventstreamTransport):
    queue: MutableSequence[Mapping[str, Any]]

    def __init__(self) -> None:
        self.queue = []

    async def send_message_serialized(self, message: Mapping[str, Any]) -> None:
        self.queue.append(message)


async def test_send_message(dummy_command: DummyCommand, dummy_event: DummyEvent):
    srlz = MessageSerializer()
    transport = AsyncDummyEventstreamTransport()
    stream = AsyncEventstreamPublisher(transport, srlz)
    await stream.send_message(dummy_command)
    await stream.send_message(dummy_event)

    assert transport.queue == [srlz.serialize_message(dummy_event)]
