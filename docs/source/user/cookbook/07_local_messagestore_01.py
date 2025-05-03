from collections.abc import MutableSequence
from typing import Any, ClassVar

from messagebus import AsyncMessageStoreAbstractRepository, Message


class InMemoryMessageStoreRepository(AsyncMessageStoreAbstractRepository):
    messages: ClassVar[MutableSequence[Message[Any]]] = []

    async def _add(self, message: Message[Any]) -> None:
        self.messages.append(message)
