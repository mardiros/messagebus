from messagebus.service._async.registry import AsyncMessageBus
from messagebus.service._async.unit_of_work import AsyncUnitOfWorkTransaction
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
