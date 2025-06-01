import time

import pytest
from phototag.db import Db
import os


def test_get_by_filename():
    current_time_ms = int(time.time() * 1000)
    db_path = f"test_db{current_time_ms}.json"
    try:
        db = Db(db_path)

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
    finally:
        # Clean up the test database file
        if os.path.exists(db_path):
            os.remove(db_path)


def test_insert():
    current_time_ms = int(time.time() * 1000)
    db_path = f"test_db{current_time_ms}.json"
    try:
        db = Db(db_path)

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

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_update():
    current_time_ms = int(time.time() * 1000)
    db_path = f"test_db{current_time_ms}.json"
    try:
        db = Db(db_path)

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
            assert (
                result["keywords"] == test_data["keywords"]
            ), "Keywords should be updated"

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_update_or_insert():
    current_time_ms = int(time.time() * 1000)
    db_path = f"test_db{current_time_ms}.json"
    try:
        db = Db(db_path)

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

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_db_operations():
    current_time_ms = int(time.time() * 1000)
    db_path = f"test_db{current_time_ms}.json"
    try:
        db = Db(db_path)

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
            assert (
                results[0]["name"] == "test"
            ), "Inserted record should have correct name"

            results = db.search("name", "bad")
            assert (
                len(results) == 0
            ), "Search for non-existent record should return empty list"

            assert (
                db.get_by_id(test_data["id"]) == test_data
            ), "Should retrieve the inserted record by ID"
            assert (
                db.get_by_id("bad id") is None
            ), "Should return None for non-existent ID"
    finally:
        # Clean up the test database file
        if os.path.exists(db_path):
            os.remove(db_path)
