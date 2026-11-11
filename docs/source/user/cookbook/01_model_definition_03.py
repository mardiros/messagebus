from uuid import UUID

from messagebus import Command, Field, Metadata


class RegisterBookV1(Command):
    """Initial version of the command authorize only one author per book."""

    id: UUID = Field()
    isbn: str = Field()
    title: str = Field()
    author: str = Field()
    metadata: Metadata = Metadata(name="register_book", schema_version=1)


class RegisterBookV2(Command):
    id: UUID = Field()
    isbn: str = Field()
    title: str = Field()
    authors: list[str] = Field()
    metadata: Metadata = Metadata(name="register_book", schema_version=2)
