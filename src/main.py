from phototagging.cli import main

# import os
# from pathlib import Path
# from dotenv import load_dotenv
# from tinydb import TinyDB
# def transform() -> None:
#     # Load .phototag.env from home directory
#     load_dotenv(dotenv_path=Path.home() / ".phototag.env")
#     # URL = os.getenv("PHOTOTAG_URL", "https://server.phototag.ai/api/keywords")
#     # TOKEN = os.getenv("PHOTOTAG_TOKEN", "")
#     DB_FILE = os.getenv("PHOTOTAG_DB", str(Path.home() / ".phototag_db.json"))
#     _db=TinyDB(DB_FILE)
#     all= _db.all()
#     for doc in all:
#         print(doc.doc_id)
#         for key in doc.keys():
#             print(f"{key}: {doc[key]}")
#             # doc["id"]=doc.doc_id
#             # _db.update(doc, doc_ids=[doc.doc_id])

if __name__ == "__main__":
    main()
