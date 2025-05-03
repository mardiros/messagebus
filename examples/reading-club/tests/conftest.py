from collections.abc import Iterator, Mapping, MutableSequence
from typing import Any, ClassVar
from uuid import UUID

import pytest
from lastuuid.dummies import uuidgen
from reading_club.domain.messages import RegisterBook
from reading_club.domain.model import Book
from reading_club.service.repositories import (
    AbstractBookRepository,
    BookRepositoryError,
    BookRepositoryOperationResult,
    BookRepositoryResult,
)
from reading_club.service.uow import AbstractUnitOfWork
from result import Err, Ok

from messagebus import (
    AsyncAbstractEventstreamTransport,
    AsyncEventstreamPublisher,
    AsyncMessageBus,
    Message,
)
from messagebus.service._async.repository import AsyncAbstractMessageStoreRepository


class InMemoryMessageStoreRepository(AsyncAbstractMessageStoreRepository):
    messages: ClassVar[MutableSequence[Message[Any]]] = []

    async def _add(self, message: Message[Any]) -> None:
        self.messages.append(message)


class EventstreamTransport(AsyncAbstractEventstreamTransport):
    """
    Transport a message to the event stream.
    """

    events: MutableSequence[Mapping[str, Any]]

    def __init__(self) -> None:
        self.events = []

    async def send_message_serialized(self, message: Mapping[str, Any]) -> None:
        """Publish a serialized message to the eventstream."""
        self.events.append(message)


class InMemoryBookRepository(AbstractBookRepository):
    books: ClassVar[dict[UUID, Book]] = {}
    ix_books_isbn: ClassVar[dict[str, UUID]] = {}

    async def add(self, model: Book) -> BookRepositoryOperationResult:
        if model.id in self.books:
            return Err(BookRepositoryError.integrity_error)
        if model.isbn in self.ix_books_isbn:
            return Err(BookRepositoryError.integrity_error)
        self.books[model.id] = model
        self.ix_books_isbn[model.isbn] = model.id
        self.seen.append(model)
        return Ok(...)

    async def by_id(self, id: UUID) -> BookRepositoryResult:
        if id not in self.books:
            return Err(BookRepositoryError.not_found)
        return Ok(self.books[id])


class InMemoryUnitOfWork(AbstractUnitOfWork):
    def __init__(self, transport: AsyncAbstractEventstreamTransport):
        self.books = InMemoryBookRepository()
        self.messagestore = InMemoryMessageStoreRepository(
            publisher=AsyncEventstreamPublisher(transport)
        )

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


@pytest.fixture
def register_book_cmd():
    return RegisterBook(
        id=uuidgen(1),
        title="Domain Driven Design",
        author="Eric Evans",
        isbn="0-321-12521-5",
    )


@pytest.fixture
def transport() -> AsyncAbstractEventstreamTransport:
    return EventstreamTransport()


@pytest.fixture
def uow(transport: AsyncAbstractEventstreamTransport) -> Iterator[InMemoryUnitOfWork]:
    uow = InMemoryUnitOfWork(transport)
    yield uow
    uow.books.books.clear()  # type: ignore
    uow.books.ix_books_isbn.clear()  # type: ignore
    uow.messagestore.messages.clear()  # type: ignore


# for performance reason, we reuse the bus here,
# the scan operation is slowing down while repeated
_bus = AsyncMessageBus()
_bus.scan("reading_club.service.handlers")


@pytest.fixture
def bus() -> AsyncMessageBus[Any]:
    return _bus


@pytest.fixture
async def uow_with_data(
    uow: AbstractUnitOfWork, bus: AsyncMessageBus, params
) -> AbstractUnitOfWork:
    async with uow as transaction:
        for command in params.get("commands", []):
            await bus.handle(command, transaction)
        await transaction.commit()
    return uow
