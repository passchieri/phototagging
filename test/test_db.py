import datetime
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from phototagging.db import Db
from phototagging.metadata import Metadata


@pytest.fixture
def test_data_1() -> Metadata:
    return Metadata(
        filename="test_image_1.jpg",
        full_path=Path("/dummy/path/to/file/test_image_1.jpg"),
        keywords={"test", "image1"},
        description="A test image",
        title="Test Image 1",
        create_date=datetime.datetime.now(),
    )


@pytest.fixture
def test_data_2() -> Metadata:
    return Metadata(
        filename="test_image_2.jpg",
        full_path=Path("/dummy/path/to/file/test_image_2.jpg"),
        keywords={"test", "image2"},
        description="Another test image",
        title="Test Image 2",
        create_date=datetime.datetime.now(),
    )


@pytest.fixture
def db(tmp_path: Path) -> Db:
    db = Db(tmp_path / "test_db.json")
    with db as _db:
        _db._db.drop_tables()  # type: ignore
    return db


def test_get(db: Db, test_data_1: Metadata):
    """Test retrieving a record by ID from the database."""

    with db:
        # Insert a test record
        id = db.insert(test_data_1)

        # Retrieve the record by ID
        result = db.get(id)
        assert result == test_data_1, "Should retrieve the inserted record by ID"

        # Retrieve a non-existent record by ID
        with pytest.raises(ValueError):
            _ = db.get(str(uuid.uuid4()))


def test_get_by_filename(db: Db, test_data_1: Metadata):
    with db as c:
        # Insert a test record
        _ = c.insert(test_data_1)

        # Search for the inserted record by filename

        result = c.get_by_filename(test_data_1.filename)
        assert result == test_data_1, "Retrieved record should be identical"

        # Search for a non-existent filename
        result = c.get_by_filename("non_existent.jpg")
        assert result is None, "Should return empty list for non-existent filename"

        # Allow to insert a double entry
        c._db.contains = MagicMock(return_value=False)  # type: ignore
        c.insert(test_data_1)
        with pytest.raises(AssertionError):
            c.get_by_filename(test_data_1.filename)
            assert False, "Double entries for 1 file should result in a AssertionError"


def test_insert(db: Db, test_data_1: Metadata):
    with db:
        # Insert a test record
        id = db.insert(test_data_1)

        # Verify the record was inserted
        result = db.get(id)
        assert result == test_data_1, "Should retrieve the inserted record by filename"

        with pytest.raises(ValueError):
            # Attempt to insert a record with the same filename
            db.insert(test_data_1)


def test_update(db: Db, test_data_1: Metadata):
    with db:
        # Insert a test record

        id = db.insert(test_data_1)
        test_data_1.keywords.add("updated")
        db.update(test_data_1)
        # Verify the record was inserted
        result = db.get(id)
        assert result == test_data_1


def test_update_exceptions(db: Db, test_data_1: Metadata):
    with pytest.raises(ValueError):
        with db as c:
            c.update(test_data_1)

    # Simulate a failed update to the database
    with pytest.raises(RuntimeError):
        with db as c:
            c._db.update = MagicMock(return_value=None)  # type: ignore
            c.get = MagicMock(return_value=(1, test_data_1))  # type: ignore
            c.update(test_data_1)

    with pytest.raises(RuntimeError):
        with db as c:
            c._db.update = MagicMock(return_value=[1, 2])  # type: ignore
            c.get = MagicMock(return_value=(1, test_data_1))  # type: ignore
            c.update(test_data_1)


def test_delete(db: Db, test_data_1: Metadata):

    with db as c:
        with pytest.raises(ValueError):
            c.delete(str(uuid.uuid4()))
            assert False, "Deleting a non-existing record should raise a ValueError"

        id = c.insert(test_data_1)
        ret = c.delete(id)
        assert ret == id
        with pytest.raises(ValueError):
            c.get(id)
            assert False, "A deleted record should not exist anymore"

        id = c.insert(test_data_1)
        c._db.remove = MagicMock(return_value=None)  # type: ignore
        with pytest.raises(RuntimeError):
            c.delete(id)

        c._db.remove = MagicMock(return_value=[1, 2])  # type: ignore
        with pytest.raises(RuntimeError):
            c.delete(id)


def test_delete_by_filename(db: Db, test_data_1: Metadata):
    with db as c:
        id = c.insert(test_data_1)
        ret = c.delete_by_filename(test_data_1.filename)
        assert ret == id
        assert c.len() == 0

        with pytest.raises(ValueError):
            c.delete_by_filename(test_data_1.filename)


def test_db_operations(db: Db, test_data_1: Metadata):
    with db as c:
        # Insert a test record
        c.insert(test_data_1)

        # Search for the inserted record
        results = c.search("filename", test_data_1.filename)
        assert len(results) == 1, "Should retrieve exactly the inserted record by filename"

        assert results[0] == test_data_1, "Should retrieve the original data"

        results = c.search("name", "bad")
        assert len(results) == 0, "Search for non-existent record should return empty list"

        with pytest.raises(ValueError):
            c.get(str(uuid.uuid4()))


def test_filename_exists_in_db(db: Db, test_data_1: Metadata):
    with db as c:
        assert not c._filename_exists_in_db(test_data_1.filename)  # type: ignore
        c.insert(test_data_1)
        assert c._filename_exists_in_db(test_data_1.filename)  # type: ignore


def test_db_operations_closed_database(db: Db, test_data_1: Metadata):
    # Test insert on closed database
    with pytest.raises(RuntimeError):
        db.insert(test_data_1)

    # Test search on closed database
    with pytest.raises(RuntimeError):
        db.search("name", "test")

    # Test get_by_id on closed database
    with pytest.raises(RuntimeError):
        db.get(test_data_1.id)

    # Test get_by_filename on closed database
    with pytest.raises(RuntimeError):
        db.get_by_filename("dummy.jpg")

    # Test update on closed database
    with pytest.raises(RuntimeError):
        db.update(test_data_1)

    # Test delete on closed database
    with pytest.raises(RuntimeError):
        db.delete(test_data_1.id)

    # Test delete_by_filename on closed database
    with pytest.raises(RuntimeError):
        db.delete_by_filename("dummy.jpg")

    # Test len on closed database
    with pytest.raises(RuntimeError):
        db.len()

    with pytest.raises(RuntimeError):
        db._filename_exists_in_db("")  # type: ignore


def test_db_is_none_after_close(db: Db):
    assert db._db is None  # type: ignore
    with db as c:
        assert c._db is not None  # type: ignore
    db.connect()
    assert db._db is not None, "_db should not be None after connect"  # type: ignore
    db.disconnect()
    assert db._db is None, "_db should be None after close"  # type: ignore


def test_close_without_connect(db: Db):
    # Call close without connecting first
    db.disconnect()
    # Should not raise an error
    assert db._db is None  # type: ignore


def test_close_twice(db: Db):
    """Test closing database twice."""
    db.connect()
    db.disconnect()
    # Call close again
    db.disconnect()
    # Should not raise an error
    assert db._db is None  # type: ignore


def test_all(tmp_path: Path, test_data_1: Metadata, test_data_2: Metadata):
    """Test retrieving all records from the database."""
    db = Db(tmp_path / "test_db.json")
    with db:
        id1 = db.insert(test_data_1)
        id2 = db.insert(test_data_2)

        # Retrieve all records
        results = db.all()
        result_ids = [result.id for result in results]
        assert len(results) == 2, "Should retrieve all inserted records"
        assert id1 in result_ids, "First record ID should be in results"
        assert id2 in result_ids, "Second record ID should be in results"
        assert test_data_1 in results, "First record should identically match the inserted data"
        assert test_data_2 in results, "Second record should identically match the inserted data"

        # Test with no records
        db2 = Db(tmp_path / "empty_db.json")
        with db2:
            results = db2.all()
            assert len(results) == 0, "Should return empty list for empty database"

        # Test with closed database
        db3 = Db(tmp_path / "closed_db.json")
        with pytest.raises(RuntimeError):
            db3.all()


def test_search(db: Db, test_data_1: Metadata, test_data_2: Metadata):
    """Test searching for records in the database."""
    with db:
        # Insert test records
        extra_key = str(uuid.uuid4())
        test_data_1.keywords.add(extra_key)

        db.insert(test_data_1)
        db.insert(test_data_2)

        # Search for records with a specific keyword

        results = db.search("keywords", extra_key)
        assert len(results) == 1, "Should retrieve one record with the keyword 'image1'"
        assert results[0] == test_data_1, "Retrieved record should have correct ID"

        # Search for records with a non-existent keyword
        results = db.search("keywords", str(uuid.uuid4()))
        assert len(results) == 0, "Should return empty list for non-existent keyword"

        extra_key = str(uuid.uuid4())
        test_data_1.keywords.add(extra_key)
        test_data_2.keywords.add(extra_key)
        db.update(test_data_1)
        db.update(test_data_2)
        results = db.search("keywords", extra_key)
        assert len(results) == 2, "Should return all matching records"
        assert test_data_1 in results
        assert test_data_1 in results


# def test_to_metadata_dict(db: Db, test_data_1: Metadata, test_data_2: Metadata):
#     with db as c:
#         id = c.insert(test_data_1)
#         doc = c._db.get(doc_id=id)  # type: ignore
#         assert doc is not None
#         ret = c._to_metadata_dict(doc)  # type: ignore
#         assert len(ret) == 1

#         _ = c.insert(test_data_2)
#         docs = c._db.all()  # type: ignore
#         assert len(docs) == 2
#         ret = c._to_metadata_dict(docs)  # type: ignore
#         assert len(ret) == 2
