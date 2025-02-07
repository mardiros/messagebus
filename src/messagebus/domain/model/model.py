"""
Message base classes.

`Command` and `Event` are two types used to handle changes in the model.

"""

from collections.abc import MutableSequence
from typing import Any, Generic

from pydantic import BaseModel, Field

from .message import Message
from .metadata import Metadata, TMetadata


class GenericModel(BaseModel, Generic[TMetadata]):
    """Base class for model."""

    messages: MutableSequence[Message[TMetadata]] = Field(
        default_factory=list, exclude=True
    )
    """
    List of messages consumed by the unit of work to mutate the repository.

    Those message are ephemeral, published by event handler and consumed
    by the unit of work during the process of an original command.
    """

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, GenericModel):
            return False
        slf = self.model_dump()
        otr = other.model_dump()
        return slf == otr


Model = GenericModel[Metadata]
