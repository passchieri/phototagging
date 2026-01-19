import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import requests
from phototag.phototag import PhotoTag, URL, TOKEN, PAYLOAD


@pytest.fixture
def phototag():
    """Create a PhotoTag instance for testing."""
    return PhotoTag()


@pytest.fixture
def custom_phototag():
    """Create a PhotoTag instance with custom options."""
    custom_options = {"maxKeywords": 30, "language": "es"}
    return PhotoTag(options=custom_options)


@pytest.fixture
def sample_response():
    """Create a sample API response."""
    return {
        "data": {
            "keywords": ["river", "sunset", "boat", "city"],
            "title": "Beautiful river sunset",
            "description": "A scenic view of a river at sunset with boats",
        }
    }


class TestPhotoTagInit:
    """Test PhotoTag initialization."""

    def test_init_default_values(self):
        """Test PhotoTag initialization with default values."""
        phototag = PhotoTag()
        assert phototag.url == URL
        assert phototag.headers == {"Authorization": f"Bearer {TOKEN}"}
        assert phototag.payload == PAYLOAD

    def test_init_custom_url(self):
        """Test PhotoTag initialization with custom URL."""
        custom_url = "https://custom.api.com/keywords"
        phototag = PhotoTag(url=custom_url)
        assert phototag.url == custom_url

    def test_init_custom_token(self):
        """Test PhotoTag initialization with custom token."""
        custom_token = "custom-token-12345"
        phototag = PhotoTag(token=custom_token)
        assert phototag.headers == {"Authorization": f"Bearer {custom_token}"}

    def test_init_custom_options(self):
        """Test PhotoTag initialization with custom options."""
        custom_options = {"maxKeywords": 30, "language": "es"}
        phototag = PhotoTag(options=custom_options)
        assert phototag.payload["maxKeywords"] == 30
        assert phototag.payload["language"] == "es"
        # Other default options should still be present
        assert "addMetadata" in phototag.payload

    def test_init_options_override_defaults(self):
        """Test that custom options override defaults."""
        custom_options = {"addMetadata": True}
        phototag = PhotoTag(options=custom_options)
        assert phototag.payload["addMetadata"] is True

    def test_init_preserves_default_payload(self):
        """Test that default payload is not mutated."""
        phototag1 = PhotoTag()
        phototag2 = PhotoTag(options={"maxKeywords": 50})
        assert phototag1.payload["maxKeywords"] == PAYLOAD["maxKeywords"]
        assert phototag2.payload["maxKeywords"] == 50


class TestPhotoTagFetchForFile:
    """Test the fetch_for_file method."""

    def test_fetch_for_file_success(self, phototag, sample_response):
        """Test successful file fetch and API call."""
        test_file = "test_image.jpg"

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch("builtins.open", create=True) as mock_open,
            patch("phototag.phototag.requests.post") as mock_post,
        ):

            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = sample_response
            mock_post.return_value = mock_response

            result = phototag.fetch_for_file(test_file)

            assert result["keywords"] == sample_response["data"]["keywords"]
            assert result["title"] == sample_response["data"]["title"]
            assert result["filename"] == "test_image.jpg"
            assert result["id"] == "test_image.jpg"

    def test_fetch_for_file_not_found(self, phototag):
        """Test that FileNotFoundError is raised for non-existent file."""
        with patch("pathlib.Path.is_file", return_value=False):
            with pytest.raises(FileNotFoundError, match="does not exist"):
                phototag.fetch_for_file("nonexistent.jpg")

    def test_fetch_for_file_api_error(self, phototag):
        """Test that HTTPError is raised on API failure."""
        test_file = "test_image.jpg"

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch("builtins.open", create=True) as mock_open,
            patch("phototag.phototag.requests.post") as mock_post,
        ):

            mock_response = Mock()
            mock_response.ok = False
            mock_response.raise_for_status.side_effect = requests.HTTPError(
                "404 Not Found"
            )
            mock_post.return_value = mock_response

            with pytest.raises(requests.HTTPError):
                phototag.fetch_for_file(test_file)

    def test_fetch_for_file_sends_correct_headers(self, phototag, sample_response):
        """Test that correct headers are sent to API."""
        test_file = "test_image.jpg"

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch("builtins.open", create=True) as mock_open,
            patch("phototag.phototag.requests.post") as mock_post,
        ):

            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = sample_response
            mock_post.return_value = mock_response

            phototag.fetch_for_file(test_file)

            # Verify headers were sent correctly
            call_args = mock_post.call_args
            assert call_args[1]["headers"] == phototag.headers

    def test_fetch_for_file_sends_payload(self, phototag, sample_response):
        """Test that payload is sent to API."""
        test_file = "test_image.jpg"

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch("builtins.open", create=True) as mock_open,
            patch("phototag.phototag.requests.post") as mock_post,
        ):

            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = sample_response
            mock_post.return_value = mock_response

            phototag.fetch_for_file(test_file)

            # Verify payload was sent
            call_args = mock_post.call_args
            assert call_args[1]["data"] == phototag.payload

    def test_fetch_for_file_sends_file(self, phototag, sample_response):
        """Test that file is sent to API."""
        test_file = "test_image.jpg"

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch("builtins.open", create=True) as mock_open,
            patch("phototag.phototag.requests.post") as mock_post,
        ):

            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = sample_response
            mock_post.return_value = mock_response

            phototag.fetch_for_file(test_file)

            # Verify file was sent
            call_args = mock_post.call_args
            assert "files" in call_args[1]
            assert "file" in call_args[1]["files"]

    def test_fetch_for_file_adds_filename_and_id(self, phototag, sample_response):
        """Test that filename and id are added to response."""
        test_file = "my_photo.png"

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch("builtins.open", create=True) as mock_open,
            patch("phototag.phototag.requests.post") as mock_post,
        ):

            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = sample_response
            mock_post.return_value = mock_response

            result = phototag.fetch_for_file(test_file)

            assert result["filename"] == "my_photo.png"
            assert result["id"] == "my_photo.png"

    def test_fetch_for_file_with_path_object(self, phototag, sample_response):
        """Test fetch_for_file with Path object."""
        test_file = Path("images/test.jpg")

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch("builtins.open", create=True) as mock_open,
            patch("phototag.phototag.requests.post") as mock_post,
        ):

            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = sample_response
            mock_post.return_value = mock_response

            result = phototag.fetch_for_file(str(test_file))

            assert result["filename"] == "test.jpg"
            assert result["id"] == "test.jpg"
