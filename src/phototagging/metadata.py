from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Self, Tuple

from sortedcontainers import SortedSet

from .db import DbMetadata


@dataclass
class MetaData:
    """Class representing metadata for a photo."""

    id: int
    filename: str
    full_path: str = ""
    keywords: SortedSet[str] = field(default_factory=SortedSet[str])
    title: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        """Normalize keywords to lowercase and ensure they are stored as a set."""
        self.keywords = SortedSet(str(kw).lower() for kw in self.keywords)

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

    def create_full_path(self, dir: str = "/Users/igor/Pictures/Lightroom Saved Photos/") -> bool:
        if self.full_path == "":
            d = Path(dir)
            path = d / self.filename
            if path.exists():
                self.full_path = str(path.resolve())
                return True
        return False

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

    def to_dict(self) -> dict[str, Any]:
        """Convert the MetaData instance to a dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "full_path": self.full_path,
            "keywords": list(self.keywords),
            "title": self.title,
            "description": self.description,
        }

    def to_db_metadata(self) -> Tuple[int, DbMetadata]:
        md = DbMetadata(**self.to_dict())
        return (self.id, md)

    @classmethod
    def from_db_metadata(cls, id: int, data: DbMetadata) -> Self:
        ret = cls(**data.model_dump(), id=id)
        return ret

    @classmethod
    def from_db_metadata_dict(cls, data: Dict[int, DbMetadata]) -> List[Self]:
        ret = [cls(id=k, **v.model_dump()) for k, v in data.items()]
        return ret
