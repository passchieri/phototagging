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
    assert metadata.to_dict() == data, "to_dict should return the original data"
