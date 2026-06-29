import os
from pathlib import Path
from typing import Any, List, Optional, cast
from os import path

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, Query
import fastapi
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from phototag.db import Db as PhototagDb
from phototag.metadata_manager import MetadataManager
from phototag.metadata import MetaData
from phototag.phototag import PhotoTag


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
    state["metadata_manager"] = metadata_manager

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


class KeywordsUpdateRequest(BaseModel):
    keywords: List[str]


class ImageMetadataRequest(BaseModel):
    include_keywords: Optional[list[str]] = None
    exclude_keywords: Optional[list[str]] = None


from functools import total_ordering


@total_ordering
class MetadataModel(BaseModel):
    # model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    filename: str
    full_path: str = ""
    keywords: list[str]
    title: Optional[str] = None
    description: Optional[str] = None

    # @field_serializer("keywords")
    # def serialize_sorted_list(cls, v: SortedSet[str] | set[str] | list[str]) -> List[str]:
    #     return list(v)

    @staticmethod
    def from_metadata(
        metadata: MetaData | List[MetaData],
    ) -> MetadataModel | List[MetadataModel]:
        if isinstance(metadata, MetaData):
            return MetadataModel(
                id=metadata.id,
                filename=metadata.filename,
                full_path=metadata.full_path,
                keywords=list(metadata.keywords),
                title=metadata.title if metadata.title else None,
                description=metadata.description if metadata.description else None,
            )
        return [
            MetadataModel(
                id=m.id,
                filename=m.filename,
                keywords=list(m.keywords),
                title=m.title if m.title else None,
                description=m.description if m.description else None,
            )
            for m in metadata
        ]

    def __lt__(self, other: Any):
        if not isinstance(other, MetadataModel):
            return NotImplemented
        return self.id < other.id

    def __eq__(self, other: Any):
        if not isinstance(other, MetadataModel):
            return NotImplemented
        return self.id == other.id


@app.get("/new_images", tags=["new_images"])
async def available_images(
    page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> dict[str, Any]:
    """Return a list of images that are available, but not yet have metadata"""

    if not ROOT_DIR.exists():
        raise HTTPException(status_code=404, detail="Root directory not found")

    metadata = metadata_manager.all()
    existing = [file.filename for file in metadata]

    # Collect all JPG files
    images = [
        file
        for file in ROOT_DIR.iterdir()
        if file.is_file() and file.name.endswith(".jpg") and file.name not in existing
    ]

    # Sort newest → oldest
    images.sort(key=lambda x: path.getmtime(x), reverse=True)

    # Pagination math
    start = (page - 1) * size
    end = start + size

    paginated = images[start:end]

    return {
        "page": page,
        "size": size,
        "total": len(images),
        "data": [img.name for img in paginated],
    }


@app.get("/images", tags=["images"])
async def list_images(
    page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    size: int = Query(1000, ge=1, le=1000, description="Items per page"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> dict[str, Any]:
    """
    Returns a paginated list of image filenames in the root directory,
    sorted by modification time (newest first).
    """

    metadata = metadata_manager.all()

    # Collect all JPG files

    # Sort newest → oldest
    metadata.sort(key=lambda x: x.id, reverse=True)

    # Pagination math
    start = (page - 1) * size
    end = start + size

    paginated = [m.to_dict() for m in metadata[start:end]]

    return {
        "page": page,
        "size": size,
        "total": len(metadata),
        "data": paginated,
    }


@app.get("/image/{name}", tags=["images"])
async def get_image(
    name: str = fastapi.Path(..., description="Filename of the image to get"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> FileResponse:

    md = metadata_manager.get_by_filename(name)
    if not md:
        raise HTTPException(
            status_code=404, detail=f"Image '{name}' not found in database"
        )
    if md.full_path:
        file_path = Path(md.full_path)
    else:
        file_path = ROOT_DIR / name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Image '{file_path}' not found")
    return FileResponse(path=file_path)


@app.get("/metadata", tags=["metadata"])
async def get_all_metadata(
    page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> dict[str, Any]:
    metadata = metadata_manager.all()
    if not metadata:
        raise HTTPException(status_code=404, detail=f"No metadata available")
    data = cast(List[MetadataModel], MetadataModel.from_metadata(metadata))
    data = sorted(data, reverse=True)
    # Pagination math
    start = (page - 1) * size
    end = start + size

    paginated = data[start:end]

    return {
        "page": page,
        "size": size,
        "total": len(metadata),
        "data": paginated,
    }


@app.get("/metadata/{id}", tags=["metadata"])
async def get_image_metadata(
    id: int = fastapi.Path(..., description="id of a metadata entry"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> dict[str, Any]:
    metadata = metadata_manager.get_by_id(id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Metadata for id '{id}' not found")
    return {"data": MetadataModel.from_metadata(metadata)}


@app.post("/metadata/{name}", tags=["metadata"])
async def post_image_metadata(
    name: str = fastapi.Path(
        ..., description="Filename of the image to create metadata for"
    ),
    include_keywords: Optional[list[str]] = Query(
        None, description="List of keywords to include in the metadata"
    ),
    exclude_keywords: Optional[list[str]] = Query(
        None, description="List of keywords to exclude from the metadata"
    ),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> dict[str, Any]:
    if metadata_manager.get_by_filename(str(name)):
        raise HTTPException(
            status_code=409, detail=f"Metadata for image '{name}' already exists"
        )

    metadata = metadata_manager.create(
        str(ROOT_DIR / name),
        required_keywords=include_keywords,
        keywords_to_remove=exclude_keywords,
    )
    return {"data": MetadataModel.from_metadata(metadata) if metadata else []}


@app.patch("/metadata/{id}", tags=["metadata"])
async def patch_image_metadata(
    id: int = fastapi.Path(..., description="ID of the metadata to update"),
    keywords: KeywordsUpdateRequest = Body(
        ..., description="List of keywords to replace in the metadata"
    ),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> dict[str, Any]:
    metadata = metadata_manager.get_by_id(id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Metadata for id '{id}' not found")

    updated_metadata = metadata_manager.update_keywords(
        metadata, keywords=keywords.keywords
    )
    return {
        "data": (
            MetadataModel.from_metadata(updated_metadata) if updated_metadata else []
        )
    }


@app.delete("/metadata/{id}", tags=["metadata"])
async def delete_image_metadata(
    id: int = fastapi.Path(..., description="ID of the metadata to delete"),
    metadata_manager: MetadataManager = Depends(get_metadata_manager),
) -> dict[str, Any]:
    if not metadata_manager.get_by_id(id):
        raise HTTPException(status_code=404, detail=f"Metadata for id '{id}' not found")

    metadata_manager.delete_by_id(id)
    return {"data": []}
