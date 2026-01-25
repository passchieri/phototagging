from typing import Any, Optional

from .metadata import MetaData
from .db import Db
from .phototag import PhotoTag


class MetadataManager:
    """
    Class to manage photo metadata using a database and PhotoTag API.
    """

    def __init__(self, db: Db, phototag: PhotoTag):
        self.db = db
        self.phototag = phototag


    def all(self) -> list[MetaData]:
        """Get all records from the database."""
        with self.db as c:
            data = c.all()
        return [MetaData(**item) for item in data]
    
    def search(self, field: str, value: Any) -> list[MetaData]:
        """Search for data in the database."""
        with self.db as c:
            data = c.search(field, value)
        return [MetaData(**item) for item in data]

    def get_or_fetch(
        self,
        filename: str,
        default_tags: Optional[list] = None,
        removed_tags: Optional[list] = None,
    ) -> Optional[MetaData]:
        """Get metadata for a file, or fetch it if not found.
        Makes sure all tags from default_tags are included, and remove tags from removed_tags.
        """

        metadata = self.get_by_filename(filename)
        if not metadata:
            metadata = self.fetch_for_file(filename)

        if not metadata:
            raise ValueError(f"Could not fetch metadata for file '{filename}'.")
        if not metadata.keywords:
            metadata.keywords = []
        if default_tags:
            self.ensure_keywords(metadata, default_tags)
        if removed_tags:
            self.remove_keywords(metadata, removed_tags)
        return metadata

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

    def fetch_for_file(self, filename: str, force=False) -> Optional[MetaData]:
        """Fetch metadata for a file using PhotoTag."""
        if not force and self.get_by_filename(filename):
            raise ValueError(
                f"Metadata for file '{filename}' already exists in the database."
            )
        data = self.phototag.fetch_for_file(filename)
        if not data:
            return None
        metadata = MetaData(**data)
        return self.update_db(metadata)

    def ensure_keywords(
        self, metadata: MetaData, required_keywords: list[str]
    ) -> MetaData:
        """Ensure all keywords are present in metadata."""
        metadata.append_keywords(required_keywords)
        return self.update_db(metadata)

    def remove_keywords(
        self, metadata: MetaData, keywords_to_remove: list[str]
    ) -> MetaData:
        """Remove specified keywords from metadata."""
        metadata.remove_keywords(keywords_to_remove)
        return self.update_db(metadata)

    def update_db(self, metadata):
        """Update or insert metadata into the database."""
        with self.db:
            self.db.update_or_insert(metadata.to_dict())
        return metadata
    

