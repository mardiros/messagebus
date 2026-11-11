from reading_club.adapters.uow_sqla.uow import SQLUnitOfWork
from reading_club.domain.model import Book
from reading_club.ports.repositories import BookRepositoryError


async def test_book_by_id_ok(uow: SQLUnitOfWork, book: Book):
    # Add a book in the repository
    async with uow as transaction:
        res = await uow.books.add(book)
        assert res.is_ok()
        await transaction.commit()
    uow.books.seen.clear()

    # Now, tests that the book is here
    async with uow as transaction:
        res = await uow.books.by_id(book.id)
        assert res.is_ok()
        book_from_uow = res.unwrap()
        await transaction.rollback()

    assert book_from_uow == book


async def test_book_by_id_err(uow: SQLUnitOfWork, book: Book):
    # Now, tests that the book is here
    async with uow as transaction:
        res = await uow.books.by_id(book.id)
        assert res.is_err()
        err = res.unwrap_err()
        await transaction.rollback()

    assert err == BookRepositoryError.not_found
