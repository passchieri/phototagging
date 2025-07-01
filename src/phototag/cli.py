import argparse
from .db import Db
from .meta import Meta
from .phototag import PhotoTag
import json

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .phototag.env from home directory
load_dotenv(dotenv_path=Path.home() / ".phototag.env")
# "c9245585-facb-4737-b91f-b7a32ca098ad"
URL = os.getenv("PHOTOTAG_URL", "https://server.phototag.ai/api/keywords")
TOKEN = os.getenv("PHOTOTAG_TOKEN", "")
DB_FILE = os.getenv("PHOTOTAG_DB", str(Path.home() / ".phototag_db.json"))


def main():
    parser = argparse.ArgumentParser(
        description="PhotoTagging CLI. Fetch metadata for images using PhotoTag API. The results are stored"
        " in a local database, and reused. Defaults for URL, token and database file can be set in environment variables"
        "or in  ~/.phototag.env file, prepending the parameter with PHOTOTAG_, e.g. PHOTOTAG_URL.",
        epilog="Example: phototag -i image1.jpg -i image2.jpg -p title -p description",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-u",
        "--url",
        default=URL,
        help="API URL",
    )
    parser.add_argument(
        "-t",
        "--token",
        default=TOKEN,
        help="API token",
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
        help="Field to print (can be used multiple times). Can also be all, shutterstock, or shutter)",
    )
    args = parser.parse_args()
    try:
        if not args.token:
            raise ValueError(
                "API token is required. Set it with -t or in $HOME/.phototag.env"
            )
        db = Db(args.db)
        phototag = PhotoTag(
            url=args.url,
            token=args.token,
        )
        meta = Meta(db, phototag)
        fields = args.print
        if fields:
            if "shutterstock" in fields or "shutter" in fields:
                if len(fields) > 1:
                    raise ValueError(
                        "The 'shutterstock' field cannot be used with other fields."
                    )
                fields = ["shutter"]
                print(
                    "Filename,Description,Keywords,Categories,Editorial,Mature content,illustration"
                )
            if "all" in fields:
                if len(fields) > 1:
                    raise ValueError(
                        "The 'all' field cannot be used with other fields."
                    )
                fields = [
                    "filename",
                    "title",
                    "pexels",
                    "instagram",
                    "description",
                ]

        for image in args.image:
            result = meta.get_or_fetch(image)
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
                data.update(
                    {"pexels": result.pexels(), "instagram": result.instagram()}
                )
                print(
                    json.dumps(
                        data,
                        indent=4,
                    )
                )
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    main()
