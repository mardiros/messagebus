from typing import Any

import pytest

from messagebus.service._async.dependency import AsyncDependency, MissingDependencyError
from messagebus.service._async.registry import AsyncMessageBus
from messagebus.service._async.unit_of_work import (
    AsyncAbstractUnitOfWork,
    AsyncUnitOfWorkTransaction,
)
from tests._async.conftest import (
    AsyncDummyUnitOfWorkWithEvents,
    AsyncEventstreamTransport,
    DummyCommand,
    DummyEvent,
    DummyModel,
    Notifier,
    Repositories,
)


async def listen_command(
    cmd: DummyCommand,
    uow: AsyncUnitOfWorkTransaction[Repositories],
    notifier: Notifier,
) -> DummyModel:
    """This command raise an event played by the message bus."""
    foo = DummyModel(id=cmd.id, counter=0)
    foo.messages.append(DummyEvent(id=foo.id, increment=10))
    await uow.foos.add(foo)
    notifier.send_message(f"Foo {cmd.id} ordered")
    return foo


async def test_store_events_and_publish(
    bus: AsyncMessageBus[Repositories],
    eventstream_transport: AsyncEventstreamTransport,
    uow_with_eventstore: AsyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    bus.add_listener(DummyCommand, listen_command)
    async with uow_with_eventstore as tuow:
        await bus.handle(dummy_command, tuow)
        await tuow.commit()
    assert notifier.inbox == [
        "Foo dummy_cmd ordered",
    ]


class TransientDependency(AsyncDependency):
    def __init__(self) -> None:
        self.tracks: list[str] = []
        self.committed: bool | None = None

    async def on_after_commit(self) -> None:
        self.committed = True

    async def on_after_rollback(self) -> None:
        self.committed = False


async def listen_with_transient(
    command: DummyCommand,
    uow: AsyncAbstractUnitOfWork[Any],
    tracker: TransientDependency,
):
    tracker.tracks.append("tracked")


async def test_transient_dependency(
    bus: AsyncMessageBus[Repositories],
    eventstream_transport: AsyncEventstreamTransport,
    uow_with_eventstore: AsyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    tmp = TransientDependency()
    bus.add_listener(DummyCommand, listen_with_transient)
    async with uow_with_eventstore as tuow:
        await bus.handle(dummy_command, tuow, tracker=tmp)
        await tuow.commit()
    assert tmp.tracks == ["tracked"]
    assert tmp.committed is True


async def test_transient_dependency_missing(
    bus: AsyncMessageBus[Repositories],
    eventstream_transport: AsyncEventstreamTransport,
    uow_with_eventstore: AsyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    bus.add_listener(DummyCommand, listen_with_transient)
    with pytest.raises(MissingDependencyError) as ctx:
        async with uow_with_eventstore as tuow:
            await bus.handle(dummy_command, tuow)
            await tuow.commit()
    assert str(ctx.value) == "Missing messagebus dependency 'tracker'"


async def listen_with_optional(
    command: DummyCommand,
    uow: AsyncAbstractUnitOfWork[Any],
    tracker: TransientDependency | None = None,
):
    if tracker:
        tracker.tracks.append("optionnaly_tracked")


async def test_optional_dependency(
    bus: AsyncMessageBus[Repositories],
    eventstream_transport: AsyncEventstreamTransport,
    uow_with_eventstore: AsyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    tmp = TransientDependency()
    bus.add_listener(DummyCommand, listen_with_optional)
    async with uow_with_eventstore as tuow:
        await bus.handle(dummy_command, tuow, tracker=tmp)
        await tuow.commit()
    assert tmp.tracks == ["optionnaly_tracked"]
    assert tmp.committed is True


async def test_optional_dependency_missing(
    bus: AsyncMessageBus[Repositories],
    eventstream_transport: AsyncEventstreamTransport,
    uow_with_eventstore: AsyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
    notifier: Notifier,
):
    bus.add_listener(DummyCommand, listen_with_optional)
    async with uow_with_eventstore as tuow:
        await bus.handle(dummy_command, tuow)
        await tuow.commit()
    # we tests that there is no issue here
