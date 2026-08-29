from pathlib import Path
from types import TracebackType
from typing import Any, List, Optional, Set, TypeVar

from tinydb import Query, TinyDB
from tinydb.queries import QueryLike
from tinydb.table import Document

from .metadata import Metadata

T = TypeVar("T")


def _search(field: str, value: Any) -> QueryLike:
    """Return a TinyDB Query object for searching by field and value."""
    if field == "keywords":
        return Query().keywords.any(value)
    elif isinstance(value, list):
        return Query()[field].one_of(value)  # type: ignore
    else:
        return Query()[field] == value


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
        self.disconnect()

    def connect(self) -> None:
        """Connect to the database."""
        self._db = TinyDB(self.db_path)

    def disconnect(self):
        """Close the database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None

    def insert(self, data: Metadata) -> str:
        """Insert data into the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        if self._db.contains(_search("filename", data.filename)):
            raise ValueError(f"Data with filename '{data.filename}' already exists in the database.")
        if self._db.contains(_search("id", data.id)):
            raise ValueError(f"Data with id '{data.id}' already exists in the database.")
        self._db.insert(data.model_dump(mode="json"))  # type: ignore
        return data.id

    def get(self, id: str) -> Metadata:
        """Get a single record from the database by id."""

        if self._db is None:
            raise RuntimeError("Database not connected.")

        docs = self._db.search(_search("id", id))
        if not docs:
            raise ValueError(f"No document found with id '{id}'.")

        assert len(docs) == 1, f"Multiple documents found with id '{id}', expected only one."
        data = Metadata(**docs[0])  # type: ignore
        return data

    def update(self, data: Metadata) -> str:
        """Update data in the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        assert self.get(data.id) is not None
        ids = self._db.update(data.model_dump(mode="json"), _search("id", data.id))  # type: ignore
        if not ids:
            raise RuntimeError(f"Failed to update document with id '{id}'.")
        if len(ids) > 1:
            raise RuntimeError(f"Multiple documents updated with id '{id}', expected only one.")
        return data.id

    def delete(self, id: str) -> str:
        """Delete data from the database by id."""
        if self._db is None:
            raise RuntimeError("Database not connected.")

        docs = self._db.search(_search("id", id))
        if not len(docs) == 1:
            raise ValueError(f"Not exactly one document found with id {id}")
        ret = self._db.remove(doc_ids=[doc.doc_id for doc in docs])  # type: ignore
        if not ret:
            raise RuntimeError(f"Failed to delete document with id '{id}'.")
        if len(ret) > 1:
            raise RuntimeError(f"Multiple documents deleted with id '{id}', expected only one.")
        return id

    def search(self, field: str, value: Any) -> List[Metadata]:
        """Search for data in the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        ret = self._db.search(_search(field, value))
        return self._to_metadata(ret)

    def get_by_filename(self, filename: str) -> Optional[Metadata]:
        """Get a single record from the database by filename.
        If multiple records are found with the same filename, a ValueError is raised.
        If no records are found, None is returned."""
        path = Path(filename)
        results = self.search("filename", path.name)
        assert len(results) <= 1, f"Multiple records found with filename '{filename}'"
        if len(results) == 0:
            return None
        data = next(iter(results))
        return data

    def get_by_full_path(self, full_path: str) -> Optional[Metadata]:
        """Get a single record from the database by full path.
        If multiple records are found with the same full path, a ValueError is raised.
        If no records are found, None is returned."""
        path = Path(full_path).resolve()
        results = self.search("full_path", str(path))
        assert len(results) <= 1, f"Multiple records found with full_path '{full_path}'"
        if len(results) == 0:
            return None
        data = next(iter(results))
        return data

    def delete_by_filename(self, filename: str) -> str:
        """Delete a single record by filename."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        ret = self.get_by_filename(filename)
        if ret:
            return self.delete(ret.id)
        else:
            raise ValueError(f"Cannot find record with filename={filename}")

    def all(self) -> List[Metadata]:
        """Get all records from the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        all = self._db.all()
        return self._to_metadata(all)
        # return self._to_metadata(self._db.all())

    def all_dirs(self) -> List[Path]:
        if self._db is None:
            raise RuntimeError("Database not connected.")
        all = self.all()
        dirs: Set[Path] = set()
        for entry in all:
            dirs.add(entry.full_path.parent)
        return list(dirs)

    def len(self) -> int:
        """Get the number of records in the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        return len(self._db)

    def _to_metadata(self, list_of_documents: List[Document] | Document) -> List[Metadata]:
        if isinstance(list_of_documents, Document):
            list_of_documents = [list_of_documents]
        return [Metadata(**doc) for doc in list_of_documents]  # type: ignore

    def _filename_exists_in_db(self, filename: str) -> bool:
        """Check if a filename already exists in the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        return self._db.contains(Query().filename == filename)

    def _get_doc_id_by_id(self, id: str | List[str]) -> List[int] | int | None:
        """Get the document ID for a given record ID."""
        if self._db is None:
            raise RuntimeError("Database not connected.")

        if isinstance(id, list):
            docs = self._db.search(Query()["id"].one_of(id))
            if not docs:
                return None
            return [doc.doc_id for doc in docs]  # pyright: ignore[report

        # id is a single string
        docs = self._db.search(Query()["id"] == id)
        if not docs:
            return None
        if len(docs) > 1:
            raise RuntimeError(f"Multiple documents found with id '{id}', expected only one.")
        return docs[0].doc_id

    # The methods below operate on doc_id, not on id. They are used internally to support operations that require direct access to the underlying TinyDB document IDs.
    def _db_update(self, doc_id: int, data: Metadata) -> int:
        """Update a record or records by their document ID."""
        if self._db is None:
            raise RuntimeError("Database not connected.")

        ids = self._db.update(data.model_dump(mode="json"), doc_ids=[doc_id])  # pyright: ignore[reportUnknownMemberType]
        if not ids:
            raise RuntimeError(f"Failed to update document with doc_id '{doc_id}'.")
        if len(ids) > 1:
            raise RuntimeError(f"Multiple documents updated with doc_id '{doc_id}', expected only one.")
        return ids[0]

    def _db_delete(self, doc_id: int | List[int]) -> int | List[int]:
        """Delete a record or records by their document ID."""
        if self._db is None:
            raise RuntimeError("Database not connected.")

        if isinstance(doc_id, int):
            doc_id = [doc_id]
        if not doc_id:
            return []
        ret = self._db.remove(doc_ids=doc_id)  # type: ignore
        if len(ret) != len(doc_id) or set(ret) != set(doc_id):
            raise RuntimeError(f"Failed to delete all documents with doc_ids '{doc_id}'.")
        return ret

    def _db_get(self, doc_id: int | List[int]) -> Metadata | List[Metadata]:
        """Get a record or records by their document ID."""
        if self._db is None:
            raise RuntimeError("Database not connected.")

        if isinstance(doc_id, list):
            docs = self._db.search(Query().doc_id.one_of(doc_id))
            if len(docs) != len(doc_id):
                raise ValueError(f"Some document IDs not found: {doc_id}")
            if set(doc.doc_id for doc in docs) != set(doc_id):
                raise ValueError(f"Some document IDs not found: {doc_id}")
            return [Metadata(**doc) for doc in docs]  # type: ignore

        doc = self._db.get(doc_id=doc_id)  # type: ignore
        if not doc:
            raise ValueError(f"No document found with doc_id '{doc_id}'.")
        return Metadata(**doc)  # type: ignore

    def __repr__(self):
        return f"Db(path={self.db_path})"


# def main() -> None:
#     db = Db("test_db.json")
#     with db as c:
#         metadata = Metadata(
#             filename="test.jpg", keywords=["nature", "sunset"], description="A beautiful sunset.", title="Sunset"
#         )
#         id = c.insert(metadata)
#         print(f"Inserted record with id: {id}")
#         # print(db.all())
