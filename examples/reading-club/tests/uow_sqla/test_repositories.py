from collections.abc import Mapping
from typing import Any

import pytest
from lastuuid.dummies import uuidgen
from reading_club.adapters.uow_sqla import orm
from reading_club.adapters.uow_sqla.uow import SQLUnitOfWork
from reading_club.domain.messages import RegisterBook
from reading_club.domain.model import Book
from reading_club.service.repositories import BookRepositoryError
from result import Err, Ok
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


@pytest.mark.parametrize(
    "params",
    [
        {
            "commands": [
                RegisterBook(
                    id=uuidgen(),
                    title="Domain Driven Design",
                    author="Eric Evans",
                    isbn="0-321-12521-5",
                )
            ]
        }
    ],
)
async def test_book_add_err(
    params: Mapping[str, Any], uow_with_data: SQLUnitOfWork, book: Book
):
    uow = uow_with_data
    book.id = params["commands"][0].id
    async with uow as transaction:
        res = await uow.books.add(book)
        assert res.is_err()
        assert res.unwrap_err() == BookRepositoryError.integrity_error
        await transaction.rollback()

    # Since it does not work, the bus can't see the book messages.
    assert uow.books.seen == []


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            {
                "book_id": uuidgen(1),
                "commands": [
                    RegisterBook(
                        id=uuidgen(1),
                        title="Domain Driven Design",
                        author="Eric Evans",
                        isbn="0-321-12521-5",
                    ),
                    RegisterBook(
                        id=uuidgen(2),
                        title="Architecture Patterns With Python",
                        author="Harry Percival and Bob Gregory",
                        isbn="978-1492052203",
                    ),
                ],
                "expected_result": Ok(
                    Book(
                        id=uuidgen(1),
                        title="Domain Driven Design",
                        author="Eric Evans",
                        isbn="0-321-12521-5",
                    )
                ),
            },
            id="return a known book",
        ),
        pytest.param(
            {
                "book_id": uuidgen(),
                "commands": [
                    RegisterBook(
                        id=uuidgen(),
                        title="Domain Driven Design",
                        author="Eric Evans",
                        isbn="0-321-12521-5",
                    ),
                    RegisterBook(
                        id=uuidgen(),
                        title="Architecture Patterns With Python",
                        author="Harry Percival and Bob Gregory",
                        isbn="978-1492052203",
                    ),
                ],
                "expected_result": Err(BookRepositoryError.not_found),
            },
            id="return an error",
        ),
    ],
)
async def test_book_by_id(params: Mapping[str, Any], uow_with_data: SQLUnitOfWork):
    uow = uow_with_data
    # Now, tests that the book is here
    async with uow as transaction:
        res = await uow.books.by_id(params["book_id"])
        await transaction.rollback()

    assert res == params["expected_result"]


async def test_messagestore_add(
    uow: SQLUnitOfWork, register_book_cmd: RegisterBook, sqla_session: AsyncSession
):
    register_book_cmd.id = uuidgen()
    async with uow as transaction:
        await uow.messagestore.add(register_book_cmd)
        await transaction.commit()

    row = (
        await sqla_session.execute(
            select(orm.messages).where(
                orm.messages.c.id == register_book_cmd.message_id
            )
        )
    ).first()
    assert row is not None
    assert row.id == register_book_cmd.message_id
    assert row.created_at == register_book_cmd.created_at
    assert row.metadata == register_book_cmd.metadata.model_dump()
    assert row.payload == {
        "id": str(register_book_cmd.id),
        "author": "Eric Evans",
        "isbn": "0-321-12521-5",
        "title": "Domain Driven Design",
    }
