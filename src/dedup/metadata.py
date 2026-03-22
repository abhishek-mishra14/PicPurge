import os
from PIL import Image

def get_metadata(path: str) -> dict:
    """Extracts resolution, file size, and creation date from a media file."""
    result = {"width": 0, "height": 0, "file_size": 0, "created": 0.0}
    try:
        stat = os.stat(path)
        result["file_size"] = stat.st_size
        result["created"] = stat.st_mtime
    except OSError:
        return result

    try:
        with Image.open(path) as img:
            result["width"], result["height"] = img.size
    except Exception:
        pass
    return result

def rank_duplicates(group: list[str]) -> list[str]:
    """Ranks a group of duplicate file paths best-first: highest resolution > largest file > newest."""
    metas = [(p, get_metadata(p)) for p in group]
    metas.sort(key=lambda x: (
        x[1]["width"] * x[1]["height"],   # resolution (ascending, reversed below)
        x[1]["file_size"],                 # file size
        x[1]["created"],                   # newest
    ), reverse=True)
    return [p for p, _ in metas]
