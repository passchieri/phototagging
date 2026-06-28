from pathlib import Path
from typing import Any, Iterable, List, Optional


from .metadata import MetaData
from .db import Db, DbMetadata
from .phototag import PhotoTag


class MetadataManager:
    """
    Class to manage photo metadata using a database and PhotoTag API.
    """

    def __init__(self, db: Db, phototag: PhotoTag):
        self.db = db
        self.phototag = phototag

    def all(self) -> List[MetaData]:
        """Get all records from the database."""
        with self.db as c:
            data = c.all()
        mdd = MetaData.from_db_metadata_dict(data)
        # for md in mdd:
        #     if md.create_full_path():
        #         print(f"Updating full path of {md.filename}")
        #         self._update_db(md)

        return mdd

    def search(self, field: str, value: Any) -> List[MetaData]:
        """Search for data in the database."""
        with self.db as c:
            data = c.search(field, value)

        return MetaData.from_db_metadata_dict(data)

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

        if force:
            try:
                self.delete_by_filename(filename)
            except ValueError:
                pass  # Ignore value error: the record just did not exist

        metadata = self.get_by_filename(filename)

        if not metadata:  # Does not exist yet, so we create it
            metadata = self.create(
                filename,
                required_keywords=default_keywords,
                keywords_to_remove=keywords_to_remove,
            )
        else:
            self.update_keywords(
                metadata,
                keywords_to_add=default_keywords,
                keywords_to_remove=keywords_to_remove,
            )
        return metadata

    def get_by_id(self, id: int) -> MetaData:
        """Get a single record from the database."""
        with self.db as c:
            result = c.get(id)
            if not result:
                raise ValueError(f"No metadata for id {id}")
            return MetaData.from_db_metadata(result[0], result[1])

    def get_by_filename(self, filename: str) -> Optional[MetaData]:
        """Get a single record by filename."""
        with self.db as c:
            data = c.get_by_filename(filename)
        if data:
            return MetaData.from_db_metadata(data[0], data[1])
        else:
            return None

    def delete_by_filename(self, filename: str) -> None:
        """Delete a single record by filename."""
        with self.db as c:
            data = c.get_by_filename(filename)
            if not data:
                raise ValueError(f"No record found with filename '{filename}'.")
            c.delete(data[0])

    def delete_by_id(self, id: int) -> None:
        """Delete a single record by id."""
        with self.db as c:
            data = c.get(id)
            if not data:
                raise ValueError(f"No record found with id '{id}'.")
            c.delete(data[0])

    def create(
        self,
        filename: str,
        required_keywords: Optional[list[str]] = None,
        keywords_to_remove: Optional[list[str]] = None,
    ) -> MetaData:
        """Create metadata for a file using PhotoTag."""
        if self.get_by_filename(filename):
            raise ValueError(
                f"Metadata for file '{filename}' already exists in the database."
            )
        data = self.phototag.fetch_for_file(filename)
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
        metadata = self._create_db_record(
            filename=Path(filename).name,
            full_path=str(Path(filename).resolve()),
            title=data.get("title", "") or "",
            keywords=kws,
            description=data.get("description", "") or "",
        )
        return metadata

    def update_keywords(
        self,
        metadata: MetaData,
        keywords: Optional[Iterable[str]] = None,
        keywords_to_add: Optional[Iterable[str]] = None,
        keywords_to_remove: Optional[Iterable[str]] = None,
    ) -> MetaData:
        """Update keywords in metadata."""
        if keywords and (keywords_to_add or keywords_to_remove):
            raise ValueError(
                "Setting keywords and also keywords_to_add or keywords_to_remove is not allowed"
            )
        if keywords:
            metadata.replace_keywords(keywords)
        if keywords_to_add:
            metadata.append_keywords(keywords_to_add)
        if keywords_to_remove:
            metadata.remove_keywords(keywords_to_remove)
        return self._update_db(metadata)

    def update_keywords_for_file(
        self,
        filename: str,
        keywords: Optional[Iterable[str]] = None,
        keywords_to_add: Optional[Iterable[str]] = None,
        keywords_to_remove: Optional[Iterable[str]] = None,
    ) -> MetaData:
        metadata = self.get_by_filename(filename)
        if not metadata:
            raise ValueError(f"No metadata found for file {filename}")
        return self.update_keywords(
            metadata, keywords, keywords_to_add, keywords_to_remove
        )

    def _create_db_record(
        self,
        filename: str,
        full_path: str,
        title: str,
        description: str,
        keywords: List[str],
    ) -> MetaData:
        """Create a new record in the database, and return the resulting MetaData"""
        data = DbMetadata(
            filename=filename,
            full_path=full_path,
            keywords=keywords,
            description=description,
            title=title,
        )
        with self.db as c:
            id = c.insert(data)
            md = MetaData.from_db_metadata(id, data)
            return md

    def _update_db(self, metadata: MetaData) -> MetaData:
        """Update the database with updated metadata"""
        with self.db as c:
            id, md = metadata.to_db_metadata()
            c.update(id, md)
        return metadata


class ExternalServiceError(Exception):
    """Generic error raised when the external API cannot be used."""

    pass
