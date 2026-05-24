from pathlib import Path
from typing import Protocol
from datetime import datetime, timedelta
import re

from .metadata_manager import MetadataManager


class ImageFilter(Protocol):  # pragma: no cover
    """Protocol for image filtering functions."""

    def __call__(self, images: list[Path]) -> list[Path]:
        """Filter a set of image paths and return the filtered set."""
        ...


def create_age_filter(max_days: int) -> ImageFilter:
    """Create a filter function that keeps only images modified within the last N days.

    Args:
        max_days: Maximum age of files in days

    Returns:
        A filter function that takes a set of image paths and returns filtered paths
    """

    def filter_by_age(images: list[Path]) -> list[Path]:
        cutoff = datetime.now() - timedelta(days=max_days)
        return [image_path for image_path in images if datetime.fromtimestamp(image_path.stat().st_mtime) >= cutoff]

    return filter_by_age


def create_max_files_filter(max_files: int) -> ImageFilter:
    """Create a filter function that limits to the first N files.

    Args:
        max_files: Maximum number of files to keep

    Returns:
        A filter function that takes a set of image paths and returns filtered paths
    """

    def filter_by_max_files(images: list[Path]) -> list[Path]:
        return images[:max_files]

    return filter_by_max_files


def create_regexp_filter(pattern: str) -> ImageFilter:
    """Create a filter function that matches filenames against a regexp pattern.

    Args:
        pattern: Regular expression pattern to match filenames

    Returns:
        A filter function that takes a set of image paths and returns filtered paths
    """
    regex = re.compile(pattern)

    def filter_by_regexp(images: list[Path]) -> list[Path]:
        return [image_path for image_path in images if regex.search(image_path.name)]

    return filter_by_regexp


def create_db_filter(metadata_managaer: MetadataManager) -> ImageFilter:
    """Create a filter function that keeps only images with existing database entries.

    Args:
        metadata_managaer: Metadata manager instance to check existing filenames

    Returns:
        A filter function that takes a set of image paths and returns filtered paths
    """

    def filter_by_db(images: list[Path]) -> list[Path]:
        existing = {record.filename for record in metadata_managaer.all()}
        return [image_path for image_path in images if str(image_path) in existing or image_path.name in existing]

    return filter_by_db
