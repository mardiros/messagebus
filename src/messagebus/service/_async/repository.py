"""
Repositories are used to fetch and store domain models.

Anstract repositories derived the :class:`messagebus.AsyncAbstractRepository`
class to declare every models interface such as CRUD operations,
and then concrete models implements those abstract methods for a given
storage.
"""

import abc
from collections.abc import MutableSequence
from typing import Any, Generic, TypeVar

from messagebus.domain.model import GenericModel, Message
from messagebus.service._async.eventstream import AsyncEventstreamPublisher

TModel_contra = TypeVar("TModel_contra", bound=GenericModel[Any], contravariant=True)


class AsyncAbstractRepository(abc.ABC, Generic[TModel_contra]):
    """Abstract Base Classe for Repository pattern."""

    def __init__(self) -> None:
        self.seen = []

    seen: MutableSequence[TModel_contra]


class AsyncEventstoreAbstractRepository(abc.ABC):
    def __init__(self, publisher: AsyncEventstreamPublisher | None = None) -> None:
        self.publisher = publisher
        self.stream_buffer: MutableSequence[Message[Any]] = []

    @abc.abstractmethod
    async def _add(self, message: Message[Any]) -> None:
        """
        Add a message to the storage backend of event repository.
        """

    async def add(self, message: Message[Any]) -> None:
        """
        Add the message to the storage backend and mark as seen

        seen message will be sent to the eventstream only if the unit of work
        has properly commit the transaction.
        If the transaction is rollback, then, message will be dropped too from the
        eventstream.
        """
        await self._add(message)
        self.stream_buffer.append(message)

    async def publish_eventstream(self) -> None:
        """
        Publish seen message to the eventstream.
        """
        stream_buffer, self.stream_buffer = self.stream_buffer, []
        if not self.publisher:
            return

        for message in stream_buffer:
            await self.publisher.send_message(message)


class AsyncSinkholeEventstoreRepository(AsyncEventstoreAbstractRepository):
    """An eventstore that drop all the message."""

    async def _add(self, message: Message[Any]) -> None:
        """Do nothing. The sinkhole drop every message."""
