from typing import Any

import pytest

from messagebus.service._sync.dependency import MissingDependencyError, SyncDependency
from messagebus.service._sync.registry import SyncMessageBus
from messagebus.service._sync.unit_of_work import (
    SyncAbstractUnitOfWork,
    SyncUnitOfWorkTransaction,
)
from tests._sync.conftest import (
    DummyModel,
    Notifier,
    Repositories,
    SyncDummyMessageStore,
    SyncDummyUnitOfWorkWithEvents,
    SyncEventstreamTransport,
)
from tests.conftest import DummyCommand, DummyEvent


def listen_command(
    cmd: DummyCommand,
    uow: SyncUnitOfWorkTransaction[Repositories, SyncDummyMessageStore],
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
    uow_with_messagestore: SyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    bus.add_listener(DummyCommand, listen_command)
    with uow_with_messagestore as tuow:
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
    uow: SyncAbstractUnitOfWork[Any, Any],
    tracker: TransientDependency,
):
    tracker.tracks.append("tracked")


def test_transient_dependency(
    bus: SyncMessageBus[Repositories],
    eventstream_transport: SyncEventstreamTransport,
    uow_with_messagestore: SyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    tmp = TransientDependency()
    bus.add_listener(DummyCommand, listen_with_transient)
    with uow_with_messagestore as tuow:
        bus.handle(dummy_command, tuow, tracker=tmp)
        tuow.commit()
    assert tmp.tracks == ["tracked"]
    assert tmp.committed is True


def test_transient_dependency_missing(
    bus: SyncMessageBus[Repositories],
    eventstream_transport: SyncEventstreamTransport,
    uow_with_messagestore: SyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    bus.add_listener(DummyCommand, listen_with_transient)
    with pytest.raises(MissingDependencyError) as ctx:
        with uow_with_messagestore as tuow:
            bus.handle(dummy_command, tuow)
            tuow.commit()
    assert str(ctx.value) == "Missing messagebus dependency 'tracker'"


def listen_with_optional(
    command: DummyCommand,
    uow: SyncAbstractUnitOfWork[Any, Any],
    tracker: TransientDependency | None = None,
):
    if tracker:
        tracker.tracks.append("optionnaly_tracked")


def test_optional_dependency(
    bus: SyncMessageBus[Repositories],
    eventstream_transport: SyncEventstreamTransport,
    uow_with_messagestore: SyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    tmp = TransientDependency()
    bus.add_listener(DummyCommand, listen_with_optional)
    with uow_with_messagestore as tuow:
        bus.handle(dummy_command, tuow, tracker=tmp)
        tuow.commit()
    assert tmp.tracks == ["optionnaly_tracked"]
    assert tmp.committed is True


def test_optional_dependency_missing(
    bus: SyncMessageBus[Repositories],
    eventstream_transport: SyncEventstreamTransport,
    uow_with_messagestore: SyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    bus.add_listener(DummyCommand, listen_with_optional)
    with uow_with_messagestore as tuow:
        bus.handle(dummy_command, tuow)
        tuow.commit()
    # we tests that there is no issue here
