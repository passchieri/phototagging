from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List, Optional, Set

from phototagging.db import Db

from .metadata import Metadata
from .phototag import PhotoTag


class MetadataManager:
    """
    Class to manage photo metadata using a database and PhotoTag API.
    """

    def __init__(self, db: Db, phototag: PhotoTag):
        self.db = db
        self.phototag = phototag

    def all(self) -> List[Metadata]:
        """Get all records from the database."""
        with self.db as c:
            data = c.all()
        return data

    def all_dirs(self) -> List[Path]:
        """Get all folders included in the database"""
        with self.db as c:
            data = c.all_dirs()
        return data

    def search(self, field: str, value: Any) -> List[Metadata]:
        """Search for data in the database."""
        with self.db as c:
            data = c.search(field, value)

        return data

    def get_or_create(
        self,
        full_path: str | Path,
        required_keywords: Optional[list[str]] = None,
        keywords_to_remove: Optional[list[str]] = None,
        force: bool = False,
    ) -> Metadata:
        """Get metadata for a file, or create it if not found.

        It ensures that all keywords from default_keywords are included, and removes keywords from
        keywords_to_remove.

        Args:
            filename: The name of the file to get or create metadata for.
            force: If True, forces creation of metadata even if it already exists.
            default_keywords: A list of keywords to ensure are included in the metadata.
            keywords_to_remove: A list of keywords to remove from the metadata.
        """

        if isinstance(full_path, str):
            full_path = Path(full_path)
        full_path = full_path.resolve()
        filename = full_path.name

        if force:
            try:
                self.delete_by_filename(filename)
            except ValueError:
                pass  # Ignore value error: the record just did not exist

        metadata = self.get_by_filename(filename)

        if not metadata:  # Does not exist yet, so we create it
            metadata = self.create(
                full_path=full_path,
                required_keywords=required_keywords,
                keywords_to_remove=keywords_to_remove,
            )
        else:
            self.update_keywords(
                metadata,
                keywords_to_add=required_keywords,
                keywords_to_remove=keywords_to_remove,
            )
        return metadata

    def get_by_id(self, id: str) -> Metadata:
        """Get a single record from the database."""
        with self.db as c:
            return c.get(id)

    def get_by_filename(self, filename: str) -> Optional[Metadata]:
        """Get a single record by filename."""
        with self.db as c:
            return c.get_by_filename(filename)

    def delete_by_filename(self, filename: str) -> None:
        """Delete a single record by filename."""
        with self.db as c:
            c.delete_by_filename(filename)

    def delete_by_id(self, id: str) -> None:
        """Delete a single record by id."""
        with self.db as c:
            c.delete(id)

    def create(
        self,
        full_path: str | Path,
        required_keywords: Optional[list[str]] = None,
        keywords_to_remove: Optional[list[str]] = None,
    ) -> Metadata:
        """Create metadata for a file using PhotoTag."""
        if isinstance(full_path, str):
            full_path = Path(full_path)
        full_path = full_path.resolve()
        filename = full_path.name
        if self.get_by_filename(filename):
            raise ValueError(f"Metadata for file '{filename}' already exists in the database.")
        data = self.phototag.fetch_for_file(full_path)
        if not data:
            raise ExternalServiceError("Phototag api did not return any value")
        kws = data.get("keywords", [])
        if required_keywords:
            for kw in required_keywords:
                kws.append(kw)
        if keywords_to_remove:
            for kw in keywords_to_remove:
                while kw in kws:
                    kws.remove(kw)
        metadata = self._create_metadata(
            full_path=full_path,
            title=data.get("title", "") or "",
            keywords=set(kws),
            description=data.get("description", "") or "",
        )
        self._insert_db(metadata)
        return metadata

    def update_keywords(
        self,
        metadata: Metadata,
        keywords: Optional[Iterable[str]] = None,
        keywords_to_add: Optional[Iterable[str]] = None,
        keywords_to_remove: Optional[Iterable[str]] = None,
    ) -> Metadata:
        """Update keywords in metadata."""
        if keywords and (keywords_to_add or keywords_to_remove):
            raise ValueError("Setting keywords and also keywords_to_add or keywords_to_remove is not allowed")
        if keywords:
            metadata.replace_keywords(keywords)
        if keywords_to_add:
            metadata.append_keywords(keywords_to_add)
        if keywords_to_remove:
            metadata.remove_keywords(keywords_to_remove)
        self._update_db(metadata)
        return metadata

    def update_keywords_for_file(
        self,
        filename: str,
        keywords: Optional[Iterable[str]] = None,
        keywords_to_add: Optional[Iterable[str]] = None,
        keywords_to_remove: Optional[Iterable[str]] = None,
    ) -> Metadata:
        metadata = self.get_by_filename(filename)
        if not metadata:
            raise ValueError(f"No metadata found for file {filename}")
        return self.update_keywords(metadata, keywords, keywords_to_add, keywords_to_remove)

    def _create_metadata(
        self,
        full_path: Path,
        title: str,
        description: str,
        keywords: Set[str],
    ) -> Metadata:
        """Create a new record in the database, and return the resulting Metadata."""
        p = Path(full_path).resolve()
        try:
            create_date = datetime.fromtimestamp(p.stat().st_ctime)
        except FileNotFoundError:
            create_date = datetime.now()

        data = Metadata(
            filename=p.name,
            full_path=p,
            create_date=create_date,
            keywords=keywords,
            description=description,
            title=title,
        )
        return data

    def _insert_db(self, metadata: Metadata) -> None:
        with self.db as c:
            c.insert(metadata)

    def _update_db(self, metadata: Metadata) -> None:
        """Update the database with updated metadata"""
        with self.db as c:
            c.update(metadata)

    def __repr__(self):
        return f"MetadataManager(db={self.db}, phototag={self.phototag})"


class ExternalServiceError(Exception):
    """Generic error raised when the external API cannot be used."""

    pass
