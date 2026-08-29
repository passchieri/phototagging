from pathlib import Path
from typing import cast

from fastapi.testclient import TestClient
from httpx2 import Response

from folder_manager.folder_manager import FolderManager
from server.api import app, get_folder_manager


def test_files_endpoint_lists_root_and_subpath(tmp_path: Path):
    root = tmp_path / "root"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (root / "photo.jpg").write_text("x")
    (nested / "child.jpg").write_text("x")

    folder_manager = FolderManager(str(root))
    app.dependency_overrides[get_folder_manager] = lambda: folder_manager

    try:
        with TestClient(app) as client:  # type: ignore
            root_response = cast(Response, client.get("/files"))  # type: ignore
            subpath_response = cast(Response, client.get("/files/nested"))  # type: ignore
    finally:
        app.dependency_overrides.clear()

    assert root_response.status_code == 200
    assert root_response.json() == [
        {"name": "nested", "path": "nested", "is_dir": True},
        {"name": "photo.jpg", "path": "photo.jpg", "is_dir": False},
    ]

    assert subpath_response.status_code == 200
    assert subpath_response.json() == [
        {"name": "child.jpg", "path": "nested/child.jpg", "is_dir": False},
    ]
