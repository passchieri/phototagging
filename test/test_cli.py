import datetime
from typing import Any, Counter, Dict, List, cast
from unittest.mock import MagicMock, Mock, patch

import pytest

from phototagging.cli import _create_parser, _print_result, _process_fields, delete, main  # type: ignore
from phototagging.metadata import Metadata  # type: ignore

_all_fields = [*list(Metadata.model_fields)]


@pytest.fixture
def metadata1() -> Metadata:
    return Metadata(
        filename="test_image_1.jpg",
        full_path="/dummy/path/to/file/test_image_1.jpg",  # type: ignore
        create_date=datetime.datetime.now(),
        keywords={"test", "image1"},
        description="A test image",
        title="Test Image 1",
    )


@pytest.fixture
def all_fields():
    return _all_fields


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
        args = parser.parse_args(["-t", "add1,add2", "-r", "remove1,remove2", "image.jpg"])
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

    @pytest.mark.parametrize(
        ("input", "output"),
        [
            ([], _all_fields),
            (None, _all_fields),
            (["all"], _all_fields),
            (["shutter"], ["shutter"]),
            (["shutterstock"], ["shutter"]),
            (["title", "description"], ["title", "description"]),
        ],
    )
    def test_process_fields(self, input: List[str], output: List[str]):
        result = _process_fields(input)
        assert Counter(result) == Counter(output)

    @pytest.mark.parametrize(
        ("input", "message"),
        [
            (["all", "title"], "'all' field cannot be used with other fields"),
            (["shutterstock", "title"], "'shutterstock' field cannot be used with other fields"),
        ],
    )
    def test_process_fields_error(self, input: List[str], message: str):
        with pytest.raises(ValueError, match=message):
            _process_fields(input)


class TestValidateArgs:
    """Test the validate_args function."""

    @pytest.mark.parametrize(
        ("kwargs", "expected_message"),
        [
            ({"token": "", "all": False, "scan": "", "delete": False, "image": []}, "API token is required"),
            (
                {"token": "token", "all": True, "scan": "some", "delete": False, "image": []},
                "Cannot use --all and --scan together",
            ),
            (
                {"token": "token", "all": True, "scan": "", "delete": True, "image": []},
                "Cannot use --delete with --all",
            ),
            (
                {"token": "token", "all": False, "scan": "some", "delete": True, "image": []},
                "Cannot use --delete with --scan",
            ),
            (
                {"token": "token", "all": False, "scan": "", "delete": False, "image": []},
                "At least one image file must be specified",
            ),
            (
                {"token": "token", "all": False, "scan": "", "delete": True, "image": []},
                "At least one image file must be specified for deletion",
            ),
        ],
    )
    def test_validate_args_rejects_disallowed_combinations(self, kwargs: Dict[str, Any], expected_message: str):
        from phototagging.cli import validate_args

        args = MagicMock()
        args.token = kwargs["token"]
        args.all = kwargs["all"]
        args.scan = kwargs["scan"]
        args.delete = kwargs["delete"]
        args.image = kwargs["image"]

        with pytest.raises(ValueError, match=expected_message):
            validate_args(args)


class TestPrintResult:
    """Test the _print_result function."""

    def test_print_result_with_fields(self, capsys: pytest.CaptureFixture[str], metadata1: Metadata):
        """Test printing result with specific fields."""

        _print_result(metadata1, ["filename", "title"])
        captured = capsys.readouterr()
        assert metadata1.filename in captured.out
        assert metadata1.title in captured.out

    def test_print_result_invalid_field(self, capsys: pytest.CaptureFixture[str], metadata1: Metadata):
        """Test printing result with invalid field."""

        _print_result(metadata1, ["invalid_field"])
        captured = capsys.readouterr()
        assert "No such field" in captured.out

    def test_print_result_callable_field(self, capsys: pytest.CaptureFixture[str], metadata1: Metadata):
        """Test printing result with callable field."""

        _print_result(metadata1, ["pexels"])
        captured = capsys.readouterr()
        assert metadata1.keywords.pop() in captured.out

    def test_print_result_shutter_format(self, capsys: pytest.CaptureFixture[str], metadata1: Metadata):
        """Test printing result in shutter format."""

        _print_result(metadata1, ["shutter"])
        captured = capsys.readouterr()
        assert metadata1.filename in captured.out
        assert metadata1.title in captured.out
        assert metadata1.keywords.pop() in captured.out

    def test_print_result_with_all_fields(
        self, capsys: pytest.CaptureFixture[str], metadata1: Metadata, all_fields: List[str]
    ):
        """Test printing result with all fields."""

        fields = _process_fields(["all"])
        _print_result(metadata1, fields)
        captured = capsys.readouterr()
        for f in all_fields:
            if f == "keywords":
                kws = cast(List[str], getattr(metadata1, f, None))
                for k in kws:
                    assert k in captured.out
            else:
                val = getattr(metadata1, f)
                assert str(val) in captured.out

    def test_print_result_with_no_results(self, capsys: pytest.CaptureFixture[str]):
        _print_result(None, ["filename"])
        captured = capsys.readouterr()
        assert "No metadata" in captured.out


class TestDelete:
    """Test the delete helper."""

    def test_delete_removes_existing_record(self, capsys: pytest.CaptureFixture[str]):
        meta = MagicMock()
        result = MagicMock()
        result.id = "record-1"
        meta.get_by_filename.return_value = result

        exit_code = delete(meta, ["image.jpg"])

        assert exit_code == 0
        meta.get_by_filename.assert_called_once_with("image.jpg")
        meta.delete_by_id.assert_called_once_with("record-1")
        captured = capsys.readouterr()
        assert "Deleted record for file image.jpg" in captured.out


class TestMain:
    """Test the main function."""

    def test_main_no_token(self, capsys: pytest.CaptureFixture[str]):
        """Test main function with no token."""
        with patch("phototagging.cli._create_parser") as mock_parser:
            mock_args = MagicMock()
            mock_args.token = ""
            mock_args.image = []
            mock_args.tags = []
            mock_parser.return_value.parse_args.return_value = mock_args

            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "API token is required" in captured.out

    @patch("phototagging.cli.Db")
    @patch("phototagging.cli.PhotoTag")
    def test_main_with_valid_args(self, mock_phototag: Mock, mock_db: Mock):
        """Test main function with valid arguments."""
        with patch("phototagging.cli._create_parser") as mock_parser:
            mock_args = MagicMock()
            mock_args.token = "valid_token"
            mock_args.delete = False
            mock_args.url = "https://api.test.com"
            mock_args.db = "/path/to/db.json"
            mock_args.tags = ["tag1"]
            mock_args.image = []
            mock_args.print = []
            mock_args.scan = None
            mock_parser.return_value.parse_args.return_value = mock_args

            result = main()
            assert result == 0
            mock_db.assert_called_once_with("/path/to/db.json")
            mock_phototag.assert_called_once_with(url="https://api.test.com", token="valid_token")

    @patch("phototagging.cli.MetadataManager")
    def test_main_with_arg_all(self, mock_meta: Mock):
        """Test main function with valid arguments."""
        with patch("phototagging.cli._create_parser") as mock_parser:
            mock_args = MagicMock()
            mock_args.token = "valid_token"
            mock_args.delete = False
            mock_args.url = "https://api.test.com"
            mock_args.db = "/path/to/db.json"
            mock_args.tags = ["tag1"]
            mock_args.image = []
            mock_args.print = []
            mock_args.all = True
            mock_args.scan = None

            mock_parser.return_value.parse_args.return_value = mock_args
            mock_meta.return_value.all.return_value = [MagicMock(filename="filename") for _ in range(3)]

            with patch("phototagging.cli._print_result") as mock_print:
                main()
                assert mock_print.call_count == 3

    @patch("phototagging.cli.MetadataManager")
    def test_main_with_images(self, mock_meta: Mock):
        """Test main function processing images."""
        with patch("phototagging.cli._create_parser") as mock_parser:
            mock_args = MagicMock()
            mock_args.token = "valid_token"
            mock_args.delete = False
            mock_args.url = "https://api.test.com"
            mock_args.db = "/path/to/db.json"
            mock_args.tags = []
            mock_args.remove_tags = []
            mock_args.image = ["image1.jpg", "image2.jpg"]
            mock_args.print = []
            mock_args.scan = False
            mock_args.all = False

            # Setup the Meta mock
            mock_meta_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {}
            mock_result.pexels.return_value = ""
            mock_result.instagram.return_value = ""
            mock_meta_instance.get_or_create.return_value = mock_result
            mock_meta.return_value = mock_meta_instance

            mock_parser.return_value.parse_args.return_value = mock_args

            with patch("phototagging.cli._print_result"):
                result = main()
            assert result == 0
            assert mock_meta_instance.get_or_create.call_count == 2

    @patch("phototagging.cli.MetadataManager")
    def test_main_with_remove_tags(self, mock_meta: Mock):
        """Test main function with remove-tags argument."""
        with patch("phototagging.cli._create_parser") as mock_parser:
            mock_args = MagicMock()
            mock_args.token = "valid_token"
            mock_args.delete = False
            mock_args.url = "https://api.test.com"
            mock_args.db = "/path/to/db.json"
            mock_args.tags = []
            mock_args.remove_tags = ["tag1", "tag2"]
            mock_args.image = ["image1.jpg"]
            mock_args.print = []
            mock_args.scan = False
            mock_args.all = False

            # Setup the Meta mock
            mock_meta_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {}
            mock_result.pexels.return_value = ""
            mock_result.instagram.return_value = ""
            mock_meta_instance.get_or_create.return_value = mock_result
            mock_meta.return_value = mock_meta_instance

            mock_parser.return_value.parse_args.return_value = mock_args

            with patch("phototagging.cli._print_result"):
                result = main()
            assert result == 0
            # Verify get_or_create was called with remove_tags
            mock_meta_instance.get_or_create.assert_called_once()
            call_kwargs = mock_meta_instance.get_or_create.call_args[1]
            assert call_kwargs["keywords_to_remove"] == ["tag1", "tag2"]

    @patch("phototagging.cli.MetadataManager")
    def test_main_with_tags_and_remove_tags(self, mock_meta: Mock):
        """Test main function with both tags and remove-tags arguments."""
        with patch("phototagging.cli._create_parser") as mock_parser:
            mock_args = MagicMock()
            mock_args.token = "valid_token"
            mock_args.delete = False
            mock_args.url = "https://api.test.com"
            mock_args.db = "/path/to/db.json"
            mock_args.tags = ["add1", "add2"]
            mock_args.remove_tags = ["remove1", "remove2"]
            mock_args.image = ["image.jpg"]
            mock_args.print = []
            mock_args.scan = False
            mock_args.all = False

            # Setup the Meta mock
            mock_meta_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {}
            mock_result.pexels.return_value = ""
            mock_result.instagram.return_value = ""
            mock_meta_instance.get_or_create.return_value = mock_result
            mock_meta.return_value = mock_meta_instance

            mock_parser.return_value.parse_args.return_value = mock_args

            with patch("phototagging.cli._print_result"):
                result = main()
            assert result == 0
            # Verify get_or_create was called with both default_tags and removed_tags
            mock_meta_instance.get_or_create.assert_called_once()
            call_kwargs = mock_meta_instance.get_or_create.call_args[1]
            assert call_kwargs["required_keywords"] == ["add1", "add2"]
            assert call_kwargs["keywords_to_remove"] == ["remove1", "remove2"]

    @patch("phototagging.cli.Db")
    def test_main_exception_handling(self, mock_db: Mock, capsys: pytest.CaptureFixture[str]):
        """Test main function exception handling."""
        with patch("phototagging.cli._create_parser") as mock_parser:
            mock_args = MagicMock()
            mock_args.token = "valid_token"
            mock_args.delete = False
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
            assert "Error:" in captured.out
