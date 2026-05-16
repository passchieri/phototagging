
import pytest
from unittest.mock import patch, MagicMock
from phototag.update_image import CITY_KEY, COUNTRY_KEY, KEYWORD_KEYS, add_keywords_to_metadata


def test_add_keywords_to_metadata():
    """Test adding keywords to a JPEG image."""
    keywords = ["test", "keyword", "phototagging"]
    
    # Create mock image instance
    mock_metadata = MagicMock()
    mock_container={}
    mock_metadata.__getitem__.side_effect = mock_container.__getitem__
    mock_metadata.__setitem__.side_effect = mock_container.__setitem__
    mock_metadata.__contains__.side_effect = mock_container.__contains__

    result = add_keywords_to_metadata(mock_metadata, keywords)
    
    # Verify all keys are present and contain the sorted keywords
    for key in KEYWORD_KEYS:
        assert key in result, f"Key '{key}' not found in metadata result"
        metadata_entry = result[key]
        for keyword in keywords:
            assert keyword in metadata_entry, f"Keyword '{keyword}' not found in result['{key}']"
    
def test_add_keywords_to_metadata_with_location_info():
    """Test adding keywords to a JPEG image."""
    keywords = ["test", "keyword", "phototagging"]

    
    # Create mock image instance
    mock_metadata = MagicMock()
    mock_container={}
    mock_metadata.__getitem__.side_effect = mock_container.__getitem__
    mock_metadata.__setitem__.side_effect = mock_container.__setitem__
    mock_metadata.__contains__.side_effect = mock_container.__contains__

    mock_container[CITY_KEY] = MagicMock()
    mock_container[CITY_KEY].value = ["Den Haag"]
    mock_container[COUNTRY_KEY] = MagicMock()
    mock_container[COUNTRY_KEY].value = ["Netherlands"]
    
    result = add_keywords_to_metadata(mock_metadata, keywords,True)
    
    # Verify all keys are present and contain the sorted keywords
    for key in KEYWORD_KEYS:
        assert key in result, f"Key '{key}' not found in metadata result"
        metadata_entry = result[key]
        assert "den haag" in metadata_entry, f"Keyword 'den haag' not found in result['{key}']"
        assert "netherlands" in metadata_entry, f"Keyword 'netherlands' not found in result['{key}']"
