import argparse
import os
from pathlib import Path
from typing import Iterable, List, Optional

from dotenv import load_dotenv

from .db import Db
from .exif import ExifManager
from .metadata import Metadata
from .metadata_manager import MetadataManager
from .phototag import PhotoTag
from .scanner import Scanner

# Load .phototag.env from home directory
load_dotenv(dotenv_path=Path.home() / ".phototag.env")
URL = os.getenv("PHOTOTAG_URL", "https://server.phototag.ai/api/keywords")
TOKEN = os.getenv("PHOTOTAG_TOKEN", "")
DB_FILE = os.getenv("PHOTOTAG_DB", str(Path.home() / ".phototag_db.json"))


def _create_parser():
    """
    Create the argument parser for the CLI.
    """
    parser = argparse.ArgumentParser(
        description="PhotoTagging CLI. Fetch metadata for images using PhotoTag API. The results are stored"
        " in a local database, and reused. Defaults for URL, token and database file can be set in environment "
        "variables or in  ~/.phototag.env file, prepending the parameter with PHOTOTAG_, e.g. PHOTOTAG_URL.",
        epilog="Example: phototag -t aap,noot -p title -p description image1.jpg image2.jpg",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Show all records in the database",
    )
    parser.add_argument(
        "-d",
        "--db",
        default=DB_FILE,
        help="Database file name",
    )
    parser.add_argument(
        "-e",
        "--exif",
        default="none",
        help="Read or write metadata",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force getting new info",
    )
    parser.add_argument(
        "-p",
        "--print",
        action="append",
        default=[],
        help="Field to print (can be used multiple times). "
        "Can also be all, shutterstock, shutter, pexels, or instagram.",
    )
    parser.add_argument(
        "-r",
        "--remove-tags",
        type=lambda s: [tag.strip() for tag in s.split(",")],
        default=[],
        help="tags to be removed from each image (comma-separated)",
    )
    parser.add_argument(
        "-s",
        "--scan",
        default="",
        help="Scan for images",
    )
    parser.add_argument(
        "-t",
        "--tags",
        type=lambda s: [tag.strip() for tag in s.split(",")],
        default=[],
        help="tags to be added to each image (comma-separated)",
    )
    parser.add_argument(
        "--token",
        default=TOKEN,
        help="API token",
    )
    parser.add_argument(
        "-u",
        "--url",
        default=URL,
        help="API URL",
    )
    parser.add_argument(
        "-x",
        "--delete",
        action="store_true",
        help="Delete an entry",
    )

    parser.add_argument(
        "image",
        nargs="*",
        default=[],
        help="Image file names (can be used multiple times)",
    )
    return parser


def _process_fields(fields: Optional[list[str]]) -> list[str]:
    """Process the fields argument and handle special cases."""
    if not fields:
        fields = ["all"]

    if "shutterstock" in fields or "shutter" in fields:
        if len(fields) > 1:
            raise ValueError("The 'shutterstock' field cannot be used with other fields.")
        print("Filename,Description,Keywords,Categories,Editorial,Mature content,illustration")
        return ["shutter"]

    if "all" in fields:
        if len(fields) > 1:
            raise ValueError("The 'all' field cannot be used with other fields.")
        return list(Metadata.model_fields)

    return fields


def _print_result(result: Metadata | None, fields: list[str]) -> None:
    if result is None:
        print("No metadata found.")
        return

    if "shutter" not in fields:
        for field in fields:
            attr = getattr(result, field, None)
            title = f"{field:<12}"[:12]
            if attr is None:
                print(f"No such field: {field}")
            elif callable(attr):
                print(title + ": " + str(attr()))
            elif isinstance(attr, list | set):
                print(title + ": " + ", ".join(attr))  # type: ignore
            else:
                print(title + ": " + str(attr))
        print("------------------------")
    else:
        print(f'{result.filename},{result.title},"{result.pexels}",,,no,')


def validate_args(args: argparse.Namespace) -> None:
    """Validate the command-line arguments."""
    if not args.token:
        raise ValueError("API token is required. Set it with --token or in $HOME/.phototag.env")
    if args.all and args.scan:
        raise ValueError("Cannot use --all and --scan together.")
    if args.delete and args.all:
        raise ValueError("Cannot use --delete with --all.")
    if args.delete and args.scan:
        raise ValueError("Cannot use --delete with --scan.")
    if args.delete and not args.image:
        raise ValueError("At least one image file must be specified for deletion.")
    if not args.image and not (args.all or args.scan):
        raise ValueError("At least one image file must be specified, or use --all or --scan.")


def main() -> int:
    try:
        parser = _create_parser()
        args = parser.parse_args()
        validate_args(args)
        default_keywords = args.tags if args.tags else None
        keywords_to_remove = args.remove_tags if args.remove_tags else None

        db = Db(args.db)
        phototag = PhotoTag(
            url=args.url,
            token=args.token,
        )
        meta = MetadataManager(db, phototag)
        fields: List[str] = _process_fields(args.print)
        images: Iterable[str] = args.image if not args.all else [img.filename for img in meta.all()]

        if args.delete:
            return delete(meta, images)

        if args.scan:
            scanner = Scanner(meta, args.scan)
            images = [str(img) for img in scanner.scan(not args.force)]

        # default action is print
        show(
            meta,
            images,
            fields,
            force=args.force,
            add_exif=args.exif == "read",
            required_keywords=default_keywords,
            keywords_to_remove=keywords_to_remove,
        )

    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


def delete(meta: MetadataManager, images: Iterable[str]):
    for image in images:
        result = meta.get_by_filename(image)
        if result:
            meta.delete_by_id(result.id)
            print(f"Deleted record for file {image}")
        else:
            raise ValueError(f"Cannot find record for image {image}")
    return 0


def show(
    meta: MetadataManager,
    images: Iterable[str],
    fields: List[str],
    force: bool = False,
    add_exif: bool = False,
    required_keywords: Optional[List[str]] = None,
    keywords_to_remove: Optional[List[str]] = None,
):
    for image in images:
        result = meta.get_or_create(
            full_path=Path(image),
            force=force,
            required_keywords=required_keywords,
            keywords_to_remove=keywords_to_remove,
        )
        if result and add_exif:
            with ExifManager(image) as exif:
                exif.add_location_info_to_keywords()
                exif_keys = exif.keywords
            meta.update_keywords(result, keywords_to_add=exif_keys)
        _print_result(result, fields)


if __name__ == "__main__":
    main()  # pragma: no cover
