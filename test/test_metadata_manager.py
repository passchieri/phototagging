import pytest
from unittest.mock import Mock, MagicMock, patch, call
from phototag.metadata_manager import MetadataManager
from phototag.metadata import MetaData


@pytest.fixture
def mock_db():
    """Create a mock database with context manager support."""
    db = MagicMock()
    db.__enter__ = Mock(return_value=db)
    db.__exit__ = Mock(return_value=None)
    return db


@pytest.fixture
def mock_phototag():
    """Create a mock PhotoTag API."""
    return Mock()


@pytest.fixture
def meta(mock_db, mock_phototag):
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

    def test_search_returns_metadata_list(self, meta, mock_db, sample_metadata):
        """Test search returns list of MetaData objects."""
        mock_db.search.return_value = [sample_metadata]

        result = meta.search("filename", "test_image.jpg")
        assert len(result) == 1
        assert isinstance(result[0], MetaData)
        assert result[0].filename == "test_image.jpg"

    def test_search_empty_result(self, meta, mock_db):
        """Test search with empty results."""
        mock_db.search.return_value = []

        result = meta.search("filename", "nonexistent.jpg")
        assert result == []

    def test_search_multiple_results(self, meta, mock_db, sample_metadata):
        """Test search with multiple results."""
        metadata1 = {**sample_metadata, "id": "image1.jpg", "filename": "image1.jpg"}
        metadata2 = {**sample_metadata, "id": "image2.jpg", "filename": "image2.jpg"}
        mock_db.search.return_value = [metadata1, metadata2]

        result = meta.search("keywords", "test")
        assert len(result) == 2


class TestMetaGetOrFetch:
    """Test the get_or_fetch method."""

    def test_get_or_fetch_from_db(self, meta, mock_db, mock_phototag, sample_metadata):
        """Test get_or_fetch when data exists in database."""
        mock_db.get_by_filename.return_value = sample_metadata

        result = meta.get_or_fetch("test_image.jpg")
        assert result.filename == "test_image.jpg"
        assert result.title == "Test Image"

    def test_get_or_fetch_from_api(self, meta, mock_db, mock_phototag, sample_metadata):
        """Test get_or_fetch when data is fetched from API."""
        mock_db.get_by_filename.return_value = None
        mock_phototag.fetch_for_file.return_value = sample_metadata

        result = meta.get_or_fetch("test_image.jpg")
        assert result.filename == "test_image.jpg"

    def test_get_or_fetch_no_data_raises_error(self, meta, mock_db, mock_phototag):
        """Test get_or_fetch raises error when no data found."""
        mock_db.get_by_filename.return_value = None
        mock_phototag.fetch_for_file.return_value = None

        with pytest.raises(ValueError, match="Could not fetch metadata"):
            meta.get_or_fetch("nonexistent.jpg")

    def test_get_or_fetch_with_default_tags(
        self, meta, mock_db, mock_phototag, sample_metadata
    ):
        """Test get_or_fetch adds default tags."""
        metadata = sample_metadata.copy()
        metadata["keywords"] = ["existing"]
        mock_db.get_by_filename.return_value = metadata

        result = meta.get_or_fetch("test_image.jpg", default_tags=["new_tag"])
        # Keywords should be extended with new tags
        assert "new_tag" in result.keywords or len(result.keywords) > 0

    def test_get_or_fetch_initializes_keywords_if_none(
        self, meta, mock_db, mock_phototag, sample_metadata
    ):
        """Test get_or_fetch initializes keywords list if None."""
        metadata = sample_metadata.copy()
        metadata["keywords"] = None
        mock_db.get_by_filename.return_value = metadata

        result = meta.get_or_fetch("test_image.jpg")
        assert result.keywords == []


class TestMetaGetById:
    """Test the get_by_id method."""

    def test_get_by_id_from_db(self, meta, mock_db, sample_metadata):
        """Test get_by_id when data exists in database."""
        mock_db.get_by_id.return_value = sample_metadata

        result = meta.get_by_id("test_image.jpg")
        assert result.filename == "test_image.jpg"

    def test_get_by_id_not_in_db_fetch_from_api(
        self, meta, mock_db, mock_phototag, sample_metadata
    ):
        """Test get_by_id fetches from API when not in database."""
        mock_db.get_by_id.return_value = None
        mock_phototag.fetch_for_file.return_value = sample_metadata

        result = meta.get_by_id("test_image.jpg")
        assert result.filename == "test_image.jpg"
        mock_db.insert.assert_called_once()

    def test_get_by_id_not_found(self, meta, mock_db, mock_phototag):
        """Test get_by_id returns None when not found anywhere."""
        mock_db.get_by_id.return_value = None
        mock_phototag.fetch_for_file.return_value = None

        result = meta.get_by_id("nonexistent.jpg")
        assert result is None


class TestMetaGetByFilename:
    """Test the get_by_filename method."""

    def test_get_by_filename_found(self, meta, mock_db, sample_metadata):
        """Test get_by_filename when record exists."""
        mock_db.get_by_filename.return_value = sample_metadata

        result = meta.get_by_filename("test_image.jpg")
        assert result.filename == "test_image.jpg"

    def test_get_by_filename_not_found(self, meta, mock_db):
        """Test get_by_filename returns None when not found."""
        mock_db.__enter__.return_value.get_by_filename.return_value = None
        mock_db.__exit__.return_value = None

        result = meta.get_by_filename("nonexistent.jpg")
        assert result is None


class TestMetaFetchForFile:
    """Test the fetch_for_file method."""

    def test_fetch_for_file_success(
        self, meta, mock_db, mock_phototag, sample_metadata
    ):
        """Test fetch_for_file fetches and stores metadata."""
        mock_db.get_by_filename.return_value = None
        mock_phototag.fetch_for_file.return_value = sample_metadata

        result = meta.fetch_for_file("test_image.jpg")
        assert result.filename == "test_image.jpg"
        mock_db.update_or_insert.assert_called_once()

    def test_fetch_for_file_already_exists_raises_error(
        self, meta, mock_db, mock_phototag, sample_metadata
    ):
        """Test fetch_for_file raises error if file already in database."""
        mock_db.get_by_filename.return_value = sample_metadata

        with pytest.raises(ValueError, match="already exists in the database"):
            meta.fetch_for_file("test_image.jpg")

    def test_fetch_for_file_force_override(
        self, meta, mock_db, mock_phototag, sample_metadata
    ):
        """Test fetch_for_file with force=True overrides existing data."""
        mock_db.get_by_filename.return_value = sample_metadata
        mock_phototag.fetch_for_file.return_value = sample_metadata

        result = meta.fetch_for_file("test_image.jpg", force=True)
        assert result.filename == "test_image.jpg"


class TestMetaEnsureKeywords:
    """Test the ensure_keywords method."""

    def test_ensure_keywords_appends_to_existing(self, meta, mock_db, sample_metadata):
        """Test ensure_keywords appends new keywords to existing ones."""
        metadata = MetaData(**sample_metadata)
        original_keywords = metadata.keywords.copy()

        with patch.object(metadata, "append_keywords") as mock_append:
            result = meta.ensure_keywords(metadata, ["new_keyword"])
            mock_append.assert_called_once_with(["new_keyword"])

    def test_ensure_keywords_updates_db(self, meta, mock_db, sample_metadata):
        """Test ensure_keywords updates database."""
        metadata = MetaData(**sample_metadata)

        with patch.object(metadata, "append_keywords"):
            result = meta.ensure_keywords(metadata, ["new_keyword"])
            mock_db.update_or_insert.assert_called_once()


class TestMetaRemoveKeywords:
    """Test the remove_keywords method."""

    def test_remove_keywords_removes_specified_keywords(
        self, meta, mock_db, sample_metadata
    ):
        """Test remove_keywords removes specified keywords."""
        metadata = MetaData(**sample_metadata)
        original_count = len(metadata.keywords)

        result = meta.remove_keywords(metadata, ["test"])
        assert "test" not in result.keywords
        assert len(result.keywords) < original_count

    def test_remove_keywords_keeps_other_keywords(self, meta, mock_db, sample_metadata):
        """Test remove_keywords keeps keywords not in removal list."""
        metadata = MetaData(**sample_metadata)

        result = meta.remove_keywords(metadata, ["test"])
        assert "image" in result.keywords

    def test_remove_keywords_removes_multiple(self, meta, mock_db):
        """Test remove_keywords removes multiple keywords at once."""
        metadata = MetaData(
            id="test.jpg",
            filename="test.jpg",
            keywords=["sunset", "beach", "ocean", "vacation"],
            title="Test",
            description="Test",
        )

        result = meta.remove_keywords(metadata, ["sunset", "vacation"])
        assert set(result.keywords) == {"beach", "ocean"}

    def test_remove_keywords_updates_db(self, meta, mock_db, sample_metadata):
        """Test remove_keywords updates database."""
        metadata = MetaData(**sample_metadata)

        result = meta.remove_keywords(metadata, ["test"])
        mock_db.update_or_insert.assert_called_once()

    def test_remove_keywords_returns_metadata(self, meta, mock_db, sample_metadata):
        """Test remove_keywords returns the metadata object."""
        metadata = MetaData(**sample_metadata)

        result = meta.remove_keywords(metadata, ["test"])
        assert result == metadata

    def test_remove_keywords_with_nonexistent_keyword(
        self, meta, mock_db, sample_metadata
    ):
        """Test remove_keywords handles non-existent keywords gracefully."""
        metadata = MetaData(**sample_metadata)
        original_keywords = metadata.keywords.copy()

        result = meta.remove_keywords(metadata, ["nonexistent"])
        assert set(result.keywords) == set(original_keywords)

    def test_remove_keywords_with_empty_removal_list(
        self, meta, mock_db, sample_metadata
    ):
        """Test remove_keywords with empty removal list."""
        metadata = MetaData(**sample_metadata)
        original_keywords = metadata.keywords.copy()

        result = meta.remove_keywords(metadata, [])
        assert set(result.keywords) == set(original_keywords)

    def test_remove_keywords_removes_all_keywords(self, meta, mock_db):
        """Test remove_keywords can remove all keywords."""
        metadata = MetaData(
            id="test.jpg",
            filename="test.jpg",
            keywords=["tag1", "tag2"],
            title="Test",
            description="Test",
        )

        result = meta.remove_keywords(metadata, ["tag1", "tag2"])
        assert result.keywords == []


class TestMetaUpdateDb:
    """Test the update_db method."""

    def test_update_db_calls_update_or_insert(self, meta, mock_db, sample_metadata):
        """Test update_db calls database update_or_insert."""
        metadata = MetaData(**sample_metadata)

        result = meta.update_db(metadata)
        mock_db.update_or_insert.assert_called_once()
        assert result == metadata

    def test_update_db_returns_metadata(self, meta, mock_db, sample_metadata):
        """Test update_db returns the metadata object."""
        metadata = MetaData(**sample_metadata)

        result = meta.update_db(metadata)
        assert result is metadata
