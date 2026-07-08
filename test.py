import os
from pathlib import Path

from dotenv import load_dotenv

from phototagging.db import Db
from phototagging.metadata_manager import MetadataManager
from phototagging.phototag import PhotoTag
from phototagging.scanner import Scanner

load_dotenv(dotenv_path=Path.home() / ".phototag.env")
URL = os.getenv("PHOTOTAG_URL", "https://server.phototag.ai/api/keywords")
TOKEN = os.getenv("PHOTOTAG_TOKEN", "")
DB_FILE = os.getenv("PHOTOTAG_DB", str(Path.home() / ".phototag_db.json"))


def main():
    db = Db(DB_FILE)
    phototag = PhotoTag(
        url=URL,
        token=TOKEN,
    )
    meta = MetadataManager(db, phototag)
    scanner = Scanner(meta, "./resources")
    images = scanner.scan()
    print(images)


if __name__ == "__main__":
    main()
