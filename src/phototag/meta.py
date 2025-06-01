from typing import Any, Optional

from .metadata import MetaData
from .db import Db
from .phototag import PhotoTag


class Meta:
    def __init__(self, db: Db):
        self.db = db
        self.phototag = PhotoTag()

    def search(self, field: str, value: Any) -> list[MetaData]:
        """Search for data in the database."""
        with self.db as c:
            data = c.search(field, value)
        return [MetaData(**item) for item in data]

    def get_or_fetch(self, filename: str) -> Optional[MetaData]:
        """Get metadata for a file, or fetch it if not found."""

        metadata = self.get_by_filename(filename)
        if metadata:
            return metadata
        return self.fetch_for_file(filename)

    def get_by_id(self, id: str) -> Optional[MetaData]:
        """Get a single record from the database."""
        with self.db as c:
            data = c.get_by_id(id)
        if data:
            return MetaData(**data)
        data = self.phototag.fetch_for_file(id)
        if data:
            metadata = MetaData(**data)
            self.db.insert(metadata.to_dict())
            return metadata
        return None

    def get_by_filename(self, filename: str) -> Optional[MetaData]:
        """Get a single record by filename."""
        with self.db as c:
            data = c.get_by_filename(filename)
        if data:
            return MetaData(**data)
        return None

    def fetch_for_file(self, filename: str, force=False) -> MetaData:
        """Fetch metadata for a file using PhotoTag."""
        if not force and self.get_by_filename(filename):
            raise ValueError(
                f"Metadata for file '{filename}' already exists in the database."
            )
        data = self.phototag.fetch_for_file(filename)
        metadata = MetaData(**data)
        with self.db:
            self.db.update_or_insert(metadata.to_dict())
        return metadata
