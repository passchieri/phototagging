import argparse
from phototag.db import Db
from phototag.meta import Meta


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
            for field in args.print:
                attr = getattr(result, field, None)
                if attr is None:
                    print(f"[No such field: {field}]")
                elif callable(attr):
                    print(attr())
                else:
                    print(attr)
        else:
            print(result)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    main()
