import os
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, cast

import fastapi
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from phototagging.db import Db as PhototagDb
from phototagging.metadata import Metadata
from phototagging.metadata_manager import MetadataManager
from phototagging.phototag import PhotoTag
from phototagging.scanner import Scanner


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(dotenv_path=Path.home() / ".phototag.env")
    phototag_url = os.getenv("PHOTOTAG_URL", "https://server.phototag.ai/api/keywords")
    phototag_token = os.getenv("PHOTOTAG_TOKEN", "")
    phototag_db_file = os.getenv("PHOTOTAG_DB", str(Path.home() / ".phototag_db.json"))

    db = PhototagDb(phototag_db_file)
    phototag = PhotoTag(
        url=phototag_url,
        token=phototag_token,
    )
    metadata_manager = MetadataManager(db, phototag)
    scanner = Scanner(metadata_manager, ROOT_DIR)
    state["metadata_manager"] = metadata_manager
    state["scanner"] = scanner

    yield  # Server runs and handles requests here

    # Shutdown logic
    pass


app = FastAPI(lifespan=lifespan)

state: dict[str, Any] = {}

origins = ["http://localhost:5173", "localhost:5173"]
ROOT_DIR = Path("/Users/igor/Pictures/Lightroom Saved Photos")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_metadata_manager() -> MetadataManager:
    metadata_manager = cast(MetadataManager, state.get("metadata_manager"))
    if not metadata_manager:
        raise HTTPException(status_code=500, detail="Metadata manager not initialized")
    return metadata_manager


def get_scanner() -> Scanner:
    scanner = cast(Scanner, state.get("scanner"))
    if not scanner:
        raise HTTPException(status_code=500, detail="Scanner not initialized")
    return scanner


class KeywordsUpdateRequest(BaseModel):
    keywords: List[str]


class ImageMetadataRequest(BaseModel):
    include_keywords: Optional[list[str]] = None
    exclude_keywords: Optional[list[str]] = None


class ImagesResponse(BaseModel):
    data: List[str]


@app.get("/scan", tags=["images"], response_model=List[str], operation_id="scan")
async def available_images(
    scanner: Scanner = Depends(get_scanner),
) -> List[str]:
    """Return a list of images that are available, but not yet have metadata"""

    images = scanner.scan(True)

    return [img.name for img in images]


@app.get("/images", tags=["images"], response_model=List[str], operation_id="get_images")
async def list_images(
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> List[str]:
    """
    Returns a paginated list of image filenames in the root directory,
    sorted by modification time (newest first).
    """

    metadata = metadata_manager.all()

    return [m.filename for m in metadata]


@app.get("/image/{name}", tags=["images"], response_class=FileResponse, operation_id="get_image")
async def get_image(
    name: str = fastapi.Path(..., description="Filename of the image to get"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
    scanner: Scanner = Depends(get_scanner),
) -> FileResponse:

    md = metadata_manager.get_by_filename(name)
    if md:
        file_path = md.full_path
    else:
        file_path = ROOT_DIR / name
        new_images = scanner.scan()
        if name not in [i.name for i in new_images]:
            raise HTTPException(status_code=404, detail=f"Image '{name}' not found in database or scan dir")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Image '{file_path}' not found")
    return FileResponse(path=file_path)


@app.get("/metadata", tags=["metadata"], response_model=List[Metadata], operation_id="get_metadatas")
async def get_all_metadata(
    # page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    # size: int = Query(10, ge=1, le=100, description="Items per page"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> List[Metadata]:
    metadata = metadata_manager.all()
    if not metadata:
        raise HTTPException(status_code=404, detail="No metadata available")
    data = sorted(metadata, reverse=True)
    # # Pagination math
    # start = (page - 1) * size
    # end = start + size

    return [d.to_metadata_filled() for d in data]


@app.get("/metadata/{id}", tags=["metadata"], operation_id="get_metadata")
async def get_image_metadata(
    id: str = fastapi.Path(..., description="id of a metadata entry"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> Metadata:
    metadata = metadata_manager.get_by_id(id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Metadata for id '{id}' not found")
    return metadata.to_metadata_filled()


@app.post("/metadata/{name}", tags=["metadata"], operation_id="get_metadata_by_name")
async def post_image_metadata(
    name: str = fastapi.Path(..., description="Filename of the image to create metadata for"),
    include_keywords: Optional[list[str]] = Query(None, description="List of keywords to include in the metadata"),
    exclude_keywords: Optional[list[str]] = Query(None, description="List of keywords to exclude from the metadata"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> Metadata:
    if metadata_manager.get_by_filename(str(name)):
        raise HTTPException(status_code=409, detail=f"Metadata for image '{name}' already exists")

    metadata = metadata_manager.create(
        str(ROOT_DIR / name),
        required_keywords=include_keywords,
        keywords_to_remove=exclude_keywords,
    )
    return metadata.to_metadata_filled()


@app.patch("/metadata/{id}", tags=["metadata"], operation_id="patch_metadata")
async def patch_image_metadata(
    id: str = fastapi.Path(..., description="ID of the metadata to update"),
    keywords: KeywordsUpdateRequest = Body(..., description="List of keywords to replace in the metadata"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> Metadata:
    metadata = metadata_manager.get_by_id(id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Metadata for id '{id}' not found")

    updated_metadata = metadata_manager.update_keywords(metadata, keywords=keywords.keywords)
    return updated_metadata.to_metadata_filled()


class Result(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


@app.delete("/metadata/{id}", tags=["metadata"], response_model=Result, operation_id="delete_metadata")
async def delete_image_metadata(
    id: str = fastapi.Path(..., description="ID of the metadata to delete"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> dict[str, Any]:
    if not metadata_manager.get_by_id(id):
        raise HTTPException(status_code=404, detail=f"Metadata for id '{id}' not found")

    metadata_manager.delete_by_id(id)
    return {"result": "success"}
