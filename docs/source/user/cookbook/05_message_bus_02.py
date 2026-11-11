from lastuuid.dummies import uuidgen
from reading_club.domain.messages import RegisterBook
from reading_club.domain.model import Book
from reading_club.ports.uow import AbstractUnitOfWork

from messagebus import AsyncMessageBus


async def test_bus_handler(
    bus: AsyncMessageBus, register_book_cmd: RegisterBook, uow: AbstractUnitOfWork
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
        await transaction.commit()
