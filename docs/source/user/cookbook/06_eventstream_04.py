from reading_club.domain.messages import BookRegistered, RegisterBook
from reading_club.domain.model import Book
from reading_club.ports.repositories import BookRepositoryOperationResult
from reading_club.ports.uow import AbstractUnitOfWork

from messagebus import async_listen


@async_listen
async def register_book(
    cmd: RegisterBook, uow: AbstractUnitOfWork
) -> BookRepositoryOperationResult:
    book = Book(id=cmd.id, title=cmd.title, author=cmd.author, isbn=cmd.isbn)
    op = await uow.books.add(book)
    book.messages.append(
        BookRegistered(id=cmd.id, title=cmd.title, author=cmd.author, isbn=cmd.isbn)
    )
    return op
