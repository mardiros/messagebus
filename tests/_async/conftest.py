import enum
import time
from collections.abc import (
    AsyncIterator,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
)
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
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
    GenericModel,
    Message,
    Metadata,
    TransactionStatus,
)
from messagebus.infrastructure.observability.metrics import (
    AbstractMetricsStore,
)
from messagebus.service._async.dependency import AsyncDependency
from messagebus.service._async.eventstream import (
    AsyncAbstractEventstreamTransport,
    AsyncEventstreamPublisher,
)
from messagebus.service._async.registry import AsyncMessageBus
from messagebus.service._async.repository import (
    AsyncAbstractMessageStoreRepository,
    AsyncAbstractRepository,
)
from messagebus.service._async.unit_of_work import (
    AsyncAbstractUnitOfWork,
    AsyncUnitOfWorkTransaction,
)
from tests.conftest import MyMetadata


@dataclass
class DummyMetricsStore(AbstractMetricsStore):
    beginned_transaction_count: int = 0
    transaction_failed_count: int = 0
    transaction_commit_count: int = 0
    transaction_rollback_count: int = 0
    processed_count: dict[tuple[str, int], int] = field(default_factory=dict)
    processing_time: float = 0

    def inc_beginned_transaction_count(self):
        self.beginned_transaction_count += 1

    def inc_transaction_failed(self):
        self.transaction_failed_count += 1

    def inc_transaction_closed_count(self, status: TransactionStatus):
        match status:
            case TransactionStatus.committed:
                self.transaction_commit_count += 1
            case TransactionStatus.rolledback:
                self.transaction_rollback_count += 1
            case _:
                assert True, f"Should nevver report {status}"

    def inc_messages_processed_total(self, msg_metadata: Metadata):
        if (msg_metadata.name, msg_metadata.schema_version) in self.processed_count:
            self.processed_count[(msg_metadata.name, msg_metadata.schema_version)] += 1
        else:
            self.processed_count[(msg_metadata.name, msg_metadata.schema_version)] = 1

    def dump(self) -> dict[str, int]:
        return asdict(self)

    @contextmanager
    def command_processing_timer(self, command: GenericCommand[Any]) -> Iterator[None]:
        start_time = time.time()
        yield
        self.processing_time = time.time() - start_time


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

    async def on_after_commit(self) -> None:
        pass

    async def on_after_rollback(self) -> None:
        pass


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

    async def find(self, id: str | None = None) -> AsyncIterator[DummyModel]:
        for model in self.models.values():
            if id is not None and id != model.id:
                continue
            yield model


class AsyncFooRepository(AsyncDummyRepository): ...


Repositories = AsyncDummyRepository | AsyncFooRepository


class AsyncEventstreamTransport(AsyncAbstractEventstreamTransport):
    events: MutableSequence[Mapping[str, Any]]

    def __init__(self):
        self.events = []

    async def send_message_serialized(self, message: Mapping[str, Any]) -> None:
        self.events.append(message)


class AsyncDummyMessageStore(AsyncAbstractMessageStoreRepository):
    messages: MutableSequence[Message[MyMetadata]]

    def __init__(self, publisher: AsyncEventstreamPublisher | None):
        super().__init__(publisher=publisher)
        self.messages = []

    async def _add(self, message: Message[MyMetadata]) -> None:
        self.messages.append(message)


class AsyncDummyUnitOfWork(
    AsyncAbstractUnitOfWork[Repositories, AsyncDummyMessageStore, DummyMetricsStore]
):
    def __init__(self) -> None:
        super().__init__()
        self.status = "init"
        self.metrics_store = DummyMetricsStore()
        self.foos = AsyncFooRepository()
        self.bars = AsyncDummyRepository()

    async def commit(self) -> None:
        self.status = "committed"

    async def rollback(self) -> None:
        self.status = "aborted"


class AsyncDummyUnitOfWorkWithEvents(
    AsyncAbstractUnitOfWork[Repositories, AsyncDummyMessageStore, DummyMetricsStore]
):
    def __init__(self, publisher: AsyncEventstreamPublisher | None) -> None:
        self.foos = AsyncFooRepository()
        self.bars = AsyncDummyRepository()
        self.messagestore = AsyncDummyMessageStore(publisher=publisher)
        self.metrics_store = DummyMetricsStore()

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


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
) -> AsyncIterator[
    AsyncUnitOfWorkTransaction[Repositories, AsyncDummyMessageStore, DummyMetricsStore]
]:
    async with uow as tuow:
        yield tuow
        await tuow.rollback()


@pytest.fixture
async def metrics(uow: AsyncDummyUnitOfWork) -> AbstractMetricsStore:
    return uow.metrics_store


@pytest.fixture
async def eventstream_transport() -> AsyncEventstreamTransport:
    return AsyncEventstreamTransport()


@pytest.fixture
async def eventstream_pub(
    eventstream_transport: AsyncEventstreamTransport,
) -> AsyncEventstreamPublisher:
    return AsyncEventstreamPublisher(eventstream_transport)


@pytest.fixture
async def messagestore(
    eventstream_pub: AsyncEventstreamPublisher,
) -> AsyncDummyMessageStore:
    return AsyncDummyMessageStore(eventstream_pub)


@pytest.fixture
async def uow_with_messagestore(
    eventstream_pub: AsyncEventstreamPublisher,
) -> AsyncIterator[AsyncDummyUnitOfWorkWithEvents]:
    uow = AsyncDummyUnitOfWorkWithEvents(eventstream_pub)
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
def bus(notifier: type[Notifier]) -> AsyncMessageBus[Repositories]:
    return AsyncMessageBus(notifier=notifier)
