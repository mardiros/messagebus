import pytest
from reading_club.ports.uow import AbstractUnitOfWork

from messagebus import AsyncMessageBus


@pytest.fixture
async def uow_with_data(
    uow: AbstractUnitOfWork, bus: AsyncMessageBus, params
) -> AbstractUnitOfWork:
    async with uow as transaction:
        for command in params.get("commands", []):
            await bus.handle(command, transaction)
        await transaction.commit()
    return uow
