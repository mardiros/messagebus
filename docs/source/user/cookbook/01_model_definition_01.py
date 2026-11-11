from uuid import UUID

from messagebus import Field, Model


class Book(Model):
    id: UUID = Field()
    title: str = Field()
    author: str = Field()
    isbn: str = Field()
