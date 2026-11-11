import abc
import enum
from types import EllipsisType

from result import Result

from messagebus import AsyncAbstractRepository
from reading_club.domain.model import Book, Review, Reviewer


class BookRepositoryError(enum.Enum):
    integrity_error = "integrity_error"
    not_found = "not_found"


class ReviewerRepositoryError(enum.Enum):
    integrity_error = "integrity_error"


class ReviewRepositoryError(enum.Enum):
    integrity_error = "integrity_error"


BookRepositoryResult = Result[Book, BookRepositoryError]
BookRepositoryOperationResult = Result[EllipsisType, BookRepositoryError]

ReviewerRepositoryOperationResult = Result[EllipsisType, ReviewerRepositoryError]
ReviewRepositoryOperationResult = Result[EllipsisType, ReviewRepositoryError]


class AbstractBookRepository(AsyncAbstractRepository[Book]):
    @abc.abstractmethod
    async def add(self, model: Book) -> BookRepositoryOperationResult: ...

    @abc.abstractmethod
    async def by_id(self, id: str) -> BookRepositoryResult: ...


class AbstractReviewerRepository(AsyncAbstractRepository[Reviewer]):
    @abc.abstractmethod
    async def add(self, model: Reviewer) -> ReviewerRepositoryOperationResult: ...


class AbstractReviewRepository(AsyncAbstractRepository[Review]):
    @abc.abstractmethod
    async def add(self, model: Review) -> ReviewRepositoryOperationResult: ...


Repositories = (
    AbstractBookRepository | AbstractReviewerRepository | AbstractReviewRepository
)
