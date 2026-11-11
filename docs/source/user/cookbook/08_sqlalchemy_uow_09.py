from uuid import UUID

from reading_club.domain.model import Book
from reading_club.ports.repositories import (
    AbstractBookRepository,
    BookRepositoryError,
    BookRepositoryOperationResult,
    BookRepositoryResult,
)
from result import Err, Ok
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from . import orm


class SQLBookRepository(AbstractBookRepository):
    def __init__(self, session: AsyncSession):
        super().__init__()
        self.session = session

    async def add(self, model: Book) -> BookRepositoryOperationResult:
        qry = insert(orm.books).values([model.model_dump(exclude={"messages"})])
        try:
            await self.session.execute(qry)
        except IntegrityError:
            return Err(BookRepositoryError.integrity_error)

        self.seen.append(model)
        return Ok(...)

    async def by_id(self, id: UUID) -> BookRepositoryResult:
        qry = select(orm.books).where(orm.books.c.id == id)
        row = (await self.session.execute(qry)).first()
        if not row:
            return Err(BookRepositoryError.not_found)
        book = Book(**row._asdict())
        return Ok(book)
