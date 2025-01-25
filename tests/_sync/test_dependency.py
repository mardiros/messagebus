from messagebus.service._sync.registry import SyncMessageBus
from messagebus.service._sync.unit_of_work import SyncUnitOfWorkTransaction
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
