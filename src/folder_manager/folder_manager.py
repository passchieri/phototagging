from operator import is_none
from pathlib import Path
from typing import List


class FolderManager:
    def __init__(self, root: str, extentions: List[str] | None = None):
        self.root = Path(root)
        self.exts: List[str] = extentions or ["jpg", "jpeg", "png"]

        if not self.root.exists():
            raise ValueError(f"Root folder {root} does not exist")

    def children(self, path: str | Path | None = None) -> List[Path]:
        dir = self.root
        if not is_none(path):
            dir = self.root / path

        if not dir.exists():
            raise ValueError(f"Folder {path} does not exist in root {self.root}")

        files: List[Path] = []
        for ext in self.exts:
            files = files + list(dir.glob(f"*.{ext}"))

        folders: List[Path] = [p for p in dir.iterdir() if p.is_dir()]
        return folders + files
