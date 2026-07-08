import json
from typing import Generator

from phototagging.db import Db, DbMetadata


def read_results_blocks(filepath: str) -> Generator[list[str], None, None]:
    """
    Reads blocks of 5 lines from the file, skipping every 6th line (the dashed separator).
    Yields each block as a list of 5 lines.
    """
    with open(filepath, "r") as f:
        block: list[str] = []
        for i, line in enumerate(f):
            if (i + 1) % 6 == 0:
                # Skip the dashed separator line
                continue
            block.append(line.rstrip("\n"))
            if len(block) == 5:
                yield block
                block = []


with Db("results.json") as db:
    for [file, kw, insta, title, desc] in read_results_blocks("results.txt"):
        keywords = kw.split(", ")
        dic: DbMetadata = DbMetadata(
            filename=file,
            keywords=keywords,
            title=title,
            description=desc,
        )
        json_str = json.dumps(dic, ensure_ascii=False)
        db.insert(dic)
        print(json_str)
