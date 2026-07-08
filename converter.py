from datetime import datetime
from pathlib import Path
from typing import List

from tinydb import TinyDB

from phototagging.metadata import Metadata


def convert() -> None:
    # db_path = Path("./existing_db.json").resolve()
    db_path = Path("/Users/igor/.phototag_db.json").resolve()
    db = TinyDB(db_path)
    new_db_path = Path("./new_db.json")
    new_db_path.unlink(True)
    new_db = TinyDB("./new_db.json")
    processed: List[str] = []
    results = db.all()
    for result in results:
        metadata = Metadata.model_validate(result)
        if metadata.id in processed:
            continue
        if not metadata.full_path.exists():
            continue
        processed.append(metadata.id)
        path = metadata.full_path
        create_date = datetime.fromtimestamp(path.stat().st_ctime)
        metadata.create_date = create_date
        n = Metadata(**metadata.model_dump())
        new_db.insert(n.model_dump(mode="json"))  # type: ignore
    print(f"{len(processed)} entries in new db {new_db_path} from {len(results)} entries in {db_path}")


# def read_back():
#     new_db = TinyDB("./new_db.json")
#     results = new_db.all()
#     for result in results:
#         metadata = NewMetadata.model_validate(result)
#         print(metadata)


def main():
    convert()
    # read_back()


if __name__ == "__main__":
    main()
