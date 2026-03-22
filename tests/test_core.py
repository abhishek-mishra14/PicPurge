import os
import pytest

from src.dedup import core


def test_group_by_hash_near_duplicates():
    hashes = {
        "file1.jpg": "ffff0000ffff0000",
        "file2.jpg": "ffff0000ffff0000",
        "file3.jpg": "ffff0000ffff0008",  # distance 1
        "file4.jpg": "0000ffff0000ffff",  # completely different
    }
    groups = core.group_identical_or_near(hashes, threshold=5)
    assert len(groups) == 1
    assert "file4.jpg" not in groups[0]
    assert set(groups[0]) == {"file1.jpg", "file2.jpg", "file3.jpg"}


def test_group_all_unique():
    hashes = {
        "a.jpg": "0000000000000000",
        "b.jpg": "ffffffffffffffff",
    }
    groups = core.group_identical_or_near(hashes, threshold=5)
    assert len(groups) == 0


def test_group_all_duplicates():
    hashes = {f"img{i}.jpg": "abcdef0123456789" for i in range(5)}
    groups = core.group_identical_or_near(hashes, threshold=0)
    assert len(groups) == 1
    assert len(groups[0]) == 5


def test_group_empty():
    assert core.group_identical_or_near({}, threshold=5) == []


def test_move_to_skipped(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    f1 = root / "f1.jpg"
    f2 = root / "f2.jpg"
    f1.write_text("data")
    f2.write_text("data")

    core.move_to_skipped([str(f1), str(f2)], str(root))
    skipped_dir = root / "skipped"
    assert skipped_dir.exists()
    assert (skipped_dir / "f1.jpg").exists()
    assert (skipped_dir / "f2.jpg").exists()
    assert not f1.exists()
    assert not f2.exists()


def test_move_to_skipped_naming_collision(tmp_path):
    """If a file with the same name already exists in skipped/, it should be renamed."""
    root = tmp_path / "root"
    root.mkdir()
    skipped = root / "skipped"
    skipped.mkdir()

    # Pre-existing file in skipped
    (skipped / "photo.jpg").write_text("old")

    # New file to move
    src = root / "photo.jpg"
    src.write_text("new")

    core.move_to_skipped([str(src)], str(root))

    assert (skipped / "photo.jpg").exists()  # old one
    assert (skipped / "photo_1.jpg").exists()  # renamed new one
    assert not src.exists()


def test_move_to_skipped_empty_list(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    core.move_to_skipped([], str(root))
    assert not (root / "skipped").exists()


def test_move_nonexistent_file(tmp_path):
    """Should silently skip files that don't exist."""
    root = tmp_path / "root"
    root.mkdir()
    core.move_to_skipped(["/nonexistent/file.jpg"], str(root))
