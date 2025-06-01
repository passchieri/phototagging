from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MetaData:
    id: str
    filename: str
    keywords: list[str] = field(default_factory=list)
    title: Optional[str] = None
    description: Optional[str] = None

    def pexels(self) -> str:
        """Return keywords formatted for Pexels."""
        return ", ".join(self.keywords)

    def instagram(self) -> str:
        """Return keywords formatted for Instagram hashtags."""
        return " ".join(f"#{k.replace(' ', '')}" for k in self.keywords)

    def to_dict(self) -> dict:
        """Convert the MetaData instance to a dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "keywords": self.keywords,
            "title": self.title,
            "description": self.description,
        }
