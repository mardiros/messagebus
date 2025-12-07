from lastuuid.dummies import uuidgen
from reading_club.domain.messages import BookRegistered, RegisterBook
from reading_club.domain.model import Book
from reading_club.service.uow import AbstractUnitOfWork
from tests.conftest import EventstreamTransport

from messagebus import AsyncMessageBus


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
            "payload": f'{{"id": "{uuidgen(1)}", "isbn": "0-321-12521-5", '
            '"title": "Domain Driven '
            'Design", "author": "Eric Evans"}',
            "type": "register_book_v1",
        },
    ]
