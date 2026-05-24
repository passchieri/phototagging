from typing import Any, Callable, Dict, Optional, Tuple
from copy import copy

import pytest
from unittest.mock import MagicMock

from sortedcontainers import SortedSet
from phototag.db import Db, DbMetadata
from phototag.metadata_manager import ExternalServiceError, MetadataManager
from phototag.metadata import MetaData
from phototag.phototag import PhotoTag, PhotoTagResponse


def create_mock_db_return_value(
    sample_db_data: Tuple[int, DbMetadata],
) -> Callable[[str], Optional[Tuple[int, DbMetadata]]]:
    def get_by_filename(filename: str) -> Optional[Tuple[int, DbMetadata]]:
        if filename == "non_existing.jpg":
            return None
        return sample_db_data

    return get_by_filename


@pytest.fixture
def mock_db(sample_db_data: Tuple[int, DbMetadata]) -> Db:
    """Create a mock database with context manager support."""
    db = MagicMock()
    db.__enter__ = MagicMock(return_value=db)
    db.__exit__ = MagicMock(return_value=None)
    db.get_by_filename.side_effect = create_mock_db_return_value(sample_db_data)
    data = sample_db_data[1]
    doc: Dict[str, Any] = {
        "filename": data.filename,
        "title": data.title,
        "description": data.description,
        "keywords": data.keywords,
    }
    ret = MagicMock()
    ret.model_dump.return_value = doc
    db.get.return_value = (sample_db_data[0], ret)
    return db


@pytest.fixture
def mock_phototag(sample_phototag_response: PhotoTagResponse) -> PhotoTag:
    """Create a mock PhotoTag API."""
    mock = MagicMock()
    mock.fetch_for_file.return_value = sample_phototag_response
    return mock


@pytest.fixture
def metadata_manager(mock_db: Db, mock_phototag: PhotoTag):  # type: ignore
    """Create a Meta instance with mocked dependencies."""
    return MetadataManager(mock_db, mock_phototag)


@pytest.fixture
def sample_metadata1() -> MetaData:
    """Create sample metadata for testing."""
    return MetaData(
        id=99,
        filename="test_image.jpg",
        keywords=SortedSet(["test", "image"]),
        title="Test Image",
        description="A test image",
    )


@pytest.fixture
def sample_metadata2() -> MetaData:
    """Create sample metadata for testing."""
    return MetaData(
        id=98,
        filename="another_image.jpg",
        keywords=SortedSet(["test", "another"]),
        title="Another Test Image",
        description="Another test image",
    )


@pytest.fixture
def sample_db_data(sample_metadata1: MetaData) -> Tuple[int, DbMetadata]:
    return sample_metadata1.to_db_metadata()


@pytest.fixture
def sample_phototag_response(sample_metadata1: MetaData) -> PhotoTagResponse:
    return PhotoTagResponse(
        filename=sample_metadata1.filename,
        id=sample_metadata1.filename,
        description=sample_metadata1.description,
        title=sample_metadata1.title,
        keywords=[kw for kw in sample_metadata1.keywords],
    )


class TestMetaBaseMethods:
    """Test Meta class initialization and other base methods."""

    def test_init_with_db_and_phototag(self, mock_db: Db, mock_phototag: PhotoTag):
        """Test Meta initialization."""
        meta = MetadataManager(mock_db, mock_phototag)
        assert meta.db is mock_db
        assert meta.phototag is mock_phototag

    def test_all(
        self, metadata_manager: MetadataManager, mock_db: Db, sample_metadata1: MetaData, sample_metadata2: MetaData
    ):
        mock_db.all.return_value = {  # type: ignore
            sample_metadata1.id: sample_metadata1.to_db_metadata()[1],
            sample_metadata2.id: sample_metadata2.to_db_metadata()[1],
        }
        all = metadata_manager.all()
        assert len(all) == 2
        assert sample_metadata1 in all


class TestMetaSearch:
    """Test the search method."""

    def test_search_returns_metadata_list(
        self,
        metadata_manager: MetadataManager,
        mock_db: Db,
        sample_db_data: Tuple[int, DbMetadata],
        sample_metadata1: MetaData,
    ):
        """Test search returns list of MetaData objects."""
        mock_db.search.return_value = {sample_db_data[0]: sample_db_data[1]}  # type: ignore

        result = metadata_manager.search("filename", sample_db_data[1].filename)
        assert len(result) == 1
        assert result[0] == sample_metadata1

    def test_search_empty_result(self, metadata_manager: MetadataManager, mock_db: Db):
        """Test search with empty results."""

        mock_db.search.return_value = {}  # type: ignore

        result = metadata_manager.search("filename", "nonexistent.jpg")
        assert result == []

    def test_search_multiple_results(self, metadata_manager: MetadataManager, mock_db: Db):
        """Test search with multiple results."""

        metadata1 = DbMetadata(filename="aap.jpg", keywords=["test", "aap"])
        metadata2 = DbMetadata(filename="noot.jpg", keywords=["test", "noot"])

        mock_db.search.return_value = {1: metadata1, 2: metadata2}  # type: ignore

        result = metadata_manager.search("keywords", "test")
        assert len(result) == 2


class TestMetaGetOrCreate:
    """Test the get_or_create method."""

    def test_get_or_create_from_db(self, metadata_manager: MetadataManager, sample_metadata1: MetaData):
        """Test get_or_create when data exists in database."""

        result = metadata_manager.get_or_create(sample_metadata1.filename)
        assert result == sample_metadata1

    def test_get_or_create_from_api(self, metadata_manager: MetadataManager):
        """Test get_or_create when data is fetched from API."""

        result = metadata_manager.get_or_create("non_existing.jpg")
        assert result is not None, "MetaData should have been created"
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

        result = metadata_manager.get_or_create("non_existing.jpg", default_keywords=["new_tag"])
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

    def test_get_by_id(self, metadata_manager: MetadataManager, sample_metadata1: MetaData):
        """Test get_by_id when data exists in database."""

        result = metadata_manager.get_by_id(sample_metadata1.id)
        assert result == sample_metadata1

    def test_get_by_id_not_found(self, metadata_manager: MetadataManager, mock_db: Db):
        """Test get_by_id returns None when not found anywhere."""

        mock_db.get.return_value = None  # type: ignore
        with pytest.raises(ValueError):
            metadata_manager.get_by_id(1)
            assert False, "A ValueError should be raised if a non-existing item is requested by id"


class TestMetaGetByFilename:
    """Test the get_by_filename method."""

    def test_get_by_filename_found(self, metadata_manager: MetadataManager, sample_metadata1: MetaData):
        """Test get_by_filename when record exists."""

        result = metadata_manager.get_by_filename(sample_metadata1.filename)
        assert result == sample_metadata1

    def test_get_by_filename_not_found(self, metadata_manager: MetadataManager):
        """Test get_by_filename returns None when not found."""

        result = metadata_manager.get_by_filename("non_existing.jpg")
        assert result is None


class TestMetaFetchForFile:
    """Test the create_for_file method."""

    def test_create_for_file_success(self, metadata_manager: MetadataManager):
        """Test create_for_file fetches and stores metadata."""

        result = metadata_manager.create("non_existing.jpg")
        assert result is not None
        assert result.filename == "non_existing.jpg"

    def test_create_for_file_already_exists_raises_error(
        self, metadata_manager: MetadataManager, sample_metadata1: MetaData
    ):
        """Test create_for_file raises error if file already in database."""

        with pytest.raises(ValueError, match="already exists in the database"):
            metadata_manager.create(sample_metadata1.filename)


class TestMetaUpdateDb:
    """Test the update_db method."""

    def test_update_db_calls_update(self, metadata_manager: MetadataManager, mock_db: Db, sample_metadata1: MetaData):
        """Test update_db calls database update_or_insert."""

        result = metadata_manager._update_db(sample_metadata1)  # type: ignore
        mock_db.update.assert_called_once()  # type: ignore
        assert result == sample_metadata1


class TestMetaDeleteByFilename:
    """Test the delete_by_filename method."""

    def test_delete_by_filename_calls_delete(self, metadata_manager: MetadataManager, mock_db: Db):

        metadata_manager.delete_by_filename("existing.jpg")
        mock_db.delete.assert_called_once()  # type: ignore

        with pytest.raises(ValueError):
            metadata_manager.delete_by_filename("non_existing.jpg")
            assert False, "Deleting metdata for a non-existing file should raise a ValueError"


class TestUpdateKeywords:
    """Test updating keywords for metadata"""

    def test_replace_keywords(self, metadata_manager: MetadataManager, sample_metadata1: MetaData):
        metadata_manager.update_keywords(
            sample_metadata1, keywords=["the", "new", "keywords", "With Capitals", "duplicate", "duplicate"]
        )

        kws = sample_metadata1.keywords
        assert len(kws) == 5
        for kw in ["the", "new", "keywords", "with capitals", "duplicate"]:
            assert kw in kws

    def test_add_keywords(self, metadata_manager: MetadataManager, sample_metadata1: MetaData):
        metadata_manager.update_keywords(
            sample_metadata1, keywords_to_add=["the", "new", "keywords", "With Capitals", "duplicate", "duplicate"]
        )

        kws = sample_metadata1.keywords
        for kw in ["the", "new", "keywords", "with capitals", "duplicate"]:
            assert kw in kws

    def test_remove_keywords(self, metadata_manager: MetadataManager, sample_metadata1: MetaData):
        metadata_manager.update_keywords(
            sample_metadata1,
            keywords_to_remove=["test", "the", "new", "keywords", "With Capitals", "duplicate", "duplicate"],
        )

        kws = sample_metadata1.keywords
        for kw in ["test", "the", "new", "keywords", "with capitals", "duplicate"]:
            assert kw not in kws

    def test_remove_add_keywords(self, metadata_manager: MetadataManager, sample_metadata1: MetaData):
        metadata_manager.update_keywords(
            sample_metadata1,
            keywords_to_remove=["test", "the", "new", "keywords", "With Capitals", "duplicate", "duplicate"],
            keywords_to_add=["add"],
        )

        kws = sample_metadata1.keywords
        for kw in ["test", "the", "new", "keywords", "with capitals", "duplicate"]:
            assert kw not in kws

        assert "add" in kws

    def test_incorrect_input(self, metadata_manager: MetadataManager, sample_metadata1: MetaData):
        with pytest.raises(ValueError):
            metadata_manager.update_keywords(sample_metadata1, keywords_to_add=["add"], keywords=["kws"])

        with pytest.raises(ValueError):
            metadata_manager.update_keywords(sample_metadata1, keywords_to_remove=["remove"], keywords=["kws"])

        with pytest.raises(ValueError):
            metadata_manager.update_keywords(
                sample_metadata1, keywords_to_add=["add"], keywords_to_remove=["remove"], keywords=["kws"]
            )

        # Providing nothing should be okay
        metadata_manager.update_keywords(sample_metadata1)

    def test_update_for_file(self, metadata_manager: MetadataManager, sample_metadata1: MetaData):
        mock=MagicMock()
        metadata_manager.update_keywords = mock #type:ignore
        metadata_manager.update_keywords_for_file(
            sample_metadata1.filename,
        )
        mock.assert_called_once()

    def test_update_for_file_exception(self, metadata_manager:MetadataManager):
        with pytest.raises(ValueError):
            metadata_manager.update_keywords_for_file("non_existing.jpg", keywords=["kws"])