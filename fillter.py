import json
from phototag.db import Db


def read_results_blocks(filepath):
    """
    Reads blocks of 5 lines from the file, skipping every 6th line (the dashed separator).
    Yields each block as a list of 5 lines.
    """
    with open(filepath, "r") as f:
        block = []
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
        dic = {
            "id": file,
            "filename": file,
            "keywords": keywords,
            "title": title,
            "description": desc,
        }
        json_str = json.dumps(dic, ensure_ascii=False)
        db.insert(dic)
        print(json_str)
