import argparse
from typing import Optional
from .db import Db
from .metadata_manager import MetadataManager
from .phototag import PhotoTag
import json

import os
from pathlib import Path
from dotenv import load_dotenv

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
        "-u",
        "--url",
        default=URL,
        help="API URL",
    )
    parser.add_argument(
        "--token",
        default=TOKEN,
        help="API token",
    )
    parser.add_argument(
        "-t",
        "--tags",
        type=lambda s: [tag.strip() for tag in s.split(",")],
        default=[],
        help="tags to be added to each image (comma-separated)",
    )

    parser.add_argument(
        "-r",
        "--remove-tags",
        type=lambda s: [tag.strip() for tag in s.split(",")],
        default=[],
        help="tags to be removed from each image (comma-separated)",
    )

    parser.add_argument(
        "-d",
        "--db",
        default=DB_FILE,
        help="Database file name",
    )
    parser.add_argument(
        "image",
        nargs="*",
        default=[],
        help="Image file names (can be used multiple times)",
    )
    parser.add_argument(
        "-p",
        "--print",
        action="append",
        default=[],
        help="Field to print (can be used multiple times). "
        "Can also be all, shutterstock, shutter, pexels, or instagram.",
    )
    return parser


def _process_fields(fields: Optional[list[str]]) -> Optional[list[str]]:
    """Process the fields argument and handle special cases."""
    if not fields:
        return fields

    if "shutterstock" in fields or "shutter" in fields:
        if len(fields) > 1:
            raise ValueError(
                "The 'shutterstock' field cannot be used with other fields."
            )
        print(
            "Filename,Description,Keywords,Categories,Editorial,Mature content,illustration"
        )
        return ["shutter"]

    if "all" in fields:
        if len(fields) > 1:
            raise ValueError("The 'all' field cannot be used with other fields.")
        return [
            "filename",
            "title",
            "pexels",
            "instagram",
            "description",
        ]

    return fields


def _print_result(result, fields: list[str]):
    if fields and "shutter" not in fields:
        for field in fields:
            attr = getattr(result, field, None)
            if attr is None:
                print(f"No such field: {field}")
            elif callable(attr):
                print(attr())
            else:
                print(attr)
        print("------------------------")
    elif fields and "shutter" in fields:
        print(f'{result.filename},{result.title},"{result.pexels()}",,,no,')
    else:
        data = result.to_dict()
        data.update({"pexels": result.pexels(), "instagram": result.instagram()})
        print(
            json.dumps(
                data,
                indent=4,
            )
        )


def main():
    parser = _create_parser()
    args = parser.parse_args()
    default_tags = args.tags if args.tags else None
    removed_tags = args.remove_tags if args.remove_tags else None
    try:
        if not args.token:
            raise ValueError(
                "API token is required. Set it with --token or in $HOME/.phototag.env"
            )
        db = Db(args.db)
        phototag = PhotoTag(
            url=args.url,
            token=args.token,
        )
        meta = MetadataManager(db, phototag)
        fields = _process_fields(args.print)

        if args.all:
            records = meta.all()
            for record in records:
                _print_result(record, fields)
            return 0

        for image in args.image:
            result = meta.get_or_fetch(
                image, default_tags=default_tags, removed_tags=removed_tags
            )
            _print_result(result, fields)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    main()  # pragma: no cover
