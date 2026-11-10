from datetime import datetime

import pytest

from messagebus import Event, Field, Message, Metadata, Model


class Foo(Model):
    name: str


class FooCreated(Event):
    name: str
    metadata: Metadata = Metadata(name="foo_created", schema_version=1)


class Bar(Model):
    name: str


class BarCreated(Event):
    name: str
    metadata: Metadata = Metadata(name="bar_created", schema_version=1)


class BigMessage(Model):
    name: str
    eta: datetime | None = Field(default=None)


class BigMessageCreated(Event):
    name: str
    eta: datetime | None = Field(default=None)
    metadata: Metadata = Metadata(name="big_message_created", schema_version=1)


def attach_events(model: Model, messages: list[Message[Metadata]]) -> Model:
    """
    To fix: the constructor of Model subclass refused subinstance of message.
    pydantic raises an error.
    """
    for evt in messages:
        model.messages.append(evt)
    return model


@pytest.mark.parametrize(
    "obj,expected",
    [
        pytest.param(
            Foo(name="joe"),
            "<Foo name='joe'>",
        ),
        pytest.param(
            attach_events(Foo(name="joe"), [FooCreated(name="joe")]),
            "<Foo name='joe' messages=[<FooCreated name='joe'>]>",
            id="with messages",
        ),
        pytest.param(
            BigMessage(name="fatjoe"),
            "<BigMessage name='fatjoe'>",
            id="unset attr",
        ),
        pytest.param(
            BigMessage(name="fatjoe", eta=None),
            "<BigMessage name='fatjoe' eta=None>",
            id="none attr",
        ),
        pytest.param(
            attach_events(
                BigMessage(name="fatjoe"),
                [BigMessageCreated(name="fatjoe")],
            ),
            "<BigMessage name='fatjoe' messages=[<BigMessageCreated name='fatjoe'>]>",
            id="unset attr with evt",
        ),
        pytest.param(
            attach_events(
                BigMessage(name="fatjoe", eta=None),
                [BigMessageCreated(name="fatjoe", eta=None)],
            ),
            "<BigMessage name='fatjoe' eta=None "
            "messages=[<BigMessageCreated name='fatjoe' eta=None>]>",
            id="none attr with evt",
        ),
    ],
)
def test_model_repr(obj: Model, expected: str):
    assert repr(obj) == expected


def test_model_equal():
    assert Foo(name="joe") == Foo(name="joe")
    assert Foo(name="joe") != Bar(name="joe")
    assert Foo(name="joe") != object()


def test_message_equal():
    assert FooCreated(name="joe") == FooCreated(name="joe")
    assert FooCreated(name="joe") != BarCreated(name="joe")
    assert FooCreated(name="joe") != object()
