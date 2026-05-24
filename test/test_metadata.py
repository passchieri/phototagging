from collections import Counter
from typing import Any, Dict

import pytest
from sortedcontainers import SortedSet

from phototag.metadata import MetaData


@pytest.fixture
def base_data() -> Dict[str, Any]:
    return {
        "id": 99,
        "filename": "filename.jpg",
        "keywords": ["test", "data1", "Capital", "duplicate", "duplicate"],
        "title": "The title",
        "description": "A longer description",
    }


@pytest.fixture
def sample(base_data: Dict[str, Any]) -> MetaData:
    return MetaData(**base_data)


def test_missing_required_fields(base_data: Dict[str, Any]):
    """Test that MetaData raises an error for invalid data."""

    is_base_data_valid = MetaData(**base_data)
    assert is_base_data_valid is not None

    for kw in ("filename", "id"):
        dup = base_data.copy()
        dup.pop(kw)
        with pytest.raises(TypeError):
            _ = MetaData(**dup)
            assert False, f"It should not be allowed that {kw} is missing"


def test_missing_non_required_fields(base_data: Dict[str, Any]):
    """Test that MetaData raises an error for invalid data."""

    for kw in ("keywords", "title", "description"):
        dup = base_data.copy()
        dup.pop(kw)
        result = MetaData(**dup)
        assert result is not None, f"It should be allowed that {kw} is missing"


def test_metadata(base_data: Dict[str, Any]):

    metadata = MetaData(**base_data)
    assert metadata.id == base_data["id"]
    assert metadata.filename == base_data["filename"]
    for kw in sorted(set(base_data["keywords"])):
        assert kw.lower() in metadata.keywords

    kws = [kw.lower() for kw in sorted(set(base_data["keywords"]))]
    for kw in kws:
        assert kw in metadata.keywords

    assert len(kws) == len(metadata.keywords)

    for kw in kws:
        assert kw in metadata.pexels

    for kw in kws:
        assert "#" + kw.replace(" ", "") in metadata.instagram

    metadata.keywords = SortedSet()
    assert metadata.pexels == ""
    assert metadata.instagram == ""


def test_append_keywords(sample: MetaData):
    """Test the append_keywords method of MetaData."""
    kws = {kw for kw in sample.keywords}
    sample.append_keywords(kws)
    assert Counter(sample.keywords) == Counter(kws), "Adding an existing keyword should avoid duplicates"
    kws.add("extra")
    sample.append_keywords(["extra"])
    assert Counter(sample.keywords) == Counter(kws), "append_keywords should add new keywords"

    sample.append_keywords([])
    assert Counter(sample.keywords) == Counter(kws), "adding an empty list should do nothing"


def test_remove_keywords(sample: MetaData):
    """Test the remove_keywords method of MetaData."""
    kws = {kw for kw in sample.keywords}

    sample.remove_keywords([])
    assert Counter(kws) == Counter(sample.keywords)

    first = next(iter(kws))
    sample.remove_keywords([first])
    assert first not in sample.keywords, "remove_keywords should remove specified keywords"

    kws.remove(first)
    assert Counter(kws) == Counter(sample.keywords)

    sample.remove_keywords(["non existing"])
    assert Counter(kws) == Counter(sample.keywords)

    sample.remove_keywords(kws)
    assert len(sample.keywords) == 0


def test_replace_keywords(sample: MetaData):
    """Test the replace_keywords method of MetaData."""
    new_keywords = ["new", "keywords"]
    sample.replace_keywords(new_keywords)
    assert Counter(new_keywords) == Counter(
        sample.keywords
    ), "replace_keywords should replace all existing keywords with new ones"
    new_keywords = ["Caps", "dup", "dup"]
    sample.replace_keywords(new_keywords)
    assert Counter(["caps", "dup"]) == Counter(
        sample.keywords
    ), "replace_keywords should remove duplicates and capitalization"


def test_to_dict(base_data: Dict[str, Any]):
    mddict = MetaData(**base_data).to_dict()
    for key in ["id", "filename", "description", "title"]:
        assert mddict[key] == base_data[key]
    assert Counter(mddict["keywords"]) == Counter({k.lower() for k in base_data["keywords"]})


def test_to_db_metadata(sample: MetaData):
    """Test if the conversion to DbMetadata is done correctly"""
    id, dbmeta = sample.to_db_metadata()
    assert dbmeta.filename == sample.filename
    assert dbmeta.title == sample.title
    assert dbmeta.description == sample.description
    assert Counter(dbmeta.keywords) == Counter(sample.keywords)
    assert id == sample.id


def test_from_db_metdata(sample: MetaData):
    id, dbmeta = sample.to_db_metadata()
    result = MetaData.from_db_metadata(id, dbmeta)
    assert sample == result

def test_from_db_metadata_dict(sample: MetaData):
    copy=MetaData(**sample.to_dict())
    copy.id=sample.id+1
    copy.filename="anotherfile.jpg"
    mddict={sample.id:sample.to_db_metadata()[1], copy.id:copy.to_db_metadata()[1]}
    result=MetaData.from_db_metadata_dict(mddict)
    assert copy in result
    assert sample in result
    assert len(result)==2
