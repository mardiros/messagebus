"""
Message base classes.

`Command` and `Event` are two types used to handle changes in the model.

"""

from datetime import datetime
from typing import Any, Generic
from uuid import UUID

from lastuuid import uuid7
from pydantic import BaseModel, Field

from .metadata import Metadata, TMetadata


class Message(BaseModel, Generic[TMetadata]):
    """Base class for messaging."""

    message_id: UUID = Field(default_factory=uuid7)
    """Unique identifier of the message."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    """
    Timestamp of the message.

    All messages are kept in order for observability, debug and event replay.
    """
    metadata: TMetadata
    """
    Define extra fields used at serialization.

    While serializing the message, a name and version must be defined to properly
    defined the message. Event if the class is renamed, those constants must be kept
    identically over the time in the codebase.

    metadata are defined statically at the definition of the message.
    """

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Message):
            return False
        slf = self.model_dump(exclude={"message_id", "created_at"})
        otr = other.model_dump(exclude={"message_id", "created_at"})
        return slf == otr


class GenericCommand(Message[TMetadata]):
    """Baseclass for message of type command."""


class GenericEvent(Message[TMetadata]):
    """Baseclass for message of type event."""


Command = GenericCommand[Metadata]
Event = GenericEvent[Metadata]
