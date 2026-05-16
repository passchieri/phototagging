import os
import re
from io import BytesIO
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Set

from flask import Flask, render_template_string, request, send_file
from dotenv import load_dotenv

from phototag.db import Db
from ..filters import create_age_filter,create_db_filter, create_max_files_filter, create_regexp_filter
from ..metadata_manager import MetadataManager
from ..phototag import PhotoTag

load_dotenv(dotenv_path=Path.home() / ".phototag.env")

DEFAULT_URL = os.getenv("PHOTOTAG_URL", "https://server.phototag.ai/api/keywords")
DEFAULT_TOKEN = os.getenv("PHOTOTAG_TOKEN", "")
DEFAULT_DB_FILE = os.getenv("PHOTOTAG_DB", str(Path.home() / ".phototag_db.json"))
DEFAULT_EXTENSIONS = ".jpg,.jpeg,.png,.gif,.bmp,.webp,.tiff"
DEFAULT_SOURCE_FOLDER = str(Path.home() / "Pictures" / "Lightroom Saved Photos")

TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>PhotoTag Web UI</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
      .page { max-width: 1100px; margin: 0 auto; padding: 24px; }
      .panel { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 20px; }
      label { display: block; margin-top: 12px; font-weight: 600; }
      input[type=text], input[type=number], textarea, select { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; box-sizing: border-box; }
      .small { max-width: 260px; display: inline-block; }
      .row { display: flex; gap: 16px; flex-wrap: wrap; }
      .row > div { flex: 1; min-width: 240px; }
      .button { margin-top: 16px; padding: 10px 18px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; }
      .button:disabled { background: #94a3b8; }
      .image-panel { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
      .metadata-box { white-space: pre-wrap; background: #111827; color: #f8fafc; padding: 18px; border-radius: 8px; overflow-wrap: break-word; }
      .image-preview { max-width: 100%; border-radius: 8px; border: 1px solid #cbd5e1; }
      .error { color: #b91c1c; font-weight: 700; margin-top: 12px; }
      .summary { margin-top: 8px; font-size: 0.95rem; color: #475569; }
    </style>
  </head>
  <body>
    <div class="page">
      <div class="panel">
        <h1>PhotoTag Web UI</h1>
        <p>Configure the same parameters used in <code>image_viewer.ipynb</code> and preview a single image with metadata.</p>
        <form method="post">
          <div class="row">
            <div>
              <label for="source_folder">Source Folder</label>
              <input id="source_folder" name="source_folder" type="text" value="{{ source_folder }}" placeholder="/path/to/images" />
            </div>
            <div>
              <label for="db_file">Database File</label>
              <input id="db_file" name="db_file" type="text" value="{{ db_file }}" />
            </div>
          </div>
          <div class="row">
            <div>
              <label for="url">API URL</label>
              <input id="url" name="url" type="text" value="{{ url }}" />
            </div>
            <div>
              <label for="token">API Token</label>
              <input id="token" name="token" type="text" value="{{ token }}" autocomplete="off" />
            </div>
          </div>
          <div class="row">
            <div class="small">
              <label for="max_file_age_days">Max File Age (days)</label>
              <input id="max_file_age_days" name="max_file_age_days" type="number" min="0" value="{{ max_file_age_days }}" />
            </div>
            <div class="small">
              <label for="max_files">Max Files</label>
              <input id="max_files" name="max_files" type="number" min="-1" value="{{ max_files }}" />
            </div>
            <div class="small">
              <label for="only_existing_in_db">Only Existing in DB</label>
              <input id="only_existing_in_db" name="only_existing_in_db" type="checkbox" {{ "checked" if only_existing_in_db else "" }} />
            </div>
          </div>
          <div>
            <label for="regexp">Filename Regexp</label>
            <input id="regexp" name="regexp" type="text" value="{{ regexp }}" placeholder="expo*" />
          </div>
          <div>
            <label for="extensions">Extensions (comma-separated)</label>
            <input id="extensions" name="extensions" type="text" value="{{ extensions }}" />
          </div>
          <div>
            <label for="selected_image">Selected Image</label>
            <select id="selected_image" name="selected_image">
              {% for image in image_files %}
              <option value="{{ image }}" {% if image == selected_image %}selected{% endif %}>{{ image }}</option>
              {% endfor %}
            </select>
          </div>
          <button class="button" type="submit">Refresh Results</button>
          <p class="summary">{{ summary }}</p>
        </form>
      </div>

      {% if error %}
      <div class="panel error">{{ error }}</div>
      {% endif %}

      {% if selected_image %}
      <div class="panel image-panel">
        <div>
          <h2>Image Preview</h2>
          <img class="image-preview" src="/image?path={{ selected_image | urlencode }}" alt="Selected image" />
        </div>
        <div>
          <h2>Metadata</h2>
          <div class="metadata-box">{{ metadata_text }}</div>
        </div>
      </div>
      {% endif %}

      {% if image_files and image_files|length > 1 %}
      <div class="panel">
        <h2>Matched Images</h2>
        <pre>{{ image_files|join("\n") }}</pre>
      </div>
      {% endif %}
    </div>
  </body>
</html>
"""


def create_app() -> Flask:
    app = Flask(__name__)
    return app


def parse_extensions(raw_extensions: str) -> Set[str]:
    return {
        ext.lower().strip() if ext.startswith(".") else f".{ext.lower().strip()}"
        for ext in raw_extensions.split(",")
        if ext.strip()
    }


def load_images(source_folder: Path, extensions: Set[str]) -> list[Path]:
    image_files: list[Path] = []
    for ext in extensions:
        image_files.extend(source_folder.glob(f"*{ext}"))
        image_files.extend(source_folder.glob(f"*{ext.upper()}"))
    return sorted(set(image_files))


def build_metadata_manager(url: str, token: str, db_file: str) -> MetadataManager:
    db = Db(db_file)
    phototag = PhotoTag(url=url, token=token)
    return MetadataManager(db, phototag)


def format_metadata(metadata) -> str:
    if not metadata:
        return "No metadata available."
    title = metadata.title or "N/A"
    description = metadata.description or "N/A"
    keywords = ", ".join(metadata.keywords or []) or "No tags"
    return (
        f"Filename: {metadata.filename}\n"
        f"Title: {title}\n"
        f"Description: {description}\n"
        f"Tags: {keywords}\n"
        f"Source: {metadata.source if hasattr(metadata, 'source') else 'database/API'}"
    )


def safe_filepath(path_string: str) -> Optional[Path]:
    if not path_string:
        return None
    candidate = Path(path_string).expanduser().resolve()
    if candidate.exists() and candidate.is_file():
        return candidate
    return None


app = create_app()


@app.route("/", methods=["GET", "POST"])
def index():
    form = {
        "source_folder": request.form.get("source_folder", DEFAULT_SOURCE_FOLDER),
        "db_file": request.form.get("db_file", DEFAULT_DB_FILE),
        "url": request.form.get("url", DEFAULT_URL),
        "token": request.form.get("token", DEFAULT_TOKEN),
        "max_file_age_days": request.form.get("max_file_age_days", "10"),
        "max_files": request.form.get("max_files", "-1"),
        "regexp": request.form.get("regexp", "expo*"),
        "extensions": request.form.get("extensions", DEFAULT_EXTENSIONS),
        "only_existing_in_db": request.form.get("only_existing_in_db") is not None,
        "selected_image": request.form.get("selected_image", ""),
    }
    image_files = []
    metadata_text = ""
    selected_image = form["selected_image"]
    error = ""
    summary = "Fill in the form and click Refresh Results to load images."

    try:
        source_folder = Path(form["source_folder"]).expanduser() if form["source_folder"] else DEFAULT_SOURCE_FOLDER
        extensions = parse_extensions(form["extensions"])
        if not extensions:
            extensions = parse_extensions(DEFAULT_EXTENSIONS)

        if not source_folder.exists() or not source_folder.is_dir():
            raise ValueError("Source folder must exist and be a directory.")

        image_files = [str(path) for path in load_images(source_folder, extensions)]
        filters = [
            create_age_filter(int(form["max_file_age_days"])),
            create_max_files_filter(int(form["max_files"])),
            create_regexp_filter(form["regexp"]),
            create_db_filter(metadata_manager, form["only_existing_in_db"])
        ]
        metadata_manager = build_metadata_manager(form["url"], form["token"], form["db_file"])
        image_paths = [Path(path) for path in image_files]
        for filter_fn in filters:
            image_paths = filter_fn(image_paths)
        image_files = [str(path) for path in image_paths]
        summary = f"Found {len(image_files)} matching image(s)."

        if image_files:
            if not selected_image or selected_image not in image_files:
                selected_image = image_files[0]
            form["selected_image"] = selected_image
            metadata = metadata_manager.get_by_filename(selected_image)
            if metadata is None:
                try:
                    metadata = metadata_manager.get_or_fetch(selected_image)
                except Exception:
                    metadata = None
            metadata_text = format_metadata(metadata)
        else:
            metadata_text = "No matching files found."
    except Exception as exc:
        error = str(exc)
        metadata_text = ""
        image_files = []

    return render_template_string(
        TEMPLATE,
        **form,
        # image_files=image_files,
        # metadata_text=metadata_text,
        # selected_image=selected_image,
        # error=error,
        # summary=summary,
    )


@app.route("/image")
def image():
    path_string = request.args.get("path", "")
    if not path_string:
        return "Image path is required.", 400
    file_path = Path(path_string).expanduser().resolve()
    if not file_path.exists() or not file_path.is_file():
        return "Image not found.", 404

    mime_type = "image/jpeg"
    if file_path.suffix.lower() == ".png":
        mime_type = "image/png"
    elif file_path.suffix.lower() == ".gif":
        mime_type = "image/gif"
    elif file_path.suffix.lower() in {".bmp", ".webp", ".tiff"}:
        mime_type = "image/" + file_path.suffix.lower().lstrip('.')

    return send_file(str(file_path), mimetype=mime_type)
