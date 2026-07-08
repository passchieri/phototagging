import uuid
from copy import copy
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Tuple
from unittest.mock import MagicMock

import pytest

from phototagging.db import Db
from phototagging.metadata import Metadata
from phototagging.metadata_manager import ExternalServiceError, MetadataManager
from phototagging.phototag import PhotoTag, PhotoTagResponse


@pytest.fixture
def db(tmp_path: Path) -> Db:
    db = Db(tmp_path / "test_db.json")
    with db as _db:
        _db._db.drop_tables()  # type: ignore
    return db


def create_mock_db_return_value(
    sample_db_data: Tuple[int, Metadata],
) -> Callable[[str], Optional[Tuple[int, Metadata]]]:
    def get_by_filename(filename: str) -> Optional[Tuple[int, Metadata]]:
        if filename == "non_existing.jpg":
            return None
        return sample_db_data

    return get_by_filename


# @pytest.fixture
# def mock_db(db_data: Tuple[int, Metadata]) -> Db:
#     """Create a mock database with context manager support."""
#     db = MagicMock()
#     db.__enter__ = MagicMock(return_value=db)
#     db.__exit__ = MagicMock(return_value=None)
#     db.get_by_filename.side_effect = create_mock_db_return_value(db_data)
#     data = db_data[1]
#     doc: Dict[str, Any] = {
#         "filename": data.filename,
#         "title": data.title,
#         "description": data.description,
#         "keywords": data.keywords,
#     }
#     ret = MagicMock()
#     ret.model_dump.return_value = doc
#     db.get.return_value = (db_data[0], ret)
#     return db


@pytest.fixture
def mock_phototag(sample_phototag_response: PhotoTagResponse) -> PhotoTag:
    """Create a mock phototagging API."""
    mock = MagicMock()
    mock.fetch_for_file.return_value = sample_phototag_response
    return mock


@pytest.fixture
def metadata_manager(db: Db, mock_phototag: PhotoTag, metadata1: Metadata, metadata2: Metadata):
    """Create a Meta instance with mocked dependencies."""

    metadata_manager = MetadataManager(db, mock_phototag)
    metadata_manager._insert_db(metadata1)  # type: ignore
    metadata_manager._insert_db(metadata2)  # type: ignore
    return metadata_manager


@pytest.fixture
def metadata1() -> Metadata:
    """Create sample metadata for testing."""

    return Metadata(
        id=str(uuid.uuid4()),
        filename="filename.jpg",
        full_path=Path("/just/a/dummy/path/filename.jpg"),
        create_date=datetime.now(),
        keywords=set(["test", "data1", "Capital", "duplicate", "duplicate"]),
        title="The title",
        description="A longer description",
    )


@pytest.fixture
def metadata2() -> Metadata:
    """Create sample metadata for testing."""
    return Metadata(
        id=str(uuid.uuid4()),
        filename="another_image.jpg",
        full_path=Path("/just/a/dummy/path/another_image.jpg"),
        create_date=datetime.now(),
        keywords=set(["test", "another"]),
        title="Another Test Image",
        description="Another Test Image",
    )


@pytest.fixture
def sample_phototag_response(metadata1: Metadata) -> PhotoTagResponse:
    return PhotoTagResponse(
        filename=metadata1.filename,
        id=metadata1.filename,
        description=metadata1.description,
        title=metadata1.title,
        keywords=[kw for kw in metadata1.keywords],
    )


class TestMetaBaseMethods:
    """Test Meta class initialization and other base methods."""

    def test_all(self, metadata_manager: MetadataManager, db: Db, metadata1: Metadata, metadata2: Metadata):
        all = metadata_manager.all()
        assert len(all) == 2
        assert metadata1 in all
        assert metadata2 in all


class TestMetaSearch:
    """Test the search method."""

    def test_search_returns_metadata_list(
        self,
        metadata_manager: MetadataManager,
        metadata1: Metadata,
    ):
        """Test search returns list of Metadata objects."""

        result = metadata_manager.search("filename", metadata1.filename)
        assert len(result) == 1
        assert result[0] == metadata1

    def test_search_empty_result(self, metadata_manager: MetadataManager):
        """Test search with empty results."""

        result = metadata_manager.search("filename", "nonexistent.jpg")
        assert result == []

    def test_search_multiple_results(self, metadata_manager: MetadataManager):
        """Test search with multiple results."""

        result = metadata_manager.search("keywords", "test")
        assert len(result) == 2


class TestMetaGetOrCreate:
    """Test the get_or_create method."""

    def test_get_or_create_from_db(self, metadata_manager: MetadataManager, metadata1: Metadata):
        """Test get_or_create when data exists in database."""

        result = metadata_manager.get_or_create(metadata1.filename)
        assert result == metadata1

    def test_get_or_create_from_api(self, metadata_manager: MetadataManager):
        """Test get_or_create when data is fetched from API."""

        result = metadata_manager.get_or_create("non_existing.jpg")
        assert result is not None, "Metadata should have been created"
        assert result.filename == "non_existing.jpg"

    def test_get_or_create_with_force(self, metadata_manager: MetadataManager):
        """Test get_or_create when data is fetched from API."""

        mock = MagicMock()
        metadata_manager.delete_by_filename = mock  # type: ignore
        result = metadata_manager.get_or_create("test_image.jpg", force=True)
        assert result is not None
        mock.assert_any_call("test_image.jpg")

        # The ValueError should be silently ignored
        mock.side_effect = ValueError()
        result = metadata_manager.get_or_create("test_image.jpg", force=True)
        assert result is not None

    def test_get_or_create_no_data_raises_error(self, metadata_manager: MetadataManager, mock_phototag: PhotoTag):
        """Test get_or_create raises error when no data found."""
        mock_phototag.fetch_for_file.return_value = None  # type: ignore

        with pytest.raises(ExternalServiceError):
            metadata_manager.get_or_create("non_existing.jpg")

    def test_get_or_create_with_default_tags(
        self, metadata_manager: MetadataManager, sample_phototag_response: PhotoTagResponse
    ):
        """Test get_or_create adds default tags."""

        sample_phototag_response["keywords"] = ["existing"]

        result = metadata_manager.get_or_create("non_existing.jpg", required_keywords=["new_tag"])
        # Keywords should be extended with new tags
        assert result is not None
        assert len(result.keywords) == 2
        assert "existing" in result.keywords
        assert "new_tag" in result.keywords

    def test_get_or_create_initializes_keywords_if_none(
        self, metadata_manager: MetadataManager, sample_phototag_response: PhotoTagResponse
    ):
        """Test get_or_create initializes keywords list if None."""
        sample_phototag_response["keywords"] = []

        result = metadata_manager.get_or_create("non_existing.jpg")
        assert result is not None
        assert result.keywords is not None

    def test_get_or_create_with_removed_tags(
        self, metadata_manager: MetadataManager, sample_phototag_response: PhotoTagResponse
    ):
        """Test get_or_create removes specified tags."""
        keywords = copy(sample_phototag_response["keywords"])
        sample_phototag_response["keywords"].append("remove_me")

        result = metadata_manager.get_or_create("non_existing.jpg", keywords_to_remove=["remove_me"])
        assert result is not None
        assert "remove_me" not in result.keywords
        for kw in keywords:
            assert kw in result.keywords


class TestMetaGetById:
    """Test the get_by_id method."""

    def test_get_by_id(self, metadata_manager: MetadataManager, metadata1: Metadata):
        """Test get_by_id when data exists in database."""

        result = metadata_manager.get_by_id(metadata1.id)
        assert result == metadata1

    def test_get_by_id_not_found(self, metadata_manager: MetadataManager, db: Db):
        """Test get_by_id returns None when not found anywhere."""

        with pytest.raises(ValueError):
            metadata_manager.get_by_id("non_existing")
            assert False, "A ValueError should be raised if a non-existing item is requested by id"


class TestMetaGetByFilename:
    """Test the get_by_filename method."""

    def test_get_by_filename_found(self, metadata_manager: MetadataManager, metadata1: Metadata):
        """Test get_by_filename when record exists."""

        result = metadata_manager.get_by_filename(metadata1.filename)
        assert result == metadata1

    def test_get_by_filename_not_found(self, metadata_manager: MetadataManager):
        """Test get_by_filename returns None when not found."""

        result = metadata_manager.get_by_filename("non_existing.jpg")
        assert result is None


class TestMetaFetchForFile:
    """Test the create_for_file method."""

    def test_create_metadata_for_missing_file_uses_fallback_date(self):
        manager = MetadataManager(MagicMock(), MagicMock())

        metadata = manager._create_metadata(  # type: ignore
            full_path=Path("/tmp/does-not-exist.jpg"),
            title="Test",
            description="Test description",
            keywords={"test"},
        )

        assert metadata.filename == "does-not-exist.jpg"
        assert metadata.create_date is not None

    def test_create_for_file_success(self, metadata_manager: MetadataManager):
        """Test create_for_file fetches and stores metadata."""

        result = metadata_manager.create("non_existing.jpg")
        assert result is not None
        assert result.filename == "non_existing.jpg"

    def test_create_for_file_already_exists_raises_error(self, metadata_manager: MetadataManager, metadata1: Metadata):
        """Test create_for_file raises error if file already in database."""

        with pytest.raises(ValueError, match="already exists in the database"):
            metadata_manager.create(metadata1.filename)


class TestMetaUpdateDb:
    """Test the update_db method."""

    def test_update_db_calls_update(self, metadata_manager: MetadataManager, metadata1: Metadata):
        """Test update_db calls database update_or_insert."""

        mock_db = MagicMock()
        mock_db.__enter__.return_value = mock_db
        metadata_manager.db = mock_db
        metadata_manager._update_db(metadata1)  # type: ignore
        mock_db.update.assert_called_once()  # type: ignore


class TestMetaDeleteByFilename:
    """Test the delete_by_filename method."""

    def test_delete_by_filename_calls_delete(self, metadata_manager: MetadataManager, metadata1: Metadata):

        db = MagicMock()
        db.__enter__.return_value = db
        metadata_manager.db = db
        metadata_manager.delete_by_filename("existing.jpg")
        db.delete_by_filename.assert_called_once()  # type: ignore


class TestUpdateKeywords:
    """Test updating keywords for metadata"""

    def test_replace_keywords(self, metadata_manager: MetadataManager, metadata1: Metadata):
        metadata_manager.update_keywords(
            metadata1, keywords=["the", "new", "keywords", "With Capitals", "duplicate", "duplicate"]
        )

        kws = metadata1.keywords
        assert len(kws) == 5
        for kw in ["the", "new", "keywords", "with capitals", "duplicate"]:
            assert kw in kws

    def test_add_keywords(self, metadata_manager: MetadataManager, metadata1: Metadata):
        metadata_manager.update_keywords(
            metadata1, keywords_to_add=["the", "new", "keywords", "With Capitals", "duplicate", "duplicate"]
        )

        kws = metadata1.keywords
        for kw in ["the", "new", "keywords", "with capitals", "duplicate"]:
            assert kw in kws

    def test_remove_keywords(self, metadata_manager: MetadataManager, metadata1: Metadata):
        metadata_manager.update_keywords(
            metadata1,
            keywords_to_remove=["test", "the", "new", "keywords", "With Capitals", "duplicate", "duplicate"],
        )

        kws = metadata1.keywords
        for kw in ["test", "the", "new", "keywords", "with capitals", "duplicate"]:
            assert kw not in kws

    def test_remove_add_keywords(self, metadata_manager: MetadataManager, metadata1: Metadata):
        metadata_manager.update_keywords(
            metadata1,
            keywords_to_remove=["test", "the", "new", "keywords", "With Capitals", "duplicate", "duplicate"],
            keywords_to_add=["add"],
        )

        kws = metadata1.keywords
        for kw in ["test", "the", "new", "keywords", "with capitals", "duplicate"]:
            assert kw not in kws

        assert "add" in kws

    def test_incorrect_input(self, metadata_manager: MetadataManager, metadata1: Metadata):
        with pytest.raises(ValueError):
            metadata_manager.update_keywords(metadata1, keywords_to_add=["add"], keywords=["kws"])

        with pytest.raises(ValueError):
            metadata_manager.update_keywords(metadata1, keywords_to_remove=["remove"], keywords=["kws"])

        with pytest.raises(ValueError):
            metadata_manager.update_keywords(
                metadata1, keywords_to_add=["add"], keywords_to_remove=["remove"], keywords=["kws"]
            )

        # Providing nothing should be okay
        metadata_manager.update_keywords(metadata1)

    def test_update_for_file(self, metadata_manager: MetadataManager, metadata1: Metadata):
        mock = MagicMock()
        metadata_manager.update_keywords = mock  # type:ignore
        metadata_manager.update_keywords_for_file(
            metadata1.filename,
        )
        mock.assert_called_once()

    def test_update_for_file_exception(self, metadata_manager: MetadataManager):
        with pytest.raises(ValueError):
            metadata_manager.update_keywords_for_file("non_existing.jpg", keywords=["kws"])
