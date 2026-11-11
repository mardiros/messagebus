from typing import Any

from reading_club.ports.repositories import AbstractBookRepository

from messagebus import AsyncAbstractUnitOfWork


class AbstractUnitOfWork(AsyncAbstractUnitOfWork[AbstractBookRepository, Any, Any]):
    books: AbstractBookRepository
