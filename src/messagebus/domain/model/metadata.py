"""
Metadata attribute for commands and events.

"""

from typing import TypeVar

from pydantic import BaseModel, Field


class Metadata(BaseModel):
    """
    Every message, commands and event have metadata used and sends while serialization.
    """

    name: str = Field(...)
    """
    Name of the schema.

    Identity a message type when serialization..
    """
    schema_version: int = Field(...)
    """
    Version of the schema.

    Every message schema is versionned in order to have multiple event/command
    living together with multiple handler.
    """
    published: bool = Field(default=False)
    """
    Publish the event to an eventstream.

    If the unit of work is associated to an eventstream, then the message is send
    throw it only if the flag has been set to True.

    It allows to have internal commands and events and public ones. Sending message
    to an event queue create a coupling, and updating signature can introduce breaking
    changes.
    """


TMetadata = TypeVar("TMetadata", bound=Metadata)
