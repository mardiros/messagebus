from messagebus import Field, Model

from .types import BookId, ReviewerId, ReviewId


class Book(Model):
    id: BookId = Field()
    title: str = Field()
    author: str = Field()
    isbn: str = Field()


class Reviewer(Model):
    id: ReviewerId = Field()
    nickname: str = Field()


class Review(Model):
    id: ReviewId = Field()
    reviewer_id: ReviewerId = Field()
    book_id: BookId = Field()
    rate: int = Field(ge=0, le=10)
    comment: str = Field()
