from typing import NewType
from uuid import UUID

BookId = NewType("BookId", UUID)
ReviewerId = NewType("ReviewerId", UUID)
ReviewId = NewType("ReviewId", UUID)
