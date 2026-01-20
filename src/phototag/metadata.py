from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MetaData:
    """Class representing metadata for a photo."""

    id: str
    filename: str
    keywords: list[str] = field(default_factory=list)
    title: Optional[str] = None
    description: Optional[str] = None

    def append_keywords(self, new_keywords: list[str]):
        """Append new keywords to the existing set of keywords."""
        for keyword in new_keywords:
            if keyword not in self.keywords:
                self.keywords.append(keyword)

    def remove_keywords(self, keywords_to_remove: list[str]):
        """Remove specified keywords from the existing set of keywords."""
        self.keywords = [kw for kw in self.keywords if kw not in keywords_to_remove]

    def pexels(self) -> str:
        """Return keywords formatted for Pexels."""
        return ", ".join(sorted(set(self.keywords)))

    def instagram(self) -> str:
        """Return keywords formatted for Instagram hashtags."""
        return " ".join(f"#{k.replace(' ', '')}" for k in sorted(set(self.keywords)))

    def to_dict(self) -> dict:
        """Convert the MetaData instance to a dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "keywords": sorted(set(self.keywords)),
            "title": self.title,
            "description": self.description,
        }
