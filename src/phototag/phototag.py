from typing import Optional
import requests
from pathlib import Path

URL = "https://server.phototag.ai/api/keywords"
TOKEN = "c9245585-facb-4737-b91f-b7a32ca098ad"


PAYLOAD = {
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


class PhotoTag:
    def __init__(
        self, url: str = URL, token: str = TOKEN, options: Optional[dict] = None
    ):
        self.url = url
        self.headers = {"Authorization": f"Bearer {token}"}
        self.payload = PAYLOAD.copy()
        if options:
            self.payload.update(options)

    def fetch_for_file(self, filename: str) -> dict:
        path = Path(filename)
        if not path.is_file():
            raise FileNotFoundError(f"File {filename} does not exist.")
        with open(path, "rb") as file:
            response = requests.post(
                self.url, headers=self.headers, data=self.payload, files={"file": file}
            )
            if not response.ok:
                response.raise_for_status()

            data = response.json()["data"]
            data["filename"] = path.name
            data["id"] = path.name
            return data
