from reading_club.domain.messages import RegisterBook
from reading_club.domain.model import Book
from reading_club.ports.repositories import BookRepositoryOperationResult

from messagebus import AsyncUnitOfWorkTransaction, async_listen


@async_listen
async def register_book(
    cmd: RegisterBook, uow: AsyncUnitOfWorkTransaction
) -> BookRepositoryOperationResult:
    book = Book(id=cmd.id, title=cmd.title, author=cmd.author, isbn=cmd.isbn)
    op = await uow.books.add(book)
    return op
