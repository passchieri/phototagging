from collections.abc import MutableMapping
from typing import Any, TypeVar

from pyexiv2 import ImageMetadata  # type: ignore

T = TypeVar("T", bound=MutableMapping[str, Any])

CITY_KEY = "Iptc.Application2.City"
COUNTRY_KEY = "Iptc.Application2.CountryName"
KEYWORD_KEYS = ("Xmp.dc.subject", "Xmp.lr.hierarchicalSubject", "Iptc.Application2.Keywords")


def read_exif(image_path: str) -> ImageMetadata:  # pragma: no cover
    exif = ImageMetadata(image_path)
    exif.read()
    return exif


def write_exif(exif: ImageMetadata) -> ImageMetadata:  # pragma: no cover
    exif.write()
    return exif


def add_keywords_to_metadata(exif: T, keywords: list[str], include_location_info: bool = False) -> T:
    """
    Add keywords/tags to image metadata.
    This updates EXIF, IPTC, and XMP metadata.
    """

    if include_location_info:
        if CITY_KEY in exif:
            city = exif[CITY_KEY].value
            keywords.append(" ".join(city).lower())

        if COUNTRY_KEY in exif:
            country = exif[COUNTRY_KEY].value
            keywords.append(" ".join(country).lower())

    keywords = list(set(keywords))
    keywords.sort()

    for key in KEYWORD_KEYS:
        exif[key] = keywords

    return exif


def remove_all_keywords_from_exif(exif: T) -> T:
    for key in KEYWORD_KEYS:
        if key in exif:
            del exif[key]
    return exif
