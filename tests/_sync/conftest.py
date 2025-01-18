import enum
from collections.abc import Iterator, Mapping, MutableMapping, MutableSequence
from types import EllipsisType
from typing import (
    Any,
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
from messagebus.service._sync.eventstream import (
    SyncAbstractEventstreamTransport,
    SyncEventstreamPublisher,
)
from messagebus.service._sync.registry import SyncMessageBus
from messagebus.service._sync.repository import (
    SyncAbstractRepository,
    SyncEventstoreAbstractRepository,
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


class SyncFooRepository(SyncDummyRepository): ...


Repositories = SyncDummyRepository | SyncFooRepository


class SyncDummyUnitOfWork(SyncAbstractUnitOfWork[Repositories]):
    def __init__(self) -> None:
        super().__init__()
        self.status = "init"
        self.foos = SyncFooRepository()
        self.bars = SyncDummyRepository()

    def commit(self) -> None:
        self.status = "committed"

    def rollback(self) -> None:
        self.status = "aborted"


class SyncEventstreamTransport(SyncAbstractEventstreamTransport):
    events: MutableSequence[Mapping[str, Any]]

    def __init__(self):
        self.events = []

    def send_message_serialized(self, message: Mapping[str, Any]) -> None:
        self.events.append(message)


class SyncDummyEventStore(SyncEventstoreAbstractRepository):
    messages: MutableSequence[Message[MyMetadata]]

    def __init__(self, publisher: SyncEventstreamPublisher | None):
        super().__init__(publisher=publisher)
        self.messages = []

    def _add(self, message: Message[MyMetadata]) -> None:
        self.messages.append(message)


class SyncDummyUnitOfWorkWithEvents(SyncAbstractUnitOfWork[Repositories]):
    def __init__(self, publisher: SyncEventstreamPublisher | None) -> None:
        self.foos = SyncFooRepository()
        self.bars = SyncDummyRepository()
        self.eventstore = SyncDummyEventStore(publisher=publisher)

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class DummyCommand(GenericCommand[MyMetadata]):
    id: str = Field(...)
    metadata: MyMetadata = MyMetadata(
        name="dummy", schema_version=1, custom_field="foo"
    )


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
) -> Iterator[SyncUnitOfWorkTransaction[Repositories]]:
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
def eventstore(
    eventstream_pub: SyncEventstreamPublisher,
) -> SyncDummyEventStore:
    return SyncDummyEventStore(eventstream_pub)


@pytest.fixture
def uow_with_eventstore(
    eventstream_pub: SyncEventstreamPublisher,
) -> Iterator[SyncDummyUnitOfWorkWithEvents]:
    uow = SyncDummyUnitOfWorkWithEvents(eventstream_pub)
    yield uow
    uow.eventstore.messages.clear()  # type: ignore
    uow.foos.models.clear()
    uow.foos.seen.clear()
    uow.bars.models.clear()
    uow.bars.seen.clear()


@pytest.fixture
def bus() -> SyncMessageBus[Repositories]:
    return SyncMessageBus()


@pytest.fixture
def dummy_command() -> DummyCommand:
    return DummyCommand(id="dummy_cmd")


@pytest.fixture
def dummy_event() -> DummyEvent:
    return DummyEvent(id="dummy_evt", increment=1)
