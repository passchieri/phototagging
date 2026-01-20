from phototag.metadata import MetaData


def test_missing_title():
    """Test that MetaData raises an error for invalid data."""
    try:
        MetaData(
            id="passchier-090.jpg",
            filename="passchier-090.jpg",
            keywords=["container ship", "river navigation"],
            # title="Container ship navigates river waters near buoy at dusk in peaceful setting with clouds",
            description="A large red container ship is traveling along a river, loaded with colorful cargo containers stacked high on its deck.",
        )
    except TypeError as e:
        assert False, "MetaData should not raise TypeError for missing title"
        assert "missing 1 required positional argument: 'filename'" in str(e)


def test_missing_keywords():
    """Test that MetaData raises an error for invalid data."""
    try:
        metadata1 = MetaData(
            id="passchier-090.jpg",
            filename="passchier-090.jpg",
            # keywords=["container ship", "river navigation"],
            title="Container ship navigates river waters near buoy at dusk in peaceful setting with clouds",
            description="A large red container ship is traveling along a river, loaded with colorful cargo containers stacked high on its deck.",
        )
        metadata2 = MetaData(
            id="passchier-090.jpg",
            filename="passchier-090.jpg",
            # keywords=["container ship", "river navigation"],
            title="Container ship navigates river waters near buoy at dusk in peaceful setting with clouds",
            description="A large red container ship is traveling along a river, loaded with colorful cargo containers stacked high on its deck.",
        )
    except TypeError as e:
        assert False, "MetaData should not raise TypeError for missing keywords"

    assert (
        metadata1.keywords == []
    ), "MetaData should have empty keywords if not provided"
    metadata1.keywords.append("container ship")
    assert (
        metadata2.keywords == []
    ), "MetaData instances should not share the same keywords list"


def test_missing_filename():
    """Test that MetaData raises an error for invalid data."""
    try:
        MetaData(
            id="passchier-090.jpg",
            # filename="passchier-090.jpg",
            keywords=["container ship", "river navigation"],
            title="Container ship navigates river waters near buoy at dusk in peaceful setting with clouds",
            description="A large red container ship is traveling along a river, loaded with colorful cargo containers stacked high on its deck.",
        )
    except TypeError as e:
        assert "missing 1 required positional argument: 'filename'" in str(e)
    else:
        assert False, "MetaData should raise TypeError for missing filename"


def test_metadata():

    data = {
        "id": "passchier-090.jpg",
        "filename": "passchier-090.jpg",
        "keywords": [
            "container ship",
            "river navigation",
            "cargo transport",
            "evening light",
            "transportation",
            "shipping",
            "red buoy",
            "waterways",
            "peaceful setting",
            "clouds",
            "commercial activity",
            "green landscape",
            "freight",
            "dusk",
            "maritime",
            "shipping industry",
            "vessels",
            "waterway",
            "port",
            "nautical",
        ],
        "title": "Container ship navigates river waters near buoy at dusk in peaceful setting with clouds",
        "description": "A large red container ship is traveling along a river, loaded with colorful cargo containers stacked high on its deck. The vessel moves steadily past a bright red navigation buoy that marks the waterway. The sky is filled with soft clouds, reflecting the warm hues of dusk, creating a serene atmosphere. Lush greenery lines the riverbank, enhancing the peacefulness of the scene.",
    }
    metadata = MetaData(**data)
    assert metadata.id == "passchier-090.jpg"
    assert metadata.filename == "passchier-090.jpg"
    assert "clouds" in metadata.keywords
    assert "peaceful setting" in metadata.keywords

    assert (
        metadata.title
        == "Container ship navigates river waters near buoy at dusk in peaceful setting with clouds"
    )
    assert (
        metadata.description
        == "A large red container ship is traveling along a river, loaded with colorful cargo containers stacked high on its deck. The vessel moves steadily past a bright red navigation buoy that marks the waterway. The sky is filled with soft clouds, reflecting the warm hues of dusk, creating a serene atmosphere. Lush greenery lines the riverbank, enhancing the peacefulness of the scene."
    )
    assert "waterway, " in metadata.pexels()
    assert "#clouds" in metadata.instagram()
    assert "#shippingindustry" in metadata.instagram()
    result = metadata.to_dict()
    expected = {**data, "keywords": result["keywords"]}
    assert (
        result == expected
    ), "to_dict should return the original data (keywords may differ in type)"
    assert set(result["keywords"]) == set(
        data["keywords"]
    ), "to_dict keywords should match original set of keywords"


def test_append_keywords():
    """Test the append_keywords method of MetaData."""
    metadata = MetaData(
        id="test.jpg",
        filename="test.jpg",
        keywords=["sunset", "beach"],
        title="Sunset at the Beach",
        description="A beautiful sunset at the beach.",
    )
    metadata.append_keywords(["ocean", "sunset", "vacation"])
    assert set(metadata.keywords) == {
        "sunset",
        "beach",
        "ocean",
        "vacation",
    }, "append_keywords should add new keywords and avoid duplicates"


def test_remove_keywords():
    """Test the remove_keywords method of MetaData."""
    metadata = MetaData(
        id="test.jpg",
        filename="test.jpg",
        keywords=["sunset", "beach", "ocean", "vacation", "travel"],
        title="Sunset at the Beach",
        description="A beautiful sunset at the beach.",
    )
    metadata.remove_keywords(["sunset", "vacation"])
    assert set(metadata.keywords) == {
        "beach",
        "ocean",
        "travel",
    }, "remove_keywords should remove specified keywords"


def test_remove_keywords_partial_match():
    """Test remove_keywords with some keywords not in the list."""
    metadata = MetaData(
        id="test.jpg",
        filename="test.jpg",
        keywords=["sunset", "beach", "ocean"],
        title="Sunset at the Beach",
        description="A beautiful sunset at the beach.",
    )
    metadata.remove_keywords(["sunset", "mountain", "vacation"])
    assert set(metadata.keywords) == {
        "beach",
        "ocean",
    }, "remove_keywords should only remove keywords that exist"


def test_remove_all_keywords():
    """Test remove_keywords when removing all keywords."""
    metadata = MetaData(
        id="test.jpg",
        filename="test.jpg",
        keywords=["sunset", "beach"],
        title="Sunset at the Beach",
        description="A beautiful sunset at the beach.",
    )
    metadata.remove_keywords(["sunset", "beach"])
    assert metadata.keywords == [], "remove_keywords should allow removing all keywords"


def test_remove_keywords_empty_list():
    """Test remove_keywords with an empty list of keywords to remove."""
    metadata = MetaData(
        id="test.jpg",
        filename="test.jpg",
        keywords=["sunset", "beach", "ocean"],
        title="Sunset at the Beach",
        description="A beautiful sunset at the beach.",
    )
    metadata.remove_keywords([])
    assert set(metadata.keywords) == {
        "sunset",
        "beach",
        "ocean",
    }, "remove_keywords with empty list should not modify keywords"


def test_remove_keywords_from_empty():
    """Test remove_keywords from an empty keywords list."""
    metadata = MetaData(
        id="test.jpg",
        filename="test.jpg",
        keywords=[],
        title="Sunset at the Beach",
        description="A beautiful sunset at the beach.",
    )
    metadata.remove_keywords(["sunset", "beach"])
    assert metadata.keywords == [], "remove_keywords on empty list should remain empty"
