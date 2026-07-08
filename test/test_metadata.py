import datetime
import uuid
from collections import Counter
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from phototagging.metadata import Metadata


@pytest.fixture
def base_data() -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "filename": "filename.jpg",
        "full_path": "/just/a/dummy/path/filename.jpg",
        "create_date": datetime.datetime.now().isoformat(),
        "keywords": ["test", "data1", "Capital", "duplicate", "duplicate"],
        "title": "The title",
        "description": "A longer description",
    }


@pytest.fixture
def metadata(base_data: Dict[str, Any]) -> Metadata:
    return Metadata(**base_data)


def test_missing_required_fields(base_data: Dict[str, Any]):
    """Test that Metadata raises an error for invalid data."""

    assert Metadata(**base_data) is not None

    dup = base_data.copy()
    dup.pop("filename")
    with pytest.raises(ValidationError):
        _ = Metadata(**dup)
        assert False, "It should not be allowed that filename is missing"


def test_missing_non_required_fields(base_data: Dict[str, Any]):
    """Test that Metadata raises an error for invalid data."""

    for kw in ["id"]:
        dup = base_data.copy()
        dup.pop(kw)
        result = Metadata(**dup)
        assert result is not None, f"It should be allowed that {kw} is missing"


def test_metadata(base_data: Dict[str, Any], metadata: Metadata):

    assert metadata.id == base_data["id"]
    assert metadata.filename == base_data["filename"]

    kws = [kw.lower() for kw in set(base_data["keywords"])]
    for kw in kws:
        assert kw in metadata.keywords

    assert len(kws) == len(metadata.keywords)

    for kw in kws:
        assert kw in metadata.pexels

    for kw in kws:
        assert "#" + kw.replace(" ", "") in metadata.instagram

    metadata.keywords = set()
    assert metadata.pexels == ""
    assert metadata.instagram == ""


def test_append_keywords(metadata: Metadata):
    """Test the append_keywords method of Metadata."""
    kws = {kw for kw in metadata.keywords}
    metadata.append_keywords(kws)
    assert Counter(metadata.keywords) == Counter(kws), "Adding an existing keyword should avoid duplicates"
    kws.add("extra")
    metadata.append_keywords(["extra"])
    assert Counter(metadata.keywords) == Counter(kws), "append_keywords should add new keywords"

    metadata.append_keywords([])
    assert Counter(metadata.keywords) == Counter(kws), "adding an empty list should do nothing"


def test_remove_keywords(metadata: Metadata):
    """Test the remove_keywords method of Metadata."""
    kws = {kw for kw in metadata.keywords}

    metadata.remove_keywords([])
    assert Counter(kws) == Counter(metadata.keywords)

    first = next(iter(kws))
    metadata.remove_keywords([first])
    assert first not in metadata.keywords, "remove_keywords should remove specified keywords"

    kws.remove(first)
    assert Counter(kws) == Counter(metadata.keywords)

    metadata.remove_keywords(["non existing"])
    assert Counter(kws) == Counter(metadata.keywords)

    metadata.remove_keywords(kws)
    assert len(metadata.keywords) == 0


def test_replace_keywords(metadata: Metadata):
    """Test the replace_keywords method of Metadata."""
    new_keywords = ["new", "keywords"]
    metadata.replace_keywords(new_keywords)
    assert Counter(new_keywords) == Counter(metadata.keywords), (
        "replace_keywords should replace all existing keywords with new ones"
    )
    new_keywords = ["Caps", "dup", "dup"]
    metadata.replace_keywords(new_keywords)
    assert Counter(["caps", "dup"]) == Counter(metadata.keywords), (
        "replace_keywords should remove duplicates and capitalization"
    )


def test_to_dict(base_data: Dict[str, Any]):
    mddict = Metadata(**base_data).model_dump(mode="json")
    for key in mddict.keys():
        if not key == "keywords":
            assert mddict[key] == base_data[key]
    assert Counter(mddict["keywords"]) == Counter({k.lower() for k in base_data["keywords"]})
