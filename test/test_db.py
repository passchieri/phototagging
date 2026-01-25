import pytest
from phototag.db import Db


def test_get_by_filename(tmp_path):
    db = Db(tmp_path / "test_db.json")

    with db:
        assert db._db is not None, "Database instance should not be None"

        # Insert a test record
        test_data = {
            "filename": "test_image.jpg",
            "id": "test_image.jpg",
            "keywords": ["test"],
        }
        db.insert(test_data)

        # Search for the inserted record by filename
        result = db.get_by_filename("test_image.jpg")
        assert result is not None, "Should retrieve the inserted record by filename"
        assert (
            result["id"] == test_data["id"]
        ), "Retrieved record should have correct ID"
        assert (
            result["filename"] == test_data["filename"]
        ), "Retrieved record should have correct filename"

        # Search for the inserted record by filename, but with a different path
        result = db.get_by_filename("arbitrary/path/test_image.jpg")
        assert result is not None, "Should retrieve the inserted record by filename"
        assert (
            result["id"] == test_data["id"]
        ), "Retrieved record should have correct ID"
        assert (
            result["filename"] == test_data["filename"]
        ), "Retrieved record should have correct filename"

        # Search for a non-existent filename
        result = db.get_by_filename("non_existent.jpg")
        assert result is None, "Should return None for non-existent filename"


def test_insert(tmp_path):
    db = Db(tmp_path / "test_db.json")

    with db:
        assert db._db is not None, "Database instance should not be None"

        # Insert a test record
        test_data = {
            "filename": "test_image.jpg",
            "id": "test_image.jpg",
            "keywords": ["test"],
        }
        db.insert(test_data)

        # Verify the record was inserted
        result = db.get_by_filename(test_data["filename"])
        assert result is not None, "Should retrieve the inserted record by filename"

        with pytest.raises(ValueError):
            # Attempt to insert a record with the same ID
            db.insert(test_data)


def test_update(tmp_path):
    db = Db(tmp_path / "test_db.json")

    with db:
        assert db._db is not None, "Database instance should not be None"

        # Insert a test record
        test_data = {
            "filename": "test_image.jpg",
            "id": "test_image.jpg",
            "keywords": ["test"],
        }
        with pytest.raises(ValueError):
            db.update(test_data)

        db.insert(test_data)
        test_data["keywords"].append("updated")
        db.update(test_data)
        # Verify the record was inserted
        result = db.get_by_filename(test_data["filename"])
        assert result is not None, "Should retrieve the inserted record by filename"
        assert result["keywords"] == test_data["keywords"], "Keywords should be updated"


def test_update_or_insert(tmp_path):
    db = Db(tmp_path / "test_db.json")

    with db:
        assert db._db is not None, "Database instance should not be None"

        # Insert a test record
        test_data = {
            "filename": "test_image.jpg",
            "id": "test_image.jpg",
            "keywords": ["test"],
        }
        results = db.search("filename", "test_image.jpg")
        assert len(results) == 0, "No records should exist before insertion"
        db.update_or_insert(test_data)
        results = db.search("filename", "test_image.jpg")
        assert len(results) == 1, "Should have one record after update_or_insert"
        db.update_or_insert(test_data)
        results = db.search("filename", "test_image.jpg")
        assert len(results) == 1, "Should have one record after update_or_insert"


def test_db_operations(tmp_path):
    db = Db(tmp_path / "test_db.json")

    with db:
        assert db._db is not None, "Database instance should not be None"

        # Insert a test record
        test_data = {
            "name": "test",
            "value": 42,
            "id": "dummy.jpg",
            "filename": "dummy.jpg",
        }
        db.insert(test_data)

        # Search for the inserted record
        results = db.search("name", "test")
        assert len(results) == 1
        assert (
            results[0]["value"] == test_data["value"]
        ), "Inserted record should be retrievable"
        assert results[0]["name"] == "test", "Inserted record should have correct name"

        results = db.search("name", "bad")
        assert (
            len(results) == 0
        ), "Search for non-existent record should return empty list"

        assert (
            db.get_by_id(test_data["id"]) == test_data
        ), "Should retrieve the inserted record by ID"
        assert db.get_by_id("bad id") is None, "Should return None for non-existent ID"


def test_db_operations_closed_database(tmp_path):
    db = Db(tmp_path / "test_db.json")
    # Database is not opened, so operations should fail

    # Test insert on closed database
    test_data = {
        "name": "test",
        "value": 42,
        "id": "dummy.jpg",
        "filename": "dummy.jpg",
    }
    with pytest.raises(RuntimeError):
        db.insert(test_data)

    # Test search on closed database
    with pytest.raises(RuntimeError):
        db.search("name", "test")

    # Test get_by_id on closed database
    with pytest.raises(RuntimeError):
        db.get_by_id("dummy.jpg")

    # Test get_by_filename on closed database
    with pytest.raises(RuntimeError):
        db.get_by_filename("dummy.jpg")

    # Test update on closed database
    with pytest.raises(RuntimeError):
        db.update(test_data)

    # Test update_or_insert on closed database
    with pytest.raises(RuntimeError):
        db.update_or_insert(test_data)


def test_db_is_none_after_close(tmp_path):
    db = Db(tmp_path / "test_db.json")
    db.connect()
    assert db._db is not None, "_db should not be None after connect"
    db.close()
    assert db._db is None, "_db should be None after close"


def test_close_without_connect(tmp_path):
    db = Db(tmp_path / "test_db.json")
    # Call close without connecting first
    db.close()
    # Should not raise an error
    assert db._db is None


def test_close_twice(tmp_path):
    """Test closing database twice."""
    db = Db(tmp_path / "test_db.json")
    db.connect()
    db.close()
    # Call close again
    db.close()
    # Should not raise an error
    assert db._db is None


def test_all(tmp_path):
    """Test retrieving all records from the database."""
    db = Db(tmp_path / "test_db.json")

    with db:
        assert db._db is not None, "Database instance should not be None"

        # Insert multiple test records
        test_data_1 = {
            "filename": "test_image_1.jpg",
            "id": "test_image_1.jpg",
            "keywords": ["test", "image1"],
        }
        test_data_2 = {
            "filename": "test_image_2.jpg",
            "id": "test_image_2.jpg",
            "keywords": ["test", "image2"],
        }
        db.insert(test_data_1)
        db.insert(test_data_2)

        # Retrieve all records
        results = db.all()
        assert len(results) == 2, "Should retrieve all inserted records"
        assert test_data_1 in results, "First record should be in results"
        assert test_data_2 in results, "Second record should be in results"

        # Test with no records
        db2 = Db(tmp_path / "empty_db.json")
        with db2:
            results = db2.all()
            assert len(results) == 0, "Should return empty list for empty database"

        # Test with closed database
        db3 = Db(tmp_path / "closed_db.json")
        with pytest.raises(RuntimeError):
            db3.all()


def test_get_by_id(tmp_path):
    """Test retrieving a record by ID from the database."""
    db = Db(tmp_path / "test_db.json")

    with db:
        # Insert a test record
        test_data = {
            "filename": "test_image.jpg",
            "id": "test_image.jpg",
            "keywords": ["test"],
        }
        db.insert(test_data)

        # Retrieve the record by ID
        result = db.get_by_id("test_image.jpg")
        assert result is not None, "Should retrieve the inserted record by ID"
        assert result["id"] == test_data["id"], "Retrieved record should have correct ID"
        assert result["filename"] == test_data["filename"], "Retrieved record should have correct filename"

        # Retrieve a non-existent record by ID
        result = db.get_by_id("non_existent.jpg")
        assert result is None, "Should return None for non-existent ID"


def test_search(tmp_path):
    """Test searching for records in the database."""
    db = Db(tmp_path / "test_db.json")

    with db:
        # Insert test records
        test_data_1 = {
            "filename": "test_image_1.jpg",
            "id": "test_image_1.jpg",
            "keywords": ["test", "image1"],
        }
        test_data_2 = {
            "filename": "test_image_2.jpg",
            "id": "test_image_2.jpg",
            "keywords": ["test", "image2"],
        }
        db.insert(test_data_1)
        db.insert(test_data_2)

        # Search for records with a specific keyword
        results = db.search("keywords", "image1")
        assert len(results) == 1, "Should retrieve one record with the keyword 'image1'"
        assert results[0]["id"] == test_data_1["id"], "Retrieved record should have correct ID"

        # Search for records with a non-existent keyword
        results = db.search("keywords", "non_existent")
        assert len(results) == 0, "Should return empty list for non-existent keyword"
