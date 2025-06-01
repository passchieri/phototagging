from pathlib import Path
from typing import Any
from tinydb import Query, TinyDB


class Db:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Connect to the database."""
        self._db = TinyDB(self.db_path)

    def close(self):
        """Close the database connection."""
        if self._db:
            self._db.close()
            self._db = None

    def insert(self, data: dict):
        """Insert data into the database."""
        assert "filename" in data, "Data must contain 'filename' key."
        assert "id" in data, "Data must contain 'id' key."
        if self._db is None:
            raise RuntimeError("Database not connected.")
        if self.get_by_id(data["id"]):
            raise ValueError(
                f"Data with id '{data['id']}' already exists in the database."
            )
        self._db.insert(data)

    def update(self, data: dict):
        """Update data in the database."""
        assert "filename" in data, "Data must contain 'filename' key."
        assert "id" in data, "Data must contain 'id' key."
        if self._db is None:
            raise RuntimeError("Database not connected.")
        if not self.get_by_id(data["id"]):
            raise ValueError(f"No record found with id '{data['id']}'.")
        self._db.update(data, Query().id == data["id"])

    def update_or_insert(self, data: dict):
        """Update data in the database or insert it if it doesn't exist."""
        assert "filename" in data, "Data must contain 'filename' key."
        assert "id" in data, "Data must contain 'id' key."
        if self._db is None:
            raise RuntimeError("Database not connected.")
        if self.get_by_id(data["id"]):
            self.update(data)
        else:
            self.insert(data)

    def search(self, field: str, value: Any):
        """Search for data in the database."""
        if self._db is None:
            raise RuntimeError("Database not connected.")
        return self._db.search(Query()[field] == value)

    def get_by_id(self, id: str):
        """Get a single record from the database."""
        results = self.search("id", id)
        return results[0] if results else None

    def get_by_filename(self, filename: str):
        """Get a single record from the database."""
        path = Path(filename)
        results = self.search("id", path.name)
        return results[0] if results else None
