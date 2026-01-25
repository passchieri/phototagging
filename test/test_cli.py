import pytest
from unittest.mock import Mock, patch, MagicMock
from phototag.cli import _create_parser, _process_fields, _print_result, main
from phototag.metadata import MetaData


class TestCreateParser:
    """Test the _create_parser function."""

    def test_parser_creation(self):
        """Test that the parser is created successfully."""
        parser = _create_parser()
        assert parser is not None

    def test_parser_with_url(self):
        """Test parser with URL argument."""
        parser = _create_parser()
        args = parser.parse_args(["-u", "https://test.api.com", "image.jpg"])
        assert args.url == "https://test.api.com"

    def test_parser_with_token(self):
        """Test parser with token argument."""
        parser = _create_parser()
        args = parser.parse_args(["--token", "test_token", "image.jpg"])
        assert args.token == "test_token"

    def test_parser_with_tags(self):
        """Test parser with tags argument."""
        parser = _create_parser()
        args = parser.parse_args(["-t", "tag1,tag2,tag3", "image.jpg"])
        assert args.tags == ["tag1", "tag2", "tag3"]

    def test_parser_with_tags_whitespace(self):
        """Test parser with tags containing whitespace."""
        parser = _create_parser()
        args = parser.parse_args(["-t", "tag1, tag2 , tag3", "image.jpg"])
        assert args.tags == ["tag1", "tag2", "tag3"]

    def test_parser_with_remove_tags(self):
        """Test parser with remove-tags argument."""
        parser = _create_parser()
        args = parser.parse_args(["-r", "tag1,tag2,tag3", "image.jpg"])
        assert args.remove_tags == ["tag1", "tag2", "tag3"]

    def test_parser_with_remove_tags_long_form(self):
        """Test parser with --remove-tags long form argument."""
        parser = _create_parser()
        args = parser.parse_args(["--remove-tags", "tag1,tag2,tag3", "image.jpg"])
        assert args.remove_tags == ["tag1", "tag2", "tag3"]

    def test_parser_with_remove_tags_whitespace(self):
        """Test parser with remove-tags containing whitespace."""
        parser = _create_parser()
        args = parser.parse_args(["-r", "tag1, tag2 , tag3", "image.jpg"])
        assert args.remove_tags == ["tag1", "tag2", "tag3"]

    def test_parser_with_tags_and_remove_tags(self):
        """Test parser with both tags and remove-tags arguments."""
        parser = _create_parser()
        args = parser.parse_args(
            ["-t", "add1,add2", "-r", "remove1,remove2", "image.jpg"]
        )
        assert args.tags == ["add1", "add2"]
        assert args.remove_tags == ["remove1", "remove2"]

    def test_parser_remove_tags_default_empty(self):
        """Test parser default remove-tags is empty list."""
        parser = _create_parser()
        args = parser.parse_args(["image.jpg"])
        assert args.remove_tags == []

        """Test parser with print field argument."""
        parser = _create_parser()
        args = parser.parse_args(["-p", "title", "-p", "description", "image.jpg"])
        assert "title" in args.print
        assert "description" in args.print

    def test_parser_with_multiple_images(self):
        """Test parser with multiple image arguments."""
        parser = _create_parser()
        args = parser.parse_args(["image1.jpg", "image2.jpg", "image3.jpg"])
        assert len(args.image) == 3
        assert "image1.jpg" in args.image

    def test_parser_with_db(self):
        """Test parser with database argument."""
        parser = _create_parser()
        args = parser.parse_args(["-d", "/path/to/db.json", "image.jpg"])
        assert args.db == "/path/to/db.json"


class TestProcessFields:
    """Test the _process_fields function."""

    def test_process_fields_empty(self):
        """Test with empty fields list."""
        result = _process_fields([])
        assert result == []

    def test_process_fields_none(self):
        """Test with None fields."""
        result = _process_fields(None)
        assert result is None

    def test_process_fields_all(self):
        """Test with 'all' field."""
        result = _process_fields(["all"])
        assert "filename" in result
        assert "title" in result
        assert "pexels" in result
        assert "instagram" in result
        assert "description" in result

    def test_process_fields_all_with_other_raises_error(self):
        """Test that 'all' with other fields raises an error."""
        with pytest.raises(
            ValueError, match="'all' field cannot be used with other fields"
        ):
            _process_fields(["all", "title"])

    def test_process_fields_shutterstock(self):
        """Test with 'shutterstock' field."""
        result = _process_fields(["shutterstock"])
        assert result == ["shutter"]

    def test_process_fields_shutter(self):
        """Test with 'shutter' field."""
        result = _process_fields(["shutter"])
        assert result == ["shutter"]

    def test_process_fields_shutterstock_with_other_raises_error(self):
        """Test that 'shutterstock' with other fields raises an error."""
        with pytest.raises(
            ValueError, match="'shutterstock' field cannot be used with other fields"
        ):
            _process_fields(["shutterstock", "title"])

    def test_process_fields_normal(self):
        """Test with normal field names."""
        result = _process_fields(["title", "description"])
        assert result == ["title", "description"]


class TestPrintResult:
    """Test the _print_result function."""

    def test_print_result_no_fields(self, capsys):
        """Test printing result with no fields specified."""
        result = Mock()
        result.to_dict.return_value = {"id": "test.jpg", "title": "Test"}
        result.pexels.return_value = "pexels_data"
        result.instagram.return_value = "instagram_data"

        _print_result(result, [])
        captured = capsys.readouterr()
        assert "test.jpg" in captured.out
        assert "Test" in captured.out

    def test_print_result_with_fields(self, capsys):
        """Test printing result with specific fields."""
        result = Mock()
        result.filename = "test.jpg"
        result.title = "Test Title"
        result.description = None

        _print_result(result, ["filename", "title"])
        captured = capsys.readouterr()
        assert "test.jpg" in captured.out
        assert "Test Title" in captured.out

    def test_print_result_invalid_field(self, capsys):
        """Test printing result with invalid field."""
        result = Mock()
        result.invalid_field = None
        result.to_dict.return_value = {}

        _print_result(result, ["invalid_field"])
        captured = capsys.readouterr()
        assert "No such field" in captured.out

    def test_print_result_callable_field(self, capsys):
        """Test printing result with callable field."""
        result = Mock()
        result.pexels = Mock(return_value="pexels_keywords")

        _print_result(result, ["pexels"])
        captured = capsys.readouterr()
        assert "pexels_keywords" in captured.out

    def test_print_result_shutter_format(self, capsys):
        """Test printing result in shutter format."""
        result = Mock()
        result.filename = "test.jpg"
        result.title = "Test Title"
        result.pexels.return_value = "keywords"

        _print_result(result, ["shutter"])
        captured = capsys.readouterr()
        assert "test.jpg" in captured.out
        assert "Test Title" in captured.out
        assert '"keywords"' in captured.out

    def test_print_result_with_all_fields(self, capsys):
        """Test printing result with all fields."""
        result = MetaData(id="test.jpg", filename="test.jpg",
                          title = "Test Title",
                          description = "Test Description",
                          keywords=["apple","banana"])

        fields=_process_fields(["all"])
        _print_result(result, fields)
        captured = capsys.readouterr()
        assert "test.jpg" in captured.out
        assert "Test Title" in captured.out
        assert "Test Description" in captured.out
        assert "apple" in captured.out
        assert "banana" in captured.out


class TestMain:
    """Test the main function."""

    @patch("phototag.cli.Db")
    @patch("phototag.cli.PhotoTag")
    @patch("phototag.cli.MetadataManager")
    def test_main_no_token(self, mock_meta, mock_phototag, mock_db, capsys):
        """Test main function with no token."""
        with patch("phototag.cli._create_parser") as mock_parser:
            mock_args = Mock()
            mock_args.token = ""
            mock_args.image = []
            mock_args.tags = []
            mock_parser.return_value.parse_args.return_value = mock_args

            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "API token is required" in captured.out

    @patch("phototag.cli.Db")
    @patch("phototag.cli.PhotoTag")
    @patch("phototag.cli.MetadataManager")
    def test_main_with_valid_args(self, mock_meta, mock_phototag, mock_db):
        """Test main function with valid arguments."""
        with patch("phototag.cli._create_parser") as mock_parser:
            mock_args = Mock()
            mock_args.token = "valid_token"
            mock_args.url = "https://api.test.com"
            mock_args.db = "/path/to/db.json"
            mock_args.tags = ["tag1"]
            mock_args.image = []
            mock_args.print = []
            mock_parser.return_value.parse_args.return_value = mock_args

            result = main()
            assert result == 0
            mock_db.assert_called_once_with("/path/to/db.json")
            mock_phototag.assert_called_once_with(
                url="https://api.test.com", token="valid_token"
            )

    @patch("phototag.cli.Db")
    @patch("phototag.cli.PhotoTag")
    @patch("phototag.cli.MetadataManager")
    def test_main_with_images(self, mock_meta, mock_phototag, mock_db):
        """Test main function processing images."""
        with patch("phototag.cli._create_parser") as mock_parser:
            mock_args = Mock()
            mock_args.token = "valid_token"
            mock_args.url = "https://api.test.com"
            mock_args.db = "/path/to/db.json"
            mock_args.tags = []
            mock_args.remove_tags = []
            mock_args.image = ["image1.jpg", "image2.jpg"]
            mock_args.print = []
            mock_args.all=False

            # Setup the Meta mock
            mock_meta_instance = Mock()
            mock_result = Mock()
            mock_result.to_dict.return_value = {}
            mock_result.pexels.return_value = ""
            mock_result.instagram.return_value = ""
            mock_meta_instance.get_or_fetch.return_value = mock_result
            mock_meta.return_value = mock_meta_instance

            mock_parser.return_value.parse_args.return_value = mock_args

            with patch("phototag.cli._print_result"):
                result = main()
            assert result == 0
            assert mock_meta_instance.get_or_fetch.call_count == 2

    @patch("phototag.cli.Db")
    @patch("phototag.cli.PhotoTag")
    @patch("phototag.cli.MetadataManager")
    def test_main_with_remove_tags(self, mock_meta, mock_phototag, mock_db):
        """Test main function with remove-tags argument."""
        with patch("phototag.cli._create_parser") as mock_parser:
            mock_args = Mock()
            mock_args.token = "valid_token"
            mock_args.url = "https://api.test.com"
            mock_args.db = "/path/to/db.json"
            mock_args.tags = []
            mock_args.remove_tags = ["tag1", "tag2"]
            mock_args.image = ["image1.jpg"]
            mock_args.print = []
            mock_args.all=False

            # Setup the Meta mock
            mock_meta_instance = Mock()
            mock_result = Mock()
            mock_result.to_dict.return_value = {}
            mock_result.pexels.return_value = ""
            mock_result.instagram.return_value = ""
            mock_meta_instance.get_or_fetch.return_value = mock_result
            mock_meta.return_value = mock_meta_instance

            mock_parser.return_value.parse_args.return_value = mock_args

            with patch("phototag.cli._print_result"):
                result = main()
            assert result == 0
            # Verify get_or_fetch was called with remove_tags
            mock_meta_instance.get_or_fetch.assert_called_once()
            call_kwargs = mock_meta_instance.get_or_fetch.call_args[1]
            assert call_kwargs["removed_tags"] == ["tag1", "tag2"]

    @patch("phototag.cli.Db")
    @patch("phototag.cli.PhotoTag")
    @patch("phototag.cli.MetadataManager")
    def test_main_with_tags_and_remove_tags(self, mock_meta, mock_phototag, mock_db):
        """Test main function with both tags and remove-tags arguments."""
        with patch("phototag.cli._create_parser") as mock_parser:
            mock_args = Mock()
            mock_args.token = "valid_token"
            mock_args.url = "https://api.test.com"
            mock_args.db = "/path/to/db.json"
            mock_args.tags = ["add1", "add2"]
            mock_args.remove_tags = ["remove1", "remove2"]
            mock_args.image = ["image.jpg"]
            mock_args.print = []
            mock_args.all=False


            # Setup the Meta mock
            mock_meta_instance = Mock()
            mock_result = Mock()
            mock_result.to_dict.return_value = {}
            mock_result.pexels.return_value = ""
            mock_result.instagram.return_value = ""
            mock_meta_instance.get_or_fetch.return_value = mock_result
            mock_meta.return_value = mock_meta_instance

            mock_parser.return_value.parse_args.return_value = mock_args

            with patch("phototag.cli._print_result"):
                result = main()
            assert result == 0
            # Verify get_or_fetch was called with both default_tags and removed_tags
            mock_meta_instance.get_or_fetch.assert_called_once()
            call_kwargs = mock_meta_instance.get_or_fetch.call_args[1]
            assert call_kwargs["default_tags"] == ["add1", "add2"]
            assert call_kwargs["removed_tags"] == ["remove1", "remove2"]

    @patch("phototag.cli.Db")
    @patch("phototag.cli.PhotoTag")
    @patch("phototag.cli.MetadataManager")
    def test_main_exception_handling(self, mock_meta, mock_phototag, mock_db, capsys):
        """Test main function exception handling."""
        with patch("phototag.cli._create_parser") as mock_parser:
            mock_args = Mock()
            mock_args.token = "valid_token"
            mock_args.url = "https://api.test.com"
            mock_args.db = "/path/to/db.json"
            mock_args.tags = []
            mock_args.image = []
            mock_args.print = []
            mock_parser.return_value.parse_args.return_value = mock_args

            mock_db.side_effect = Exception("Database error")

            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "Error: Database error" in captured.out
