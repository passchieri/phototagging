from pathlib import Path
from unittest.mock import MagicMock

import pytest
from phototag.db import Db, DbMetadata, DbMetadataPatch
from pydantic import ValidationError


@pytest.fixture
def test_data_1() -> DbMetadata:
    return DbMetadata(
        filename="test_image_1.jpg",
        full_path="/dummy/path/to/file/test_image_1.jpg",
        keywords=["test", "image1"],
        description="A test image",
        title="Test Image 1",
    )


@pytest.fixture
def test_data_2() -> DbMetadata:
    return DbMetadata(
        filename="test_image_2.jpg",
        full_path="/dummy/path/to/file/test_image_2.jpg",
        keywords=["test", "image2"],
        description="Another test image",
        title="Test Image 2",
    )


@pytest.fixture
def db(tmp_path: Path) -> Db:
    return Db(tmp_path / "test_db.json")


def test_get(db: Db, test_data_1: DbMetadata):
    """Test retrieving a record by ID from the database."""

    with db:
        # Insert a test record
        id = db.insert(test_data_1)

        # Retrieve the record by ID
        retid, result = db.get(id)
        assert id == retid, "Should retrieve the correct record by ID"
        assert result == test_data_1, "Should retrieve the inserted record by ID"

        # Retrieve a non-existent record by ID
        with pytest.raises(ValueError):
            id, result = db.get(id + 1)


def test_get_by_filename(db: Db, test_data_1: DbMetadata):
    with db as c:

        # Insert a test record
        _ = c.insert(test_data_1)

        # Search for the inserted record by filename

        result = c.get_by_filename(test_data_1.filename)
        assert result is not None, "Should retrieve exactly the inserted record by filename"
        assert result[1] == test_data_1, "Retrieved record should be identical"

        # Search for a non-existent filename
        result = c.get_by_filename("non_existent.jpg")
        assert result is None, "Should return empty list for non-existent filename"

        # Allow to insert a double entry
        c._filename_exists_in_db = MagicMock(return_value=False)  # type: ignore
        c.insert(test_data_1)
        with pytest.raises(AssertionError):
            c.get_by_filename(test_data_1.filename)
            assert False, "Double entries for 1 file should result in a AssertionError"


def test_insert(db: Db, test_data_1: DbMetadata):
    with db:

        # Insert a test record
        id = db.insert(test_data_1)

        # Verify the record was inserted
        id, result = db.get(id)
        assert result == test_data_1, "Should retrieve the inserted record by filename"

        with pytest.raises(ValueError):
            # Attempt to insert a record with the same filename
            db.insert(test_data_1)


def test_update(db: Db, test_data_1: DbMetadata):
    with db:

        # Insert a test record

        id = db.insert(test_data_1)
        test_data_1.keywords.append("updated")
        db.update(id, test_data_1)
        # Verify the record was inserted
        id, result = db.get(id)
        assert result is not None, "Should retrieve the inserted record by filename"
        assert result.keywords == test_data_1.keywords, "Keywords should be updated"


def test_update_exceptions(db: Db, test_data_1: DbMetadata):
    with pytest.raises(ValueError):
        with db as c:
            c.update(1, test_data_1)

    # Simulate a failed update to the database
    with pytest.raises(RuntimeError):
        with db as c:
            c._db.update = MagicMock(return_value=None)  # type: ignore
            c.get = MagicMock(return_value=(1, test_data_1))  # type: ignore
            c.update(1, test_data_1)

    with pytest.raises(RuntimeError):
        with db as c:
            c._db.update = MagicMock(return_value=[1, 2])  # type: ignore
            c.get = MagicMock(return_value=(1, test_data_1))  # type: ignore
            c.update(1, test_data_1)


def test_patch(db: Db, test_data_1: DbMetadata):
    patch_data = DbMetadataPatch(keywords=["new", "set", "of", "keywords"])
    # patch without opening
    with pytest.raises(RuntimeError):
        db.patch(1, patch_data)

    with db as c:
        assert db._db is not None, "Database instance should not be None"  # type: ignore

        # patch without inserting
        with pytest.raises(ValueError):
            c.patch(1, patch_data)
            assert False, "Patching an non-existing entry should raise a ValueError"

        # Insert a test record
        id = c.insert(test_data_1)
        c.patch(id, patch_data)
        # Verify the record was inserted
        retid, result = db.get(id)
        assert result is not None, "Patching should not remove the record"
        assert result.keywords == patch_data.keywords, "Keywords should be updated"
        assert result.filename == test_data_1.filename, "Filename should not have been updated"
        assert result.description == test_data_1.description, "Description should not have been updated"
        assert result.title == test_data_1.title, "Title should not been updated"
        assert db.len() == 1, "Number of records should not change during patch"

        patch_data = DbMetadataPatch(**test_data_1.model_dump())
        c.patch(id, patch_data)
        retid, result = c.get(id)
        assert id == retid, "Patching should leave the doc_id unchanged"
        assert result == test_data_1, "Patching with all data set should result in an identical record"


def test_patch_exceptions(db: Db, test_data_1: DbMetadata):
    patch_data = DbMetadataPatch(**test_data_1.model_dump())

    # Simulate a failed patch to the database
    with db as c:
        c.get = MagicMock(return_value=(1, test_data_1))  # type: ignore
        with pytest.raises(RuntimeError):
            c._db.update = MagicMock(return_value=None)  # type: ignore
            c.patch(1, patch_data)

        with pytest.raises(RuntimeError):
            c._db.update = MagicMock(return_value=[1, 2])  # type: ignore
            c.patch(1, patch_data)


def test_delete(db: Db, test_data_1: DbMetadata):

    with db as c:
        with pytest.raises(ValueError):
            c.delete(1)
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

def test_delete_by_filename(db:Db, test_data_1:DbMetadata):
    with db as c:
        id=c.insert(test_data_1)
        ret=c.delete_by_filename(test_data_1.filename)
        assert ret ==id
        assert c.len()==0

        ret=c.delete_by_filename(test_data_1.filename)
        assert ret is None


def test_db_operations(db: Db, test_data_1: DbMetadata):
    with db as c:
        # Insert a test record
        id = c.insert(test_data_1)

        # Search for the inserted record
        results = c.search("filename", test_data_1.filename)
        assert len(results) == 1, "Should retrieve exactly the inserted record by filename"

        assert results[id] == test_data_1, "Should retrieve the original data"

        results = c.search("name", "bad")
        assert len(results) == 0, "Search for non-existent record should return empty list"

        with pytest.raises(ValueError):
            c.get(id + 1)

def test_filename_exists_in_db(db:Db,test_data_1:DbMetadata):
    with db as c:
        assert c._filename_exists_in_db(test_data_1.filename) ==False # type: ignore
        c.insert(test_data_1)
        assert c._filename_exists_in_db(test_data_1.filename) == True # type: ignore

def test_db_operations_closed_database(db: Db, test_data_1: DbMetadata):
    # Test insert on closed database
    with pytest.raises(RuntimeError):
        db.insert(test_data_1)

    # Test search on closed database
    with pytest.raises(RuntimeError):
        db.search("name", "test")

    # Test get_by_id on closed database
    with pytest.raises(RuntimeError):
        db.get(1)

    # Test get_by_filename on closed database
    with pytest.raises(RuntimeError):
        db.get_by_filename("dummy.jpg")

    # Test update on closed database
    with pytest.raises(RuntimeError):
        db.update(1, test_data_1)

    # Test delete on closed database
    with pytest.raises(RuntimeError):
        db.delete(1)

    # Test delete_by_filename on closed database
    with pytest.raises(RuntimeError):
        db.delete_by_filename("dummy.jpg")

    # Test len on closed database
    with pytest.raises(RuntimeError):
        db.len()

    with pytest.raises(RuntimeError):
        db._filename_exists_in_db("") # type: ignore


def test_db_is_none_after_close(db: Db):
    assert db._db is None # type: ignore
    with db as c:
        assert c._db is not None # type: ignore
    db.connect()
    assert db._db is not None, "_db should not be None after connect"  # type: ignore
    db.close()
    assert db._db is None, "_db should be None after close"  # type: ignore


def test_close_without_connect(db: Db):
    # Call close without connecting first
    db.close()
    # Should not raise an error
    assert db._db is None  # type: ignore


def test_close_twice(db: Db):
    """Test closing database twice."""
    db.connect()
    db.close()
    # Call close again
    db.close()
    # Should not raise an error
    assert db._db is None  # type: ignore


def test_all(tmp_path: Path, test_data_1: DbMetadata, test_data_2: DbMetadata):
    """Test retrieving all records from the database."""
    db = Db(tmp_path / "test_db.json")
    with db:
        id1 = db.insert(test_data_1)
        id2 = db.insert(test_data_2)

        # Retrieve all records
        results = db.all()
        assert len(results) == 2, "Should retrieve all inserted records"
        assert id1 in results, "First record ID should be in results"
        assert id2 in results, "Second record ID should be in results"
        assert test_data_1 == results[id1], "First record should identically match the inserted data"
        assert test_data_2 == results[id2], "Second record should identically match the inserted data"

        # Test with no records
        db2 = Db(tmp_path / "empty_db.json")
        with db2:
            results = db2.all()
            assert len(results) == 0, "Should return empty list for empty database"

        # Test with closed database
        db3 = Db(tmp_path / "closed_db.json")
        with pytest.raises(RuntimeError):
            db3.all()


def test_search(db: Db, test_data_1: DbMetadata, test_data_2: DbMetadata):
    """Test searching for records in the database."""
    with db:
        # Insert test records
        id1 = db.insert(test_data_1)
        id2 = db.insert(test_data_2)

        # Search for records with a specific keyword
        results = db.search("keywords", test_data_1.keywords[-1])
        assert len(results) == 1, "Should retrieve one record with the keyword 'image1'"
        assert results[id1] == test_data_1, "Retrieved record should have correct ID"

        # Search for records with a non-existent keyword
        results = db.search("keywords", "non_existent")
        assert len(results) == 0, "Should return empty list for non-existent keyword"

        NEW_KEY = "a new unique key"
        test_data_1.keywords.append(NEW_KEY)
        test_data_2.keywords.append(NEW_KEY)
        db.update(id1, test_data_1)
        db.update(id2, test_data_2)
        results = db.search("keywords", NEW_KEY)
        assert len(results) == 2, "Should return all matching recors"
        assert id1 in results
        assert id2 in results


def test_db_metadata_patch():

    result = DbMetadataPatch()
    assert result, "All values missing should be okay"

    result = DbMetadataPatch(filename="", keywords=[], description=None)
    assert result, "All values missing should be okay"

    with pytest.raises(ValidationError):
        result = DbMetadataPatch(keywords="invalid")  # type: ignore

    with pytest.raises(ValidationError):
        result = DbMetadataPatch(filename=Path("real.path.jpg"))  # type: ignore

def test_to_metadata_dict(db:Db,test_data_1:DbMetadata,test_data_2:DbMetadata):
    with db as c:
        id=c.insert(test_data_1)
        doc = c._db.get(doc_id=id) # type: ignore
        assert doc is not None
        ret=c._to_metadata_dict(doc)  # type: ignore
        assert len(ret)==1

        _=c.insert(test_data_2)
        docs=c._db.all() # type: ignore
        assert len(docs) ==2
        ret=c._to_metadata_dict(docs) # type: ignore
        assert len(ret)==2
        
