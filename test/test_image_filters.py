#type: ignore
# tests/test_image_filters.py

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from phototag.filters import (
    create_age_filter,
    create_max_files_filter,
    create_regexp_filter,
    create_db_filter,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_images(tmp_path):
    """Create a set of temporary image files."""
    paths = []
    for name in ["a.jpg", "b.jpg", "c.jpg"]:
        p = tmp_path / name
        p.write_text("dummy")
        paths.append(p)
    return paths


def patch_mtimes(images: list[Path], mtimes: list[datetime]):
    """Patch Path.stat() to return controlled modification times."""
    assert len(images) == len(mtimes)

    stats = [MagicMock(st_mtime=dt.timestamp()) for dt in mtimes]

    return patch.object(Path, "stat", side_effect=stats)


# ---------------------------------------------------------------------------
# Age filter tests (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "max_days, ages, expected_indices",
    [
        (5, [1, 10, 2], [0, 2]),   # keep images 0 and 2
        (1, [0.5, 2, 0.2], [0, 2]),
        (0, [0, 1, 2], [0]),
    ],
)
def test_age_filter(tmp_images, max_days, ages, expected_indices):
    now = datetime.now()
    # Add 5 minutes, otherwise all dates can be as good as on the cutoff time
    mtimes = [now - timedelta(days=a)+timedelta(minutes=5) for a in ages]

    with patch_mtimes(tmp_images, mtimes):
        flt = create_age_filter(max_days)
        result = flt(tmp_images)

    expected = [tmp_images[i] for i in expected_indices]
    assert result == expected


# ---------------------------------------------------------------------------
# Max files filter tests (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "max_files, expected_count",
    [
        (0, 0),
        (1, 1),
        (2, 2),
        (10, 3),  # more than available
    ],
)
def test_max_files_filter(tmp_images, max_files, expected_count):
    flt = create_max_files_filter(max_files)
    result = flt(tmp_images)
    assert len(result) == expected_count
    assert result == tmp_images[:expected_count]


# ---------------------------------------------------------------------------
# Regexp filter tests (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "pattern, filenames, expected",
    [
        (r"cat", ["cat1.jpg", "dog.jpg"], ["cat1.jpg"]),
        (r"\d+", ["a1.jpg", "b2.jpg", "c.jpg"], ["a1.jpg", "b2.jpg"]),
        (r"^x", ["x.jpg", "y.jpg"], ["x.jpg"]),
        (r"nomatch", ["a.jpg", "b.jpg"], []),
    ],
)
def test_regexp_filter(tmp_path, pattern, filenames, expected):
    images = []
    for name in filenames:
        p = tmp_path / name
        p.write_text("x")
        images.append(p)

    flt = create_regexp_filter(pattern)
    result = flt(images)

    expected_paths = [tmp_path / name for name in expected]
    assert result == expected_paths


# ---------------------------------------------------------------------------
# DB filter tests
# ---------------------------------------------------------------------------

class DummyRecord:
    def __init__(self, filename: str):
        self.filename = filename


@pytest.mark.parametrize(
    "db_filenames, image_name, should_match",
    [
        (["a.jpg"], "a.jpg", True),
        (["/full/path/b.jpg"], "b.jpg", True),
        (["c.jpg"], "x.jpg", False),
        ([], "a.jpg", False),
    ],
)
def test_db_filter(tmp_path, db_filenames, image_name, should_match):
    img = tmp_path / image_name
    img.write_text("x")

    mock_db = MagicMock()
    mock_db.all.return_value = [DummyRecord(str(Path(f).name)) for f in db_filenames]

    flt = create_db_filter(mock_db)
    result = flt([img])

    if should_match:
        assert result == [img]
    else:
        assert result == []