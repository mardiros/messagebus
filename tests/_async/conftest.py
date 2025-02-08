import enum
from collections.abc import AsyncIterator, Mapping, MutableMapping, MutableSequence
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
from messagebus.service._async.dependency import AsyncDependency
from messagebus.service._async.eventstream import (
    AsyncAbstractEventstreamTransport,
    AsyncEventstreamPublisher,
)
from messagebus.service._async.registry import AsyncMessageBus
from messagebus.service._async.repository import (
    AsyncAbstractRepository,
    AsyncEventstoreAbstractRepository,
)
from messagebus.service._async.unit_of_work import (
    AsyncAbstractUnitOfWork,
    AsyncUnitOfWorkTransaction,
)


class MyMetadata(Metadata):
    custom_field: str


class DummyError(enum.Enum):
    integrity_error = "integrity_error"
    not_found = "not_found"


class DummyModel(GenericModel[MyMetadata]):
    id: str = Field()
    counter: int = Field(0)


class Notifier(AsyncDependency):
    inbox: ClassVar[list[str]] = []

    def send_message(self, message: str):
        self.inbox.append(message)


DummyRepositoryOperationResult = Result[EllipsisType, DummyError]
DummyRepositoryResult = Result[DummyModel, DummyError]


class AsyncDummyRepository(AsyncAbstractRepository[DummyModel]):
    models: MutableMapping[str, DummyModel]

    def __init__(self) -> None:
        self.seen = []
        self.models = {}

    async def add(self, model: DummyModel) -> DummyRepositoryOperationResult:
        if model.id in self.models:
            return Err(DummyError.integrity_error)
        self.models[model.id] = model
        self.seen.append(model)
        return Ok(...)

    async def get(self, id: str) -> DummyRepositoryResult:
        try:
            return Ok(self.models[id])
        except KeyError:
            return Err(DummyError.not_found)


class AsyncFooRepository(AsyncDummyRepository): ...


Repositories = AsyncDummyRepository | AsyncFooRepository


class AsyncDummyUnitOfWork(AsyncAbstractUnitOfWork[Repositories]):
    def __init__(self) -> None:
        super().__init__()
        self.status = "init"
        self.foos = AsyncFooRepository()
        self.bars = AsyncDummyRepository()

    async def commit(self) -> None:
        self.status = "committed"

    async def rollback(self) -> None:
        self.status = "aborted"


class AsyncEventstreamTransport(AsyncAbstractEventstreamTransport):
    events: MutableSequence[Mapping[str, Any]]

    def __init__(self):
        self.events = []

    async def send_message_serialized(self, message: Mapping[str, Any]) -> None:
        self.events.append(message)


class AsyncDummyEventStore(AsyncEventstoreAbstractRepository):
    messages: MutableSequence[Message[MyMetadata]]

    def __init__(self, publisher: AsyncEventstreamPublisher | None):
        super().__init__(publisher=publisher)
        self.messages = []

    async def _add(self, message: Message[MyMetadata]) -> None:
        self.messages.append(message)


class AsyncDummyUnitOfWorkWithEvents(AsyncAbstractUnitOfWork[Repositories]):
    def __init__(self, publisher: AsyncEventstreamPublisher | None) -> None:
        self.foos = AsyncFooRepository()
        self.bars = AsyncDummyRepository()
        self.eventstore = AsyncDummyEventStore(publisher=publisher)

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


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
async def uow() -> AsyncIterator[AsyncDummyUnitOfWork]:
    uow = AsyncDummyUnitOfWork()
    yield uow
    uow.foos.models.clear()
    uow.foos.seen.clear()
    uow.bars.models.clear()
    uow.bars.seen.clear()


@pytest.fixture
async def tuow(
    uow: AsyncDummyUnitOfWork,
) -> AsyncIterator[AsyncUnitOfWorkTransaction[Repositories]]:
    async with uow as tuow:
        yield tuow
        await tuow.rollback()


@pytest.fixture
async def eventstream_transport() -> AsyncEventstreamTransport:
    return AsyncEventstreamTransport()


@pytest.fixture
async def eventstream_pub(
    eventstream_transport: AsyncEventstreamTransport,
) -> AsyncEventstreamPublisher:
    return AsyncEventstreamPublisher(eventstream_transport)


@pytest.fixture
async def eventstore(
    eventstream_pub: AsyncEventstreamPublisher,
) -> AsyncDummyEventStore:
    return AsyncDummyEventStore(eventstream_pub)


@pytest.fixture
async def uow_with_eventstore(
    eventstream_pub: AsyncEventstreamPublisher,
) -> AsyncIterator[AsyncDummyUnitOfWorkWithEvents]:
    uow = AsyncDummyUnitOfWorkWithEvents(eventstream_pub)
    yield uow
    uow.eventstore.messages.clear()  # type: ignore
    uow.foos.models.clear()
    uow.foos.seen.clear()
    uow.bars.models.clear()
    uow.bars.seen.clear()


@pytest.fixture
def notifier():
    return Notifier


@pytest.fixture
def bus(notifier: type[Notifier]) -> AsyncMessageBus[Repositories]:
    return AsyncMessageBus(notifier=notifier)


@pytest.fixture
def dummy_command() -> DummyCommand:
    return DummyCommand(id="dummy_cmd")


@pytest.fixture
def dummy_event() -> DummyEvent:
    return DummyEvent(id="dummy_evt", increment=1)
