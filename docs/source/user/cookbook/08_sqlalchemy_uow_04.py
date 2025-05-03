from types import TracebackType

from reading_club.domain.model import Book
from reading_club.service.repositories import (
    AbstractBookRepository,
    BookRepositoryOperationResult,
    BookRepositoryResult,
)
from reading_club.service.uow import AbstractUnitOfWork
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from messagebus import (
    AsyncAbstractEventstreamTransport,
    AsyncEventstreamPublisher,
    AsyncMessageStoreAbstractRepository,
    AsyncUnitOfWorkTransaction,
    Message,
)


class SQLMessageStoreRepository(AsyncMessageStoreAbstractRepository):
    def __init__(self, session: AsyncSession, publisher: AsyncEventstreamPublisher):
        super().__init__(publisher)
        self.session = session

    async def _add(self, message: Message) -> None:
        raise NotImplementedError


class SQLBookRepository(AbstractBookRepository):
    def __init__(self, session: AsyncSession):
        super().__init__()
        self.session = session

    async def add(self, model: Book) -> BookRepositoryOperationResult:
        raise NotImplementedError

    async def by_id(self, id: str) -> BookRepositoryResult:
        raise NotImplementedError


class SQLUnitOfWork(AbstractUnitOfWork):
    session: AsyncSession

    def __init__(
        self,
        transport: AsyncAbstractEventstreamTransport,
        sqla_engine: AsyncEngine,
    ):
        super().__init__()
        self.sqla_engine = sqla_engine
        self.session_factory = async_sessionmaker(self.sqla_engine, class_=AsyncSession)
        self.transport = transport

    async def __aenter__(self) -> AsyncUnitOfWorkTransaction:
        self.messages = []
        self.session = self.session_factory()
        self.messagestore = SQLMessageStoreRepository(
            self.session,
            AsyncEventstreamPublisher(self.transport),
        )
        self.books = SQLBookRepository(self.session)
        ret = await super().__aenter__()
        return ret

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            await super().__aexit__(exc_type, exc, tb)
        finally:
            await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
