from collections.abc import MutableSequence
from typing import Any, ClassVar

from messagebus import AsyncAbstractMessageStoreRepository, Message


class InMemoryMessageStoreRepository(AsyncAbstractMessageStoreRepository):
    messages: ClassVar[MutableSequence[Message[Any]]] = []

    async def _add(self, message: Message[Any]) -> None:
        self.messages.append(message)
