from typing import Any, Optional

from .metadata import MetaData
from .db import Db
from .phototag import PhotoTag, PhotoTagResponse


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

    def get_or_create(
        self,
        filename: str,
        force: bool = False,
        default_keywords: Optional[list[str]] = None,
        keywords_to_remove: Optional[list[str]] = None,
    ) -> Optional[MetaData]:
        """Get metadata for a file, or create it if not found.

        It ensures that all keywords from default_keywords are included, and removes keywords from
        keywords_to_remove.

        Args:
            filename: The name of the file to get or create metadata for.
            force: If True, forces creation of metadata even if it already exists.
            default_keywords: A list of keywords to ensure are included in the metadata.
            keywords_to_remove: A list of keywords to remove from the metadata.
        """

        metadata = self.get_by_filename(filename)
        if not metadata or force:
            metadata = self.create_for_file(filename, force,required_keywords=default_keywords, keywords_to_remove=keywords_to_remove)
            if not metadata:
                raise ValueError(f"Could not create metadata for file '{filename}'.")
        else:
            self.update_keywords(metadata, default_keywords, keywords_to_remove)
        return metadata

    def get_by_id(self, id: str) -> Optional[MetaData]:
        """Get a single record from the database."""
        with self.db as c:
            data = c.get_by_id(id)
        if data:
            return MetaData(**data)
        fetched_data: PhotoTagResponse = self.phototag.fetch_for_file(id)
        if fetched_data:
            metadata = MetaData(**fetched_data)
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

    def create_for_file(
        self,
        filename: str,
        force: bool = False,
        required_keywords: Optional[list[str]] = None,
        keywords_to_remove: Optional[list[str]] = None,
    ) -> Optional[MetaData]:
        """Create metadata for a file using PhotoTag."""
        if not force and self.get_by_filename(filename):
            raise ValueError(f"Metadata for file '{filename}' already exists in the database.")
        data = self.phototag.fetch_for_file(filename)
        if not data:
            return None
        metadata = MetaData(**data)
        metadata = self.update_keywords(metadata, required_keywords, keywords_to_remove)
        return metadata

    def update_keywords(
        self,
        metadata: MetaData,
        required_keywords: Optional[list[str]] = None,
        keywords_to_remove: Optional[list[str]] = None,
    ) -> MetaData:
        """Update keywords in metadata."""
        if required_keywords is not None:
            metadata.append_keywords(required_keywords)
        if keywords_to_remove is not None:
            metadata.remove_keywords(keywords_to_remove)
        return self.update_db(metadata)

    def update_db(self, metadata: MetaData) -> MetaData:
        """Update or insert metadata into the database."""
        with self.db:
            self.db.update_or_insert(metadata.to_dict())
        return metadata
