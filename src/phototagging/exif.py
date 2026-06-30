from collections.abc import MutableMapping
from pathlib import Path
from types import TracebackType
from typing import Any, Set, TypeVar

from pyexiv2 import ImageMetadata  # type: ignore

T = TypeVar("T", bound=MutableMapping[str, Any])

CITY_KEY = "Iptc.Application2.City"
COUNTRY_KEY = "Iptc.Application2.CountryName"
KEYWORD_KEYS = ("Xmp.dc.subject", "Xmp.lr.hierarchicalSubject", "Iptc.Application2.Keywords")


class ExifMetadata(ImageMetadata):
    commit: bool = True  # If True, write changes to file on exit of context manager

    def __init__(self, base: ImageMetadata, auto_commit: bool = True):
        # Do NOT call super().__init__ — we are wrapping, not constructing
        self._base = base
        self.commit = auto_commit

    @property
    def city(self) -> str | None:
        if CITY_KEY in self._base:
            city = self._base[CITY_KEY].value
            return " ".join(city).lower()
        return None

    @property
    def country(self) -> str | None:
        if COUNTRY_KEY in self._base:
            country = self._base[COUNTRY_KEY].value
            return " ".join(country).lower()
        return None

    @property
    def keywords(self) -> list[str]:
        keywords: Set[str] = set()
        for key in KEYWORD_KEYS:
            if key in self._base:
                keywords.update(self._base[key].value)
        return list(keywords)

    def clear_keywords(self) -> None:
        for key in KEYWORD_KEYS:
            if key in self._base:
                del self._base[key]

    def add_location_info_to_keywords(self) -> None:
        self.add_keywords([], include_location_info=True)

    def add_keywords(self, keywords: list[str], include_location_info: bool = False) -> None:
        _keywords = set(self.keywords)  # Start with existing keywords
        if include_location_info:
            if self.city:
                _keywords.add(self.city)
            if self.country:
                _keywords.add(self.country)

        _keywords.update(keywords)
        keywords = sorted(list(set(_keywords)))

        for key in KEYWORD_KEYS:
            self._base[key] = keywords

    # --- Delegate everything else to the wrapped object ---
    def __getattr__(self, name: str) -> Any:
        # Called only if attribute not found on self
        return getattr(self._base, name)

    def __setattr__(self, name: str, value: Any):
        # Allow normal setting for our own attributes
        if name.startswith("_"):
            return super().__setattr__(name, value)
        # Forward everything else to the wrapped metadata
        return setattr(self._base, name, value)


class ExifManager:
    """
    Class to manage EXIF metadata for photos.
    """

    exif: ExifMetadata | None = None

    def __init__(self, filename: str | Path):
        if isinstance(filename, Path):
            self.file = filename
        else:
            self.file = Path(filename)

    def __enter__(self) -> ExifMetadata:
        self.exif = ExifMetadata(read_exif(self.file.as_posix()))
        return self.exif

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        assert self.exif is not None, "ExifManager.__exit__ called without a valid exif object"
        if exc_type is not None:
            print(f"Not saving, because an error occurred: {exc_value}")
            return
        if self.exif.commit and exc_type is None:
            self.exif.write()
        self.exif = None


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


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test EXIF metadata management")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument(
        "--keyword",
        "-k",
        action="append",
        nargs="+",
        help="Add one or more keywords (can be repeated)",
    )
    args = parser.parse_args()

    with ExifManager(args.image_path) as exif:
        print("City:", exif.city)
        print("Country:", exif.country)
        print("Current keywords:", exif.keywords)
        exif.clear_keywords()
        print("Current keywords:", exif.keywords)
        exif.add_location_info_to_keywords()
        print("Current keywords:", exif.keywords)
        keywords = [kw for group in args.keyword for kw in group]
        exif.add_keywords(keywords)
        print("Current keywords:", exif.keywords)


if __name__ == "__main__":
    main()
