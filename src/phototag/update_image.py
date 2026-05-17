from pyexiv2 import ImageMetadata  # type: ignore

from typing import Any, TypeVar
from collections.abc import MutableMapping

T = TypeVar("T", bound=MutableMapping[str, Any])

CITY_KEY = "Iptc.Application2.City"
COUNTRY_KEY = "Iptc.Application2.CountryName"
KEYWORD_KEYS = ("Xmp.dc.subject", "Xmp.lr.hierarchicalSubject", "Iptc.Application2.Keywords")


def read_metadata(image_path: str) -> ImageMetadata:
    metadata = ImageMetadata(image_path)
    metadata.read()
    return metadata


def write_metadata(metadata: ImageMetadata) -> ImageMetadata:
    metadata.write()
    return metadata


def add_keywords_to_metadata(metadata: T, keywords: list[str], include_location_info: bool = False) -> T:
    """
    Add keywords/tags to image metadata.
    This updates EXIF, IPTC, and XMP metadata.
    """

    if include_location_info:
        if "Iptc.Application2.City" in metadata:
            city = metadata["Iptc.Application2.City"].value
            keywords.append(" ".join(city).lower())

        if "Iptc.Application2.CountryName" in metadata:
            country = metadata["Iptc.Application2.CountryName"].value
            keywords.append(" ".join(country).lower())

    keywords = list(set(keywords))
    keywords.sort()

    for key in KEYWORD_KEYS:
        metadata[key] = keywords

    return metadata


def remove_all_keywords_from_metadata(metadata: T) -> T:
    for key in KEYWORD_KEYS:
        if key in metadata:
            del metadata[key]
    return metadata
