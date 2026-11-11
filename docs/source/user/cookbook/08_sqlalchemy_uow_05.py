from reading_club.adapters.uow_sqla import orm
from reading_club.adapters.uow_sqla.uow import SQLUnitOfWork
from reading_club.domain.model import Book
from reading_club.ports.repositories import BookRepositoryError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def test_book_add_ok(uow: SQLUnitOfWork, book: Book, sqla_session: AsyncSession):
    async with uow as transaction:
        res = await uow.books.add(book)
        await transaction.commit()

    assert res.is_ok()

    row = (
        await sqla_session.execute(select(orm.books).where(orm.books.c.id == book.id))
    ).first()
    assert row is not None
    assert row._asdict() == book.model_dump(exclude={"messages"})

    # ensure the message bus can follow the book messages
    assert uow.books.seen == [book]


async def test_book_add_err(uow: SQLUnitOfWork, book: Book):
    # Add a book in the repository
    async with uow as transaction:
        res = await uow.books.add(book)
        assert res.is_ok()
        await transaction.commit()
    uow.books.seen.clear()

    # Now, tests that it wrap the error
    async with uow as transaction:
        res = await uow.books.add(book)
        assert res.is_err()
        assert res.unwrap_err() == BookRepositoryError.integrity_error
        await transaction.rollback()

    # Since it does not work, the bus can't see the book messages.
    assert uow.books.seen == []
