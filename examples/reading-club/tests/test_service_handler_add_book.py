from collections.abc import Mapping
from typing import Any

import pytest
from lastuuid.dummies import uuidgen
from reading_club.domain.messages import BookRegistered, RegisterBook
from reading_club.domain.model import Book
from reading_club.service.handlers.book import register_book
from reading_club.service.repositories import BookRepositoryError
from reading_club.service.uow import AbstractUnitOfWork
from result import Err, Ok

from messagebus import AsyncMessageBus
from tests.conftest import EventstreamTransport


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            {
                "expected_result": Ok(...),
                "expected_book": Ok(
                    Book(
                        id=uuidgen(1),
                        title="Domain Driven Design",
                        author="Eric Evans",
                        isbn="0-321-12521-5",
                    )
                ),
                "expected_messages": [
                    BookRegistered(
                        id=uuidgen(1),
                        isbn="0-321-12521-5",
                        title="Domain Driven Design",
                        author="Eric Evans",
                    )
                ],
            },
            id="ok",
        ),
        pytest.param(
            {
                "commands": [
                    RegisterBook(
                        id=uuidgen(1),
                        title="Architecture Patterns With Python",
                        author="Harry Percival and Bob Gregory",
                        isbn="978-1492052203",
                    )
                ],
                "expected_result": Err(BookRepositoryError.integrity_error),
                "expected_book": Ok(
                    Book(
                        id=uuidgen(1),
                        title="Architecture Patterns With Python",
                        author="Harry Percival and Bob Gregory",
                        isbn="978-1492052203",
                    )
                ),
                "expected_messages": [],
            },
            id="integrity error",
        ),
    ],
)
async def test_register_book(
    params: Mapping[str, Any],
    register_book_cmd: RegisterBook,
    uow_with_data: AbstractUnitOfWork,
):
    uow = uow_with_data
    async with uow as transaction:
        operation = await register_book(register_book_cmd, transaction)
        assert operation is not None
        res = await uow.books.by_id(register_book_cmd.id)
        if operation.is_ok():
            await transaction.commit()
        else:
            await transaction.rollback()

    assert operation == params["expected_result"]
    if res.is_ok():
        assert res.unwrap().messages == params["expected_messages"]


async def test_bus_handler(
    bus: AsyncMessageBus,
    register_book_cmd: RegisterBook,
    uow: AbstractUnitOfWork,
    transport: EventstreamTransport,
):
    async with uow as transaction:
        await bus.handle(register_book_cmd, transaction)
        book = await transaction.books.by_id(register_book_cmd.id)
        assert book.is_ok()
        assert book.unwrap() == Book(
            id=uuidgen(1),
            title="Domain Driven Design",
            author="Eric Evans",
            isbn="0-321-12521-5",
        )
        assert book.unwrap().messages == []
        await transaction.commit()

    assert uow.messagestore.messages == [  # type: ignore
        RegisterBook(
            id=uuidgen(1),
            isbn="0-321-12521-5",
            title="Domain Driven Design",
            author="Eric Evans",
        ),
        BookRegistered(
            id=uuidgen(1),
            isbn="0-321-12521-5",
            title="Domain Driven Design",
            author="Eric Evans",
        ),
    ]
    assert transport.events == [
        {
            "id": transport.events[0]["id"],
            "created_at": transport.events[0]["created_at"],
            "payload": f'{{"id":"{uuidgen(1)}","isbn":"0-321-12521-5",'
            '"title":"Domain Driven '
            'Design","author":"Eric Evans"}',
            "type": "book_registered_v1",
        },
    ]
