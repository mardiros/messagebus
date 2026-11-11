from reading_club.ports.repositories import AbstractBookRepository
from reading_club.ports.uow import AbstractUnitOfWork


class InMemoryBookRepository(AbstractBookRepository):
    # see chapter repository for the content of the class
    ...


class InMemoryUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.books = InMemoryBookRepository()

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
