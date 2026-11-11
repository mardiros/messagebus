from uuid import UUID

from messagebus import Command, Field, Metadata


class RegisterBook(Command):
    id: UUID = Field()
    isbn: str = Field()
    title: str = Field()
    author: str = Field()
    metadata: Metadata = Metadata(name="register_book", schema_version=1)
