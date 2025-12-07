import enum
import time
from collections.abc import (
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
from messagebus.service._sync.dependency import SyncDependency
from messagebus.service._sync.eventstream import (
    SyncAbstractEventstreamTransport,
    SyncEventstreamPublisher,
)
from messagebus.service._sync.registry import SyncMessageBus
from messagebus.service._sync.repository import (
    SyncAbstractMessageStoreRepository,
    SyncAbstractRepository,
)
from messagebus.service._sync.unit_of_work import (
    SyncAbstractUnitOfWork,
    SyncUnitOfWorkTransaction,
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


class SyncDummyMessageStore(SyncAbstractMessageStoreRepository):
    messages: MutableSequence[Message[MyMetadata]]

    def __init__(self, publisher: SyncEventstreamPublisher | None):
        super().__init__(publisher=publisher)
        self.messages = []

    def _add(self, message: Message[MyMetadata]) -> None:
        self.messages.append(message)


class SyncDummyUnitOfWork(
    SyncAbstractUnitOfWork[Repositories, SyncDummyMessageStore, DummyMetricsStore]
):
    def __init__(self) -> None:
        super().__init__()
        self.status = "init"
        self.metrics_store = DummyMetricsStore()
        self.foos = SyncFooRepository()
        self.bars = SyncDummyRepository()

    def commit(self) -> None:
        self.status = "committed"

    def rollback(self) -> None:
        self.status = "aborted"


class SyncDummyUnitOfWorkWithEvents(SyncAbstractUnitOfWork[Any, Any, Any]):
    def __init__(self, publisher: SyncEventstreamPublisher | None) -> None:
        self.foos = SyncFooRepository()
        self.bars = SyncDummyRepository()
        self.messagestore = SyncDummyMessageStore(publisher=publisher)
        self.metrics_store = DummyMetricsStore()

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


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
) -> Iterator[SyncUnitOfWorkTransaction[SyncDummyUnitOfWork]]:
    with uow as tuow:
        yield tuow
        tuow.rollback()


@pytest.fixture
def metrics(uow: SyncDummyUnitOfWork) -> AbstractMetricsStore:
    return uow.metrics_store


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
def bus(notifier: type[Notifier]) -> SyncMessageBus[SyncDummyUnitOfWork]:
    return SyncMessageBus(notifier=notifier)
