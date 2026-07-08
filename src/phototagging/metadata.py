import uuid
from datetime import datetime
from functools import total_ordering
from pathlib import Path
from typing import Any, Dict, Iterable, Set, TypeAlias

from pydantic import BaseModel, Field

MetadataMap: TypeAlias = Dict[int, "Metadata"]


# class MetadataFilled(BaseModel):
#     id: str
#     filename: str
#     full_path: Path
#     create_date: datetime
#     keywords: Set[str]
#     description: str
#     title: str


@total_ordering
class Metadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    full_path: Path
    create_date: datetime
    keywords: Set[str]
    description: str
    title: str

    def model_post_init(self, __context: Any):
        # Ensure keywords are stored in lowercase
        self.keywords = set(kw.lower() for kw in self.keywords)

    def append_keywords(self, new_keywords: Iterable[str]):
        """Append new keywords to the existing set of keywords."""
        if not new_keywords:
            return
        for keyword in new_keywords:
            self.keywords.add(keyword.lower())

    def replace_keywords(self, keywords: Iterable[str]):
        """Replace all keywords with the provided list."""
        self.keywords.clear()
        for keyword in keywords:
            self.keywords.add(keyword.lower())

    def remove_keywords(self, keywords_to_remove: Iterable[str]):
        """Remove specified keywords from the existing set of keywords."""
        for kw in keywords_to_remove:
            if kw.lower() in self.keywords:
                self.keywords.remove(kw.lower())

    @property
    def pexels(self) -> str:
        """Return keywords formatted for Pexels."""
        if not self.keywords:
            return ""
        return ", ".join(self.keywords)

    @property
    def instagram(self) -> str:
        """Return keywords formatted for Instagram hashtags."""
        if not self.keywords:
            return ""
        return " ".join(f"#{k.replace(' ', '')}" for k in self.keywords)

    def __lt__(self, other: Any):
        if not isinstance(other, Metadata):
            return NotImplemented
        return self.create_date < other.create_date

    def __eq__(self, other: Any):
        if not isinstance(other, Metadata):
            return NotImplemented
        return self.id == other.id

    def to_metadata_filled(self) -> Metadata:
        return self
