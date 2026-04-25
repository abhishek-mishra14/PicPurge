import os
import pytest
from picpurge import metadata


def test_get_metadata_image(image_factory):
    img = image_factory("test.jpg", mode="sharp")
    meta = metadata.get_metadata(img)
    assert meta["width"] == 100
    assert meta["height"] == 100
    assert meta["file_size"] > 0
    assert "created" in meta


def test_get_metadata_nonexistent():
    with pytest.raises(FileNotFoundError):
        metadata.get_metadata("/nonexistent/file.jpg")


def test_rank_duplicates(image_factory, tmp_path):
    """Given a group of duplicates, rank_duplicates should return them sorted best-first."""
    # Create two images: one larger resolution, one smaller
    large = image_factory("large.jpg", mode="sharp", size=(200, 200))
    small = image_factory("small.jpg", mode="sharp", size=(50, 50))

    ranked = metadata.rank_duplicates([small, large])
    # The larger resolution image should be first
    assert ranked[0] == large
    assert ranked[1] == small
