import pytest
from pydantic import Field

from messagebus.domain.model import (
    GenericCommand,
    GenericEvent,
    Metadata,
)


class MyMetadata(Metadata):
    custom_field: str


class DummyCommand(GenericCommand[MyMetadata]):
    id: str = Field(...)
    metadata: MyMetadata = MyMetadata(
        name="dummy", schema_version=1, custom_field="foo"
    )


class AnotherDummyCommand(GenericCommand[MyMetadata]):
    id: str = Field(...)
    metadata: MyMetadata = MyMetadata(name="dummy2", schema_version=1, custom_field="f")


class DummyEvent(GenericEvent[MyMetadata]):
    id: str = Field(...)
    increment: int = Field(...)
    metadata: MyMetadata = MyMetadata(
        name="dummied", schema_version=1, published=True, custom_field="foo"
    )


@pytest.fixture
def dummy_command() -> DummyCommand:
    return DummyCommand(id="dummy_cmd")


@pytest.fixture
def dummy_event() -> DummyEvent:
    return DummyEvent(id="dummy_evt", increment=1)
