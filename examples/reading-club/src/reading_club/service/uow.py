from typing import Any

from messagebus import AsyncAbstractUnitOfWork
from reading_club.service.repositories import (
    AbstractBookRepository,
    AbstractReviewerRepository,
    AbstractReviewRepository,
    Repositories,
)


class AbstractUnitOfWork(AsyncAbstractUnitOfWork[Repositories, Any, Any]):
    books: AbstractBookRepository
    reviewers: AbstractReviewerRepository
    reviews: AbstractReviewRepository
