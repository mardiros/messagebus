from lastuuid.dummies import uuidgen
from reading_club.domain.messages import RegisterBook
from reading_club.domain.model import Book
from reading_club.ports.repositories import BookRepositoryError
from reading_club.ports.uow import AbstractUnitOfWork
from reading_club.service_handlers.book import register_book


async def test_register_book(register_book_cmd: RegisterBook, uow: AbstractUnitOfWork):
    async with uow as transaction:
        operation = await register_book(register_book_cmd, transaction)
        assert operation.is_ok()
        book = await transaction.books.by_id(register_book_cmd.id)
        assert book.is_ok()
        assert book.unwrap() == Book(
            id=uuidgen(2),
            title="Domain Driven Design",
            author="Eric Evans",
            isbn="0-321-12521-5",
        )
        await transaction.commit()

    async with uow as transaction:
        operation = await register_book(register_book_cmd, transaction)
        assert operation.is_err()
        assert operation.unwrap_err() == BookRepositoryError.integrity_error
        await transaction.rollback()
