from pathlib import Path
from typing import List

from phototagging.metadata_manager import MetadataManager


class Scanner:
    recursive: bool = False
    extenssions: List[str] = ["jpg", "jpeg", "png"]

    def __init__(self, manager: MetadataManager, folder: str | Path):
        if isinstance(folder, str):
            folder = Path(folder)
        if not folder.is_dir():
            raise ValueError(f"File {folder} is not a directory")
        self.folder = folder.resolve()
        self.manager = manager

    def _candidates(self) -> List[Path]:
        image_files: List[Path] = []
        if self.recursive:
            glob = self.folder.rglob
        else:
            glob = self.folder.glob
        for ext in self.extenssions:
            image_files = image_files + list(glob(f"*.{ext}"))
        return image_files

    def _existing(self) -> List[Path]:
        existing = [met.full_path for met in self.manager.all()]
        return existing

    def _filenames(self) -> List[str]:
        return [m.filename for m in self.manager.all()]

    def scan(self, remove_conflicting: bool = True) -> List[Path]:
        candidates = self._candidates()
        existing = self._existing()
        new_images = [img for img in candidates if img not in existing]
        existing_filenames = self._filenames()
        if remove_conflicting:
            conflicting = [str(img) for img in new_images if img.name in existing_filenames]
            if len(conflicting) > 0:
                print("New but conflicting files will not be included:" + ", ".join(conflicting))
                new_images = [img for img in new_images if img.name not in existing_filenames]
        return new_images
