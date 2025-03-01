from messagebus import Event, Metadata, Model


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


def test_model_repr():
    assert repr(Foo(name="joe")) == "<Foo name='joe'>"


def test_model_repr_with_messages():
    foo = Foo(name="joe")
    foo.messages.append(FooCreated(name="joe"))
    assert repr(foo) == "<Foo name='joe' message=[<FooCreated name='joe'>]>"


def test_model_equal():
    assert Foo(name="joe") == Foo(name="joe")
    assert Foo(name="joe") != Bar(name="joe")


def test_message_equal():
    assert FooCreated(name="joe") == FooCreated(name="joe")
    assert FooCreated(name="joe") != BarCreated(name="joe")
