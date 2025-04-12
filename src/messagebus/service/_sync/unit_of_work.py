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
    """Initial state of the transaction status in the context manager."""
    rolledback = "rolledback"
    """state of the transaction status after it has been aborted."""
    committed = "committed"
    """state of the transaction status after it has been committed."""
    closed = "closed"
    """state of the transaction status after the with state block."""
    streaming = "streaming"
    """
    Unsafe way to manually exit the transaction manager for streaming purpose.

    While streaming response in some context like FastAPI or Starlette
    StreamingResponse, the transaction must be closed lately, usually in a
    finally block to close the transaction.
    """


TRepositories = TypeVar("TRepositories", bound=SyncAbstractRepository[Any])


class SyncUnitOfWorkTransaction(Generic[TRepositories]):
    """
    Context manager for business transactions of the unit of work.

    While using a unit of work as a context manager, it will return a
    transaction object instead of the unit of work in order to track and
    ensure that the transaction has been manually committed, rolled back
    of detached for streaming purpose.
    """

    uow: SyncAbstractUnitOfWork[TRepositories]
    """Associated unit of work instance manipulated in the transaction."""
    status: TransactionStatus
    """Current status of the transaction"""

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
        """Commit the transaction, if things has been written"""
        if self.status != TransactionStatus.running:
            raise TransactionError(f"Transaction already closed ({self.status.value}).")
        self.uow.commit()
        self.status = TransactionStatus.committed
        self._on_after_commit()

    def rollback(self) -> None:
        """
        Rollback the transaction, preferred way to finalize a read only transaction.
        """
        self.uow.rollback()
        self.status = TransactionStatus.rolledback
        self._on_after_rollback()

    def detach(self) -> None:
        """
        Prepare a delayed transaction for streaming response.

        After detaching a transaction, always call the {method}`.close` method manually.
        """
        self.status = TransactionStatus.streaming

    def __enter__(self) -> SyncUnitOfWorkTransaction[TRepositories]:
        """Entering the transaction."""
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

        if self.status != TransactionStatus.streaming:
            self._close()

    def _close(self) -> None:
        if self.status == TransactionStatus.closed:
            raise TransactionError("Transaction is closed.")
        if self.status == TransactionStatus.running:
            raise TransactionError(
                "Transaction must be explicitly close. Missing commit/rollback call."
            )
        if self.status == TransactionStatus.committed:
            self.uow.eventstore.publish_eventstream()
        self.status = TransactionStatus.closed

    def close(self) -> None:
        """
        Manually close the transaction.

        This method has to be called manually only in case of streaming response.
        It will rollback the transaction automatically except if the transaction
        has been manually commited before.
        """
        if self.status == TransactionStatus.streaming:
            self.rollback()
        self._close()


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
