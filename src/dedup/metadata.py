import os
from PIL import Image

def get_metadata(path: str) -> dict:
    """Extracts resolution, file size, and creation date from a media file."""
    stat = os.stat(path)
    file_size = stat.st_size
    created = stat.st_mtime

    with Image.open(path) as img:
        width, height = img.size

    return {
        "width": width,
        "height": height,
        "file_size": file_size,
        "created": created,
    }

def rank_duplicates(group: list[str]) -> list[str]:
    """Ranks a group of duplicate file paths best-first: highest resolution > largest file > newest."""
    metas = [(p, get_metadata(p)) for p in group]
    metas.sort(key=lambda x: (
        x[1]["width"] * x[1]["height"],   # resolution (ascending, reversed below)
        x[1]["file_size"],                 # file size
        x[1]["created"],                   # newest
    ), reverse=True)
    return [p for p, _ in metas]
