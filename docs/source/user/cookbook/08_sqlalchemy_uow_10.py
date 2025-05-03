from lastuuid.dummies import uuidgen
from reading_club.adapters.uow_sqla import orm
from reading_club.adapters.uow_sqla.uow import SQLUnitOfWork
from reading_club.domain.messages import RegisterBook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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
        "id": register_book_cmd.id,
        "author": "Eric Evans",
        "isbn": "0-321-12521-5",
        "title": "Domain Driven Design",
    }
