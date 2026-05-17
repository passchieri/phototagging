from typing import Any, Mapping, Optional, TypedDict, cast
import requests
from pathlib import Path

URL = "https://server.phototag.ai/api/keywords"    
TOKEN = "c9245585-facb-4737-b91f-b7a32ca098ad"


PAYLOAD:dict[str,Any] = {
    "addMetadata": False,
    "keywordsOnly": False,
    "saveFile": False,
    "language": "en",
    "maxKeywords": 20,
    "maxTitleCharacters": 100,
    "maxDescriptionCharacters": 500,
    "minTitleCharacters": 10,
    "minDescriptionCharacters": 50,
    "singleWordKeywordsOnly": False,
    # "requiredKeywords": ",sky",
    # "customContext": "big city",
}

class PhotoTagResponse(TypedDict):
    filename: str
    id: str
    keywords: list[str]
    title: Optional[str]
    description: Optional[str]


class PhotoTag:
    def __init__(self, url: str = URL, token: str = TOKEN, options: Optional[dict[str,Any]] = None):
        self.url = url
        self.headers = {"Authorization": f"Bearer {token}"}
        self.payload = PAYLOAD.copy()
        if options:
            self.payload.update(options)

    def fetch_for_file(self, filename: str) -> PhotoTagResponse:
        path = Path(filename)
        if not path.is_file():
            raise FileNotFoundError(f"File {filename} does not exist.")
        with open(path, "rb") as file:
            response = requests.post(self.url, headers=self.headers, data=self.payload, files={"file": file})
            if not response.ok:
                response.raise_for_status()

            raw_data = response.json()["data"]
            if not isinstance(raw_data, dict):
                raise TypeError("Expected response data to be a mapping.")

            data=cast(Mapping[str, Any], raw_data)
            normalized_data: dict[str, Any] = {str(key): value for key, value in data.items()}
            normalized_data["filename"] = path.name
            normalized_data["id"] = path.name
            if not "keywords" in normalized_data :
                normalized_data["keywords"] = []
            return cast(PhotoTagResponse, normalized_data)
