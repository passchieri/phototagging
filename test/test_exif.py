from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest
from pyexiv2 import ImageMetadata  # type: ignore

from phototagging.exif import (
    CITY_KEY,
    COUNTRY_KEY,
    KEYWORD_KEYS,
    ExifManager,
    ExifMetadata,
    add_keywords_to_metadata,
    remove_all_keywords_from_exif,
)


class FakeExifEntry:
    def __init__(self, value: Any):
        self.value = value


class FakeBaseMetadata(dict[str, Any]):
    pass


def make_base_metadata() -> ImageMetadata:
    base = FakeBaseMetadata()
    base[CITY_KEY] = FakeExifEntry(["Amsterdam"])
    base[COUNTRY_KEY] = FakeExifEntry(["The Netherlands"])
    base[KEYWORD_KEYS[0]] = FakeExifEntry(["existing"])
    return cast(ImageMetadata, base)


def test_exif_metadata_keywords_collect_values_from_all_keys():
    wrapped = ExifMetadata(make_base_metadata())

    assert set(wrapped.keywords) == {"existing"}


def test_exif_metadata_add_keywords_includes_location_info_and_deduplicates():
    wrapped = ExifMetadata(make_base_metadata())

    wrapped.add_keywords(["new", "existing"], include_location_info=True)

    for key in KEYWORD_KEYS:
        assert wrapped._base[key] == ["amsterdam", "existing", "new", "the netherlands"]  # type: ignore


def test_exif_metadata_clear_keywords_removes_all_known_keys():
    wrapped = ExifMetadata(make_base_metadata())

    wrapped.clear_keywords()

    assert all(key not in wrapped._base for key in KEYWORD_KEYS)  # type: ignore


def test_add_keywords_to_metadata_writes_sorted_keywords_to_all_keys():
    exif = FakeBaseMetadata()
    exif[CITY_KEY] = FakeExifEntry(["Den Haag"])
    exif[COUNTRY_KEY] = FakeExifEntry(["Netherlands"])

    result = add_keywords_to_metadata(exif, ["beta", "alpha"], include_location_info=True)

    assert result is exif
    for key in KEYWORD_KEYS:
        assert exif[key] == ["alpha", "beta", "den haag", "netherlands"]


def test_remove_all_keywords_from_exif_removes_known_keys():
    exif = FakeBaseMetadata()
    for key in KEYWORD_KEYS:
        exif[key] = ["value"]

    result = remove_all_keywords_from_exif(exif)

    assert result is exif
    assert all(key not in exif for key in KEYWORD_KEYS)


def test_exif_manager_context_reads_and_writes_metadata():
    fake_base = FakeBaseMetadata()
    fake_exif = MagicMock()
    fake_exif.commit = True

    with (
        patch("phototagging.exif.read_exif", return_value=fake_base) as mock_read,
        patch("phototagging.exif.ExifMetadata", return_value=fake_exif) as mock_wrapper,
    ):
        with ExifManager("image.jpg") as exif:
            assert exif is fake_exif

    mock_read.assert_called_once_with("image.jpg")
    mock_wrapper.assert_called_once_with(fake_base)
    fake_exif.write.assert_called_once_with()


def test_exif_manager_context_skips_write_on_exception():
    fake_base = FakeBaseMetadata()
    fake_exif = MagicMock()
    fake_exif.commit = True

    with (
        patch("phototagging.exif.read_exif", return_value=fake_base),
        patch("phototagging.exif.ExifMetadata", return_value=fake_exif),
    ):
        with pytest.raises(RuntimeError):
            with ExifManager("image.jpg") as _exif:
                raise RuntimeError("boom")

    fake_exif.write.assert_not_called()
