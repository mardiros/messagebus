from typing import Any

from messagebus.service._sync.dependency import SyncDependency
from messagebus.service._sync.registry import SyncMessageBus
from messagebus.service._sync.unit_of_work import (
    SyncAbstractUnitOfWork,
    SyncUnitOfWorkTransaction,
)
from tests._sync.conftest import (
    DummyCommand,
    DummyEvent,
    DummyModel,
    Notifier,
    Repositories,
    SyncDummyUnitOfWorkWithEvents,
    SyncEventstreamTransport,
)


def listen_command(
    cmd: DummyCommand,
    uow: SyncUnitOfWorkTransaction[Repositories],
    notifier: Notifier,
) -> DummyModel:
    """This command raise an event played by the message bus."""
    foo = DummyModel(id=cmd.id, counter=0)
    foo.messages.append(DummyEvent(id=foo.id, increment=10))
    uow.foos.add(foo)
    notifier.send_message(f"Foo {cmd.id} ordered")
    return foo


def test_store_events_and_publish(
    bus: SyncMessageBus[Repositories],
    eventstream_transport: SyncEventstreamTransport,
    uow_with_eventstore: SyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    bus.add_listener(DummyCommand, listen_command)
    with uow_with_eventstore as tuow:
        bus.handle(dummy_command, tuow)
        tuow.commit()
    assert notifier.inbox == [
        "Foo dummy_cmd ordered",
    ]


class TransientDependency(SyncDependency):
    def __init__(self) -> None:
        self.tracks: list[str] = []
        self.committed: bool | None = None

    def on_after_commit(self) -> None:
        self.committed = True

    def on_after_rollback(self) -> None:
        self.committed = False


def listen_with_transient(
    command: DummyCommand,
    uow: SyncAbstractUnitOfWork[Any],
    tracker: TransientDependency,
):
    tracker.tracks.append("tracked")


def test_transient_dependency(
    bus: SyncMessageBus[Repositories],
    eventstream_transport: SyncEventstreamTransport,
    uow_with_eventstore: SyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    tmp = TransientDependency()
    bus.add_listener(DummyCommand, listen_with_transient)
    with uow_with_eventstore as tuow:
        bus.handle(dummy_command, tuow, tracker=tmp)
        tuow.commit()
    assert tmp.tracks == ["tracked"]
    assert tmp.committed is True
