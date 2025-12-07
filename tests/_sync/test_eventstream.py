from collections.abc import Mapping, MutableSequence
from typing import Any

from messagebus.service._sync.eventstream import (
    SyncAbstractEventstreamTransport,
    SyncEventstreamPublisher,
)
from messagebus.service.eventstream import MessageSerializer
from tests.conftest import DummyCommand, DummyEvent


class SyncDummyEventstreamTransport(SyncAbstractEventstreamTransport):
    queue: MutableSequence[Mapping[str, Any]]

    def __init__(self) -> None:
        self.queue = []

    def send_message_serialized(self, message: Mapping[str, Any]) -> None:
        self.queue.append(message)


def test_send_message(dummy_command: DummyCommand, dummy_event: DummyEvent):
    srlz = MessageSerializer()
    transport = SyncDummyEventstreamTransport()
    stream = SyncEventstreamPublisher(transport, srlz)
    stream.send_message(dummy_command)
    stream.send_message(dummy_event)

    assert transport.queue == [srlz.serialize_message(dummy_event)]
