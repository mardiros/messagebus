from uuid import UUID

from messagebus import Event, Field, Metadata


class BookRegistered(Event):
    id: UUID = Field()
    isbn: str = Field()
    title: str = Field()
    author: str = Field()
    metadata: Metadata = Metadata(
        name="register_book",
        schema_version=1,
        published=True,
    )
