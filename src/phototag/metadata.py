from dataclasses import dataclass, field
from typing import Any, Iterable, Optional


@dataclass
class MetaData:
    """Class representing metadata for a photo."""

    id: str
    filename: str
    keywords: set[str] = field(default_factory=set[str])
    title: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        """Normalize keywords to lowercase and ensure they are stored as a set."""
        self.keywords = set(kw.lower() for kw in self.keywords)

    def append_keywords(self, new_keywords: Iterable[str]):
        """Append new keywords to the existing set of keywords."""
        if not new_keywords:
            return
        for keyword in new_keywords:
            self.keywords.add(keyword.lower())

    def remove_keywords(self, keywords_to_remove: Iterable[str]):
        """Remove specified keywords from the existing set of keywords."""
        for kw in keywords_to_remove:
            if kw.lower() in self.keywords:
                self.keywords.remove(kw.lower())

    def pexels(self) -> str:
        """Return keywords formatted for Pexels."""
        if not self.keywords:
            return ""
        return ", ".join(sorted(set(self.keywords)))

    def instagram(self) -> str:
        """Return keywords formatted for Instagram hashtags."""
        if not self.keywords:
            return ""
        return " ".join(f"#{k.replace(' ', '')}" for k in sorted(set(self.keywords)))

    def to_dict(self) -> dict[str, Any]:
        """Convert the MetaData instance to a dictionary."""
        kw = []
        if self.keywords:
            kw = sorted(self.keywords)
        return {
            "id": self.id,
            "filename": self.filename,
            "keywords": kw,
            "title": self.title,
            "description": self.description,
        }
