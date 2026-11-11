from reading_club.domain.messages import RegisterBook
from reading_club.ports.repositories import BookRepositoryOperationResult

from messagebus import AsyncUnitOfWorkTransaction


async def register_book(
    cmd: RegisterBook, uow: AsyncUnitOfWorkTransaction
) -> BookRepositoryOperationResult:
    raise NotImplementedError
