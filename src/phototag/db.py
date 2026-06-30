from pathlib import Path
from types import TracebackType
from typing import Any, Dict, List, Optional, Tuple, TypeAlias, TypeVar

from pydantic import BaseModel, Field, field_validator
from tinydb import Query, TinyDB
from tinydb.table import Document


# class Document(Dict[str, Any]):
#     """A simple wrapper around TinyDB's document format that includes the document ID."""
#     doc_id: int
class DbMetadata(BaseModel):
    filename: str = Field(..., min_length=1)
    full_path: str = Field(default="")
    keywords: List[str] = Field(default_factory=list)
    description: str = ""
    title: str = ""


T = TypeVar("T")


class DbMetadataPatch(BaseModel):
    filename: Optional[str] = None
    keywords: Optional[List[str]] = None
    description: Optional[str] = None
    title: Optional[str] = None

    @field_validator("*")
    def no_empty_values(cls, v: T) -> Optional[T]:
        if v == "" or v == []:
            return None
        return v

    # Add other fields as needed


DbMetadataMap: TypeAlias = Dict[int, DbMetadata]


class Db:
    """
    A simple database wrapper around TinyDB for storing photo metadata.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._db: Optional[TinyDB] = None

    def __enter__(self) -> "Db":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def connect(self) -> None:
        """Connect to the database."""
        self._db = TinyDB(self.db_path)

    def close(self):
        """Close the database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None

    def insert(self, data: DbMetadata) -> int:
        """Insert data into the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        if self._filename_exists_in_db(data.filename):
            raise ValueError(f"Data with filename '{data.filename}' already exists in the database.")
        id = self._db.insert(data.model_dump())  # pyright: ignore[reportUnknownMemberType]
        return id

    def get(self, id: int) -> Tuple[int, DbMetadata]:
        """Get a single record from the database by id."""

        if self._db is None:
            raise RuntimeError("Database not connected.")

        doc = self._db.get(doc_id=id)  # pyright: ignore[reportUnknownMemberType]
        if doc is None:
            raise ValueError(f"No document found with id '{id}'.")
        assert isinstance(doc, Document)
        data = DbMetadata(**doc)  # type: ignore
        return (id, data)

    def update(self, id: int, data: DbMetadata) -> int:
        """Update data in the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        assert self.get(id) is not None
        ids = self._db.update(data.model_dump(), doc_ids=[id])  # pyright: ignore[reportUnknownMemberType]
        if not ids:
            raise RuntimeError(f"Failed to update document with id '{id}'.")
        if len(ids) > 1:
            raise RuntimeError(f"Multiple documents updated with id '{id}', expected only one.")
        return ids[0]

    def patch(self, id: int, data: DbMetadataPatch) -> int:
        """Update data in the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        id, ret = self.get(id)

        combined = {**ret.model_dump(), **{k: v for k, v in data.model_dump().items() if v is not None}}
        md = DbMetadata(**combined)

        ids = self._db.update(md.model_dump(), doc_ids=[id])  # pyright: ignore[reportUnknownMemberType]
        if not ids:
            raise RuntimeError(f"Failed to patch document with id '{id}'.")
        if len(ids) > 1:
            raise RuntimeError(f"Multiple documents patched with id '{id}', expected only one.")
        return ids[0]

    def delete(self, id: int) -> int:
        """Delete data from the database by id."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        assert self.get(id) is not None
        ids = self._db.remove(doc_ids=[id])
        if not ids:
            raise RuntimeError(f"Failed to delete document with id '{id}'.")
        if len(ids) > 1:
            raise RuntimeError(f"Multiple documents deleted with id '{id}', expected only one.")
        return ids[0]

    def search(self, field: str, value: Any) -> DbMetadataMap:
        """Search for data in the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        if field == "keywords":
            ret = self._db.search(Query()[field].any(value))
        else:
            ret = self._db.search(Query()[field] == value)
        return self._to_metadata_dict(ret)

    def get_by_filename(self, filename: str) -> Optional[Tuple[int, DbMetadata]]:
        """Get a single record from the database by filename.
        If multiple records are found with the same filename, a ValueError is raised.
        If no records are found, None is returned."""
        path = Path(filename)
        results = self.search("filename", path.name)
        assert len(results) <= 1, f"Multiple records found with filename '{filename}'"
        if len(results) == 0:
            return None
        id = next(iter(results))
        data = results[id]
        return (id, data)

    def delete_by_filename(self, filename: str) -> int | None:
        """Delete a single record by filename."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        ret = self.get_by_filename(filename)
        if ret:
            return self.delete(ret[0])
        else:
            return None

    def all(self) -> DbMetadataMap:
        """Get all records from the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        return self._to_metadata_dict(self._db.all())

    def len(self) -> int:
        """Get the number of records in the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        return len(self._db)

    def _to_metadata_dict(self, list_of_documents: List[Document] | Document) -> DbMetadataMap:
        if isinstance(list_of_documents, Document):
            list_of_documents = [list_of_documents]
        return {doc.doc_id: DbMetadata(**doc) for doc in list_of_documents}  # type: ignore

    def _filename_exists_in_db(self, filename: str) -> bool:
        """Check if a filename already exists in the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        return self._db.contains(Query().filename == filename)


# def main() -> None:
#     db = Db("test_db.json")
#     with db as c:
#         metadata = DbMetadata(
#             filename="test.jpg", keywords=["nature", "sunset"], description="A beautiful sunset.", title="Sunset"
#         )
#         id = c.insert(metadata)
#         print(f"Inserted record with id: {id}")
#         # print(db.all())
