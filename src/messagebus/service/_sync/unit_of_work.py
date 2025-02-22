"""Unit of work"""

from __future__ import annotations

import abc
import enum
from collections.abc import Iterator
from types import TracebackType
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from messagebus.domain.model import Message

if TYPE_CHECKING:
    from messagebus.service._sync.dependency import SyncDependency  # coverage: ignore
from messagebus.service._sync.repository import (
    SyncAbstractRepository,
    SyncEventstoreAbstractRepository,
    SyncSinkholeEventstoreRepository,
)


class TransactionError(RuntimeError):
    """A runtime error raised if the transaction lifetime is inappropriate."""


class TransactionStatus(enum.Enum):
    """Transaction status used to ensure transaction lifetime."""

    running = "running"
    rolledback = "rolledback"
    committed = "committed"
    closed = "closed"


TRepositories = TypeVar("TRepositories", bound=SyncAbstractRepository[Any])


class SyncUnitOfWorkTransaction(Generic[TRepositories]):
    uow: SyncAbstractUnitOfWork[TRepositories]
    status: TransactionStatus

    def __init__(self, uow: SyncAbstractUnitOfWork[TRepositories]) -> None:
        self.status = TransactionStatus.running
        self.uow = uow
        self._hooks: list[Any] = []

    def __getattr__(self, name: str) -> TRepositories:
        return getattr(self.uow, name)

    @property
    def eventstore(self) -> SyncEventstoreAbstractRepository:
        return self.uow.eventstore

    def add_listener(self, listener: SyncDependency) -> SyncDependency:
        self._hooks.append(listener)
        return listener

    def _on_after_commit(self) -> None:
        for val in self._hooks:
            val.on_after_commit()

    def _on_after_rollback(self) -> None:
        for val in self._hooks:
            val.on_after_rollback()

    def commit(self) -> None:
        if self.status != TransactionStatus.running:
            raise TransactionError(f"Transaction already closed ({self.status.value}).")
        self.uow.commit()
        self.status = TransactionStatus.committed
        self._on_after_commit()

    def rollback(self) -> None:
        self.uow.rollback()
        self.status = TransactionStatus.rolledback
        self._on_after_rollback()

    def __enter__(self) -> SyncUnitOfWorkTransaction[TRepositories]:
        if self.status != TransactionStatus.running:
            raise TransactionError("Invalid transaction status.")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Rollback in case of exception."""
        if exc:
            self.rollback()
            return
        if self.status == TransactionStatus.closed:
            raise TransactionError("Transaction is closed.")
        if self.status == TransactionStatus.running:
            raise TransactionError(
                "Transaction must be explicitly close. Missing commit/rollback call."
            )
        if self.status == TransactionStatus.committed:
            self.uow.eventstore.publish_eventstream()
        self.status = TransactionStatus.closed


class SyncAbstractUnitOfWork(abc.ABC, Generic[TRepositories]):
    """
    Abstract unit of work.

    To implement a unit of work, the :meth:`AsyncAbstractUnitOfWork.commit` and
    :meth:`AsyncAbstractUnitOfWork.rollback` has to be defined, and some repositories
    has to be declared has attributes.
    """

    eventstore: SyncEventstoreAbstractRepository = SyncSinkholeEventstoreRepository()

    def collect_new_events(self) -> Iterator[Message[Any]]:
        for repo in self._iter_repositories():
            while repo.seen:
                model = repo.seen.pop(0)
                while model.messages:
                    yield model.messages.pop(0)

    def _iter_repositories(
        self,
    ) -> Iterator[SyncAbstractRepository[Any]]:
        for member_name in self.__dict__.keys():
            member = getattr(self, member_name)
            if isinstance(member, SyncAbstractRepository):
                yield member

    def __enter__(self) -> SyncUnitOfWorkTransaction[TRepositories]:
        self.__transaction = SyncUnitOfWorkTransaction(self)
        self.__transaction.__enter__()
        return self.__transaction

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        # AsyncUnitOfWorkTransaction is making the thing
        self.__transaction.__exit__(exc_type, exc, tb)

    @abc.abstractmethod
    def commit(self) -> None:
        """Commit the transation."""

    @abc.abstractmethod
    def rollback(self) -> None:
        """Rollback the transation."""


TSyncUow = TypeVar("TSyncUow", bound=SyncAbstractUnitOfWork[Any])
