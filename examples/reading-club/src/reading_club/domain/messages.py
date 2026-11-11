from messagebus import Command, Event, Field, Metadata

from .types import BookId, ReviewerId, ReviewId


class RegisterBook(Command):
    id: BookId = Field()
    isbn: str = Field()
    title: str = Field()
    author: str = Field()
    metadata: Metadata = Metadata(name="register_book", schema_version=1)


class BookRegistered(Event):
    id: BookId = Field()
    isbn: str = Field()
    title: str = Field()
    author: str = Field()
    metadata: Metadata = Metadata(
        name="book_registered", schema_version=1, published=True
    )


class CreateReviewer(Command):
    id: ReviewerId = Field()
    nickname: str = Field()
    metadata: Metadata = Metadata(name="create_review", schema_version=1)


class ReviewerCreated(Command):
    id: ReviewerId = Field()
    nickname: str = Field()
    metadata: Metadata = Metadata(
        name="reviewer_created", schema_version=1, published=True
    )


class CreateReview(Command):
    id: ReviewId = Field()
    reviewer_id: ReviewerId = Field()
    book_id: BookId = Field()
    rate: int = Field()
    comment: str = Field()
    metadata: Metadata = Metadata(name="create_review", schema_version=1)


class ReviewCreated(Command):
    id: ReviewId = Field()
    reviewer_id: ReviewerId = Field()
    book_id: BookId = Field()
    rate: int = Field()
    comment: str = Field()
    metadata: Metadata = Metadata(
        name="create_review", schema_version=1, published=True
    )
