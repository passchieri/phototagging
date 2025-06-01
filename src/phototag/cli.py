import argparse
from .db import Db
from .meta import Meta
import json


def main():
    parser = argparse.ArgumentParser(description="PhotoTagging CLI")
    parser.add_argument(
        "-d",
        "--db",
        default="results.json",
        help="Database file name (default: results.json)",
    )
    parser.add_argument(
        "-i", "--image", required=True, help="Image file name (required)"
    )
    parser.add_argument(
        "-p",
        "--print",
        action="append",
        default=[],
        help="Field to print (can be used multiple times)",
    )
    args = parser.parse_args()

    try:
        db = Db(args.db)
        meta = Meta(db)
        result = meta.get_or_fetch(args.image)
        if args.print:
            fields = args.print
            if "all" in fields:
                fields = [
                    "filename",
                    "title",
                    "pexels",
                    "instagram",
                    "description",
                ]
            for field in fields:
                attr = getattr(result, field, None)
                if attr is None:
                    print(f"No such field: {field}")
                elif callable(attr):
                    print(attr())
                else:
                    print(attr)
        else:
            data = result.to_dict()
            data.update({"pexels": result.pexels(), "instagram": result.instagram()})
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
