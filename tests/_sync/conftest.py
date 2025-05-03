import enum
from collections.abc import Iterator, Mapping, MutableMapping, MutableSequence
from types import EllipsisType
from typing import (
    Any,
    ClassVar,
)

import pytest
from pydantic import Field
from result import Err, Ok, Result

from messagebus.domain.model import (
    GenericCommand,
    GenericEvent,
    GenericModel,
    Message,
    Metadata,
)
from messagebus.service._sync.dependency import SyncDependency
from messagebus.service._sync.eventstream import (
    SyncAbstractEventstreamTransport,
    SyncEventstreamPublisher,
)
from messagebus.service._sync.registry import SyncMessageBus
from messagebus.service._sync.repository import (
    SyncAbstractRepository,
    SyncMessageStoreAbstractRepository,
)
from messagebus.service._sync.unit_of_work import (
    SyncAbstractUnitOfWork,
    SyncUnitOfWorkTransaction,
)


class MyMetadata(Metadata):
    custom_field: str


class DummyError(enum.Enum):
    integrity_error = "integrity_error"
    not_found = "not_found"


class DummyModel(GenericModel[MyMetadata]):
    id: str = Field()
    counter: int = Field(0)


class Notifier(SyncDependency):
    inbox: ClassVar[list[str]] = []

    def send_message(self, message: str):
        self.inbox.append(message)

    def on_after_commit(self) -> None:
        pass

    def on_after_rollback(self) -> None:
        pass


DummyRepositoryOperationResult = Result[EllipsisType, DummyError]
DummyRepositoryResult = Result[DummyModel, DummyError]


class SyncDummyRepository(SyncAbstractRepository[DummyModel]):
    models: MutableMapping[str, DummyModel]

    def __init__(self) -> None:
        self.seen = []
        self.models = {}

    def add(self, model: DummyModel) -> DummyRepositoryOperationResult:
        if model.id in self.models:
            return Err(DummyError.integrity_error)
        self.models[model.id] = model
        self.seen.append(model)
        return Ok(...)

    def get(self, id: str) -> DummyRepositoryResult:
        try:
            return Ok(self.models[id])
        except KeyError:
            return Err(DummyError.not_found)

    def find(self, id: str | None = None) -> Iterator[DummyModel]:
        for model in self.models.values():
            if id is not None and id != model.id:
                continue
            yield model


class SyncFooRepository(SyncDummyRepository): ...


Repositories = SyncDummyRepository | SyncFooRepository


class SyncEventstreamTransport(SyncAbstractEventstreamTransport):
    events: MutableSequence[Mapping[str, Any]]

    def __init__(self):
        self.events = []

    def send_message_serialized(self, message: Mapping[str, Any]) -> None:
        self.events.append(message)


class SyncDummyMessageStore(SyncMessageStoreAbstractRepository):
    messages: MutableSequence[Message[MyMetadata]]

    def __init__(self, publisher: SyncEventstreamPublisher | None):
        super().__init__(publisher=publisher)
        self.messages = []

    def _add(self, message: Message[MyMetadata]) -> None:
        self.messages.append(message)


class SyncDummyUnitOfWork(SyncAbstractUnitOfWork[Repositories, SyncDummyMessageStore]):
    def __init__(self) -> None:
        super().__init__()
        self.status = "init"
        self.foos = SyncFooRepository()
        self.bars = SyncDummyRepository()

    def commit(self) -> None:
        self.status = "committed"

    def rollback(self) -> None:
        self.status = "aborted"


class SyncDummyUnitOfWorkWithEvents(
    SyncAbstractUnitOfWork[Repositories, SyncDummyMessageStore]
):
    def __init__(self, publisher: SyncEventstreamPublisher | None) -> None:
        self.foos = SyncFooRepository()
        self.bars = SyncDummyRepository()
        self.messagestore = SyncDummyMessageStore(publisher=publisher)

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class DummyCommand(GenericCommand[MyMetadata]):
    id: str = Field(...)
    metadata: MyMetadata = MyMetadata(
        name="dummy", schema_version=1, custom_field="foo"
    )


class AnotherDummyCommand(GenericCommand[MyMetadata]):
    id: str = Field(...)
    metadata: MyMetadata = MyMetadata(name="dummy2", schema_version=1, custom_field="f")


class DummyEvent(GenericEvent[MyMetadata]):
    id: str = Field(...)
    increment: int = Field(...)
    metadata: MyMetadata = MyMetadata(
        name="dummied", schema_version=1, published=True, custom_field="foo"
    )


@pytest.fixture
def foo_factory() -> type[DummyModel]:
    return DummyModel


@pytest.fixture
def uow() -> Iterator[SyncDummyUnitOfWork]:
    uow = SyncDummyUnitOfWork()
    yield uow
    uow.foos.models.clear()
    uow.foos.seen.clear()
    uow.bars.models.clear()
    uow.bars.seen.clear()


@pytest.fixture
def tuow(
    uow: SyncDummyUnitOfWork,
) -> Iterator[SyncUnitOfWorkTransaction[Repositories, SyncDummyMessageStore]]:
    with uow as tuow:
        yield tuow
        tuow.rollback()


@pytest.fixture
def eventstream_transport() -> SyncEventstreamTransport:
    return SyncEventstreamTransport()


@pytest.fixture
def eventstream_pub(
    eventstream_transport: SyncEventstreamTransport,
) -> SyncEventstreamPublisher:
    return SyncEventstreamPublisher(eventstream_transport)


@pytest.fixture
def messagestore(
    eventstream_pub: SyncEventstreamPublisher,
) -> SyncDummyMessageStore:
    return SyncDummyMessageStore(eventstream_pub)


@pytest.fixture
def uow_with_messagestore(
    eventstream_pub: SyncEventstreamPublisher,
) -> Iterator[SyncDummyUnitOfWorkWithEvents]:
    uow = SyncDummyUnitOfWorkWithEvents(eventstream_pub)
    yield uow
    uow.messagestore.messages.clear()  # type: ignore
    uow.foos.models.clear()
    uow.foos.seen.clear()
    uow.bars.models.clear()
    uow.bars.seen.clear()


@pytest.fixture
def notifier():
    return Notifier


@pytest.fixture
def bus(notifier: type[Notifier]) -> SyncMessageBus[Repositories]:
    return SyncMessageBus(notifier=notifier)


@pytest.fixture
def dummy_command() -> DummyCommand:
    return DummyCommand(id="dummy_cmd")


@pytest.fixture
def dummy_event() -> DummyEvent:
    return DummyEvent(id="dummy_evt", increment=1)
