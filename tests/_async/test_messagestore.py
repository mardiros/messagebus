from messagebus.service._async.registry import AsyncMessageBus
from messagebus.service._async.unit_of_work import AsyncUnitOfWorkTransaction
from tests._async.conftest import (
    AsyncDummyMessageStore,
    AsyncDummyUnitOfWorkWithEvents,
    AsyncEventstreamTransport,
    DummyModel,
    MyMetadata,
    Repositories,
)
from tests.conftest import DummyCommand, DummyEvent


async def listen_command(
    cmd: DummyCommand,
    uow: AsyncUnitOfWorkTransaction[Repositories, AsyncDummyMessageStore],
) -> DummyModel:
    """This command raise an event played by the message bus."""
    foo = DummyModel(id=cmd.id, counter=0)
    foo.messages.append(DummyEvent(id=foo.id, increment=10))
    await uow.foos.add(foo)
    return foo


async def test_store_events_and_publish(
    bus: AsyncMessageBus[Repositories],
    eventstream_transport: AsyncEventstreamTransport,
    uow_with_messagestore: AsyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
):
    bus.add_listener(DummyCommand, listen_command)
    async with uow_with_messagestore as tuow:
        await bus.handle(dummy_command, tuow)
        await tuow.commit()

    assert uow_with_messagestore.messagestore.messages == [  # type: ignore
        DummyCommand(
            metadata=MyMetadata(
                name="dummy", schema_version=1, published=False, custom_field="foo"
            ),
            id="dummy_cmd",
        ),
        DummyEvent(
            metadata=MyMetadata(
                name="dummied", schema_version=1, published=True, custom_field="foo"
            ),
            id="dummy_cmd",
            increment=10,
        ),
    ]
    evt: DummyEvent = uow_with_messagestore.messagestore.messages[1]  # type: ignore
    assert eventstream_transport.events == [
        {
            "created_at": evt.created_at.isoformat(),
            "id": str(evt.message_id),
            "payload": '{"id":"dummy_cmd","increment":10}',
            "type": "dummied_v1",
        },
    ]


async def test_store_events_and_rollback(
    bus: AsyncMessageBus[Repositories],
    eventstream_transport: AsyncEventstreamTransport,
    uow_with_messagestore: AsyncDummyUnitOfWorkWithEvents,
    dummy_command: DummyCommand,
):
    bus.add_listener(DummyCommand, listen_command)
    async with uow_with_messagestore as tuow:
        await bus.handle(dummy_command, tuow)
        await tuow.rollback()
    assert eventstream_transport.events == []
