from typing import ClassVar
from uuid import UUID

from reading_club.domain.model import Book
from reading_club.ports.repositories import (
    AbstractBookRepository,
    BookRepositoryError,
    BookRepositoryOperationResult,
    BookRepositoryResult,
)
from result import Err, Ok


class InMemoryBookRepository(AbstractBookRepository):
    books: ClassVar[dict[UUID, Book]] = {}
    ix_books_isbn: ClassVar[dict[UUID, str]] = {}

    async def add(self, model: Book) -> BookRepositoryOperationResult:
        if model.id in self.books:
            return Err(BookRepositoryError.integrity_error)
        if model.isbn in self.ix_books_isbn:
            return Err(BookRepositoryError.integrity_error)
        self.books[model.id] = model
        self.books[model.isbn] = model.id
        return Ok(...)

    async def by_id(self, id: UUID) -> BookRepositoryResult:
        if id not in self.books:
            return Err(BookRepositoryError.not_found)
        return Ok(self.books[id])
