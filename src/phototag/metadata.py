from dataclasses import dataclass, field
from operator import is_none
from typing import Any, Optional


@dataclass
class MetaData:
    """Class representing metadata for a photo."""

    id: str
    filename: str
    keywords: list[str]  = field(default_factory=list[str])
    title: Optional[str] = None
    description: Optional[str] = None

    def append_keywords(self, new_keywords: list[str]):
        """Append new keywords to the existing set of keywords."""
        if not new_keywords:
            return
        if is_none(self.keywords):
            self.keywords = []
        for keyword in new_keywords:
            if keyword not in self.keywords:
                self.keywords.append(keyword)

    def remove_keywords(self, keywords_to_remove: list[str]):
        """Remove specified keywords from the existing set of keywords."""
        if not self.keywords:
            return
        self.keywords = [kw for kw in self.keywords if kw not in keywords_to_remove]

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

    def to_dict(self) -> dict[str,Any]:
        """Convert the MetaData instance to a dictionary."""
        kw=[]
        if self.keywords:
            kw=sorted(set(self.keywords))
        return {
            "id": self.id,
            "filename": self.filename,
            "keywords": kw,
            "title": self.title,
            "description": self.description,
        }
