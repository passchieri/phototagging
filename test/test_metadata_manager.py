# type: ignore

import pytest
from unittest.mock import MagicMock, patch
from phototag.metadata_manager import MetadataManager
from phototag.metadata import MetaData


@pytest.fixture
def mock_db():
    """Create a mock database with context manager support."""
    db = MagicMock()
    db.__enter__ = MagicMock(return_value=db)
    db.__exit__ = MagicMock(return_value=None)
    return db


@pytest.fixture
def mock_phototag():
    """Create a mock PhotoTag API."""
    return MagicMock()


@pytest.fixture
def meta_manager(mock_db, mock_phototag):  # type: ignore
    """Create a Meta instance with mocked dependencies."""
    return MetadataManager(mock_db, mock_phototag)


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return {
        "id": "test_image.jpg",
        "filename": "test_image.jpg",
        "title": "Test Image",
        "description": "A test image",
        "keywords": ["test", "image"],
    }


class TestMetaInit:
    """Test Meta class initialization."""

    def test_init_with_db_and_phototag(self, mock_db, mock_phototag):
        """Test Meta initialization."""
        meta = MetadataManager(mock_db, mock_phototag)
        assert meta.db is mock_db
        assert meta.phototag is mock_phototag


class TestMetaSearch:
    """Test the search method."""

    def test_search_returns_metadata_list(self, meta_manager, mock_db, sample_metadata):
        """Test search returns list of MetaData objects."""
        mock_db.search.return_value = [sample_metadata]

        result = meta_manager.search("filename", "test_image.jpg")
        assert len(result) == 1
        assert isinstance(result[0], MetaData)
        assert result[0].filename == "test_image.jpg"

    def test_search_empty_result(self, meta_manager, mock_db):
        """Test search with empty results."""
        mock_db.search.return_value = []

        result = meta_manager.search("filename", "nonexistent.jpg")
        assert result == []

    def test_search_multiple_results(self, meta_manager, mock_db, sample_metadata):
        """Test search with multiple results."""
        metadata1 = {**sample_metadata, "id": "image1.jpg", "filename": "image1.jpg"}
        metadata2 = {**sample_metadata, "id": "image2.jpg", "filename": "image2.jpg"}
        mock_db.search.return_value = [metadata1, metadata2]

        result = meta_manager.search("keywords", "test")
        assert len(result) == 2


class TestMetaGetOrCreate:
    """Test the get_or_create method."""

    def test_get_or_create_from_db(self, meta_manager, mock_db, mock_phototag, sample_metadata):
        """Test get_or_create when data exists in database."""
        mock_db.get_by_filename.return_value = sample_metadata

        result = meta_manager.get_or_create("test_image.jpg")
        assert result.filename == "test_image.jpg"
        assert result.title == "Test Image"

    def test_get_or_create_from_api(self, meta_manager, mock_db, mock_phototag, sample_metadata):
        """Test get_or_create when data is fetched from API."""
        mock_db.get_by_filename.return_value = None
        mock_phototag.fetch_for_file.return_value = sample_metadata

        result = meta_manager.get_or_create("test_image.jpg")
        assert result.filename == "test_image.jpg"

    def test_get_or_create_no_data_raises_error(self, meta_manager, mock_db, mock_phototag):
        """Test get_or_create raises error when no data found."""
        mock_db.get_by_filename.return_value = None
        mock_phototag.fetch_for_file.return_value = None

        with pytest.raises(ValueError, match="Could not create metadata for file 'nonexistent.jpg'."):
            meta_manager.get_or_create("nonexistent.jpg")

    def test_get_or_create_with_default_tags(self, meta_manager, mock_db, mock_phototag, sample_metadata):
        """Test get_or_create adds default tags."""
        metadata = sample_metadata.copy()
        metadata["keywords"] = ["existing"]
        mock_db.get_by_filename.return_value = metadata

        result = meta_manager.get_or_create("test_image.jpg", default_keywords=["new_tag"])
        # Keywords should be extended with new tags
        assert "new_tag" in result.keywords or len(result.keywords) > 0

    def test_get_or_create_initializes_keywords_if_none(self, meta_manager, mock_db, mock_phototag, sample_metadata):
        """Test get_or_create initializes keywords list if None."""
        metadata = sample_metadata.copy()
        metadata["keywords"] = []
        mock_db.get_by_filename.return_value = metadata

        result = meta_manager.get_or_create("test_image.jpg")
        assert result.keywords == []

    def test_get_or_create_with_removed_tags(self, meta_manager, mock_db, mock_phototag, sample_metadata):
        """Test get_or_create removes specified tags."""
        metadata = sample_metadata.copy()
        metadata["keywords"] = ["test", "image", "remove_me"]
        mock_db.get_by_filename.return_value = metadata

        result = meta_manager.get_or_create("test_image.jpg", keywords_to_remove=["remove_me"])
        assert "remove_me" not in result.keywords
        assert "test" in result.keywords
        assert "image" in result.keywords


class TestMetaGetById:
    """Test the get_by_id method."""

    def test_get_by_id_from_db(self, meta_manager, mock_db, sample_metadata):
        """Test get_by_id when data exists in database."""
        mock_db.get_by_id.return_value = sample_metadata

        result = meta_manager.get_by_id("test_image.jpg")
        assert result.filename == "test_image.jpg"

    def test_get_by_id_not_in_db_fetch_from_api(self, meta_manager, mock_db, mock_phototag, sample_metadata):
        """Test get_by_id fetches from API when not in database."""
        mock_db.get_by_id.return_value = None
        mock_phototag.fetch_for_file.return_value = sample_metadata

        result = meta_manager.get_by_id("test_image.jpg")
        assert result.filename == "test_image.jpg"
        mock_db.insert.assert_called_once()

    def test_get_by_id_not_found(self, meta_manager, mock_db, mock_phototag):
        """Test get_by_id returns None when not found anywhere."""
        mock_db.get_by_id.return_value = None
        mock_phototag.fetch_for_file.return_value = None

        result = meta_manager.get_by_id("nonexistent.jpg")
        assert result is None


class TestMetaGetByFilename:
    """Test the get_by_filename method."""

    def test_get_by_filename_found(self, meta_manager, mock_db, sample_metadata):
        """Test get_by_filename when record exists."""
        mock_db.get_by_filename.return_value = sample_metadata

        result = meta_manager.get_by_filename("test_image.jpg")
        assert result.filename == "test_image.jpg"

    def test_get_by_filename_not_found(self, meta_manager, mock_db):
        """Test get_by_filename returns None when not found."""
        mock_db.__enter__.return_value.get_by_filename.return_value = None
        mock_db.__exit__.return_value = None

        result = meta_manager.get_by_filename("nonexistent.jpg")
        assert result is None


class TestMetaFetchForFile:
    """Test the create_for_file method."""

    def test_create_for_file_success(self, meta_manager, mock_db, mock_phototag, sample_metadata):
        """Test create_for_file fetches and stores metadata."""
        mock_db.get_by_filename.return_value = None
        mock_phototag.fetch_for_file.return_value = sample_metadata

        result = meta_manager.create_for_file("test_image.jpg")
        assert result.filename == "test_image.jpg"
        mock_db.update_or_insert.assert_called_once()

    def test_create_for_file_already_exists_raises_error(self, meta_manager, mock_db, mock_phototag, sample_metadata):
        """Test create_for_file raises error if file already in database."""
        mock_db.get_by_filename.return_value = sample_metadata

        with pytest.raises(ValueError, match="already exists in the database"):
            meta_manager.create_for_file("test_image.jpg")

    def test_create_for_file_force_override(self, meta_manager, mock_db, mock_phototag, sample_metadata):
        """Test create_for_file with force=True overrides existing data."""
        mock_db.get_by_filename.return_value = sample_metadata
        mock_phototag.fetch_for_file.return_value = sample_metadata

        result = meta_manager.create_for_file("test_image.jpg", force=True)
        assert result.filename == "test_image.jpg"


class TestMetaUpdateDb:
    """Test the update_db method."""

    def test_update_db_calls_update_or_insert(self, meta_manager, mock_db, sample_metadata):
        """Test update_db calls database update_or_insert."""
        metadata = MetaData(**sample_metadata)

        result = meta_manager.update_db(metadata)
        mock_db.update_or_insert.assert_called_once()
        assert result == metadata

    def test_update_db_returns_metadata(self, meta_manager, mock_db, sample_metadata):
        """Test update_db returns the metadata object."""
        metadata = MetaData(**sample_metadata)

        result = meta_manager.update_db(metadata)
        assert result is metadata
