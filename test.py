import os
from pathlib import Path

from dotenv import load_dotenv

from folder_manager.folder_manager import FolderManager

load_dotenv(dotenv_path=Path.home() / ".phototag.env")
URL = os.getenv("PHOTOTAG_URL", "https://server.phototag.ai/api/keywords")
TOKEN = os.getenv("PHOTOTAG_TOKEN", "")
DB_FILE = os.getenv("PHOTOTAG_DB", str(Path.home() / ".phototag_db.json"))


def main():
    # db = Db(DB_FILE)
    # phototag = PhotoTag(
    #     url=URL,
    #     token=TOKEN,
    # )
    # meta = MetadataManager(db, phototag)
    # for dir in meta.all_dirs():
    #     print(str(dir))

    fm = FolderManager("/Users/igor/Pictures/")
    for c in fm.children("Lightroom Saved Photos"):
        print(c.name, c.is_dir())


if __name__ == "__main__":
    main()
