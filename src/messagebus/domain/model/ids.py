from uuid import UUID

from typing_extensions import NewType

MessageId = NewType("MessageId", UUID)
