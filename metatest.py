from pathlib import Path

from pyexiv2 import ImageMetadata
from phototag.update_image import KEYWORD_KEYS, add_keywords_to_metadata, read_exif, remove_all_keywords_from_exif, write_exif

def print_tags(metadata:ImageMetadata):
    for key in KEYWORD_KEYS:
        try:
            print(f"{key} = {metadata[key].value}")
        except KeyError:
            print(f"{key} not found in metadata.")

    # for key in metadata.iptc_keys:
    #     try:
    #         print(f"{key} = {metadata[key].value}")
    #     except KeyError:
    #         print(f"{key} not found in metadata.")


file_path =Path("resources") / "passchier-100.jpg"
print(str(file_path ))
metadata=read_exif(str(file_path))
print("======= Before =======")
print_tags(metadata)
metadata=remove_all_keywords_from_exif(metadata)
print("======= After remove =======")
print_tags(metadata)

add_keywords_to_metadata(metadata, ["test", "phototagging", "example"],True)
print("======= After add =======")
print_tags(metadata)
write_exif(metadata)
