import os
import zipfile
import pytest
import shutil
from typer.testing import CliRunner
from unittest.mock import patch
from main import app

runner = CliRunner()


def test_process_e2e(tmp_path, image_factory):
    """Full process flow: blur + dedup + move to skipped."""
    test_dir = tmp_path / "trip"
    test_dir.mkdir()

    shutil.copy(image_factory("a.jpg", mode="sharp"), test_dir / "a.jpg")
    shutil.copy(image_factory("b.jpg", mode="sharp"), test_dir / "b.jpg")  # dup of a
    shutil.copy(image_factory("blur.jpg", mode="blurry"), test_dir / "blur.jpg")

    with patch("src.dedup.ui.prompt_duplicate_resolution") as mock_ui, \
         patch("src.dedup.ui.prompt_skipped_files"):
        mock_ui.side_effect = lambda group: [group[0]]
        result = runner.invoke(app, ["process", str(test_dir)])

    assert result.exit_code == 0
    skipped = [f.name for f in (test_dir / "skipped").iterdir()]
    main = [f.name for f in test_dir.iterdir() if f.is_file()]
    assert len(skipped) == 2
    assert "blur.jpg" in skipped
    assert "blur.jpg" not in main


def test_process_empty_folder(tmp_path):
    """Processing an empty folder should not crash."""
    empty = tmp_path / "empty"
    empty.mkdir()
    result = runner.invoke(app, ["process", str(empty)])
    assert result.exit_code == 0


def test_process_single_file(tmp_path, image_factory):
    """A single file should just pass through with no skips."""
    d = tmp_path / "single"
    d.mkdir()
    shutil.copy(image_factory("only.jpg", mode="sharp"), d / "only.jpg")

    with patch("src.dedup.ui.prompt_skipped_files"):
        result = runner.invoke(app, ["process", str(d)])
    assert result.exit_code == 0
    assert (d / "only.jpg").exists()
    assert not (d / "skipped").exists()


def test_process_dry_run(tmp_path, image_factory):
    """Dry-run should NOT move any files."""
    d = tmp_path / "dryrun"
    d.mkdir()
    shutil.copy(image_factory("a.jpg", mode="sharp"), d / "a.jpg")
    shutil.copy(image_factory("b.jpg", mode="sharp"), d / "b.jpg")
    shutil.copy(image_factory("blur.jpg", mode="blurry"), d / "blur.jpg")

    result = runner.invoke(app, ["process", str(d), "--dry-run"])
    assert result.exit_code == 0
    # No files should have been moved
    assert not (d / "skipped").exists()
    assert len(list(d.iterdir())) == 3


def test_process_custom_thresholds(tmp_path, image_factory):
    """Custom thresholds should be respected."""
    d = tmp_path / "thresh"
    d.mkdir()
    shutil.copy(image_factory("a.jpg", mode="sharp"), d / "a.jpg")

    with patch("src.dedup.ui.prompt_skipped_files"):
        result = runner.invoke(app, ["process", str(d),
                                     "--blur-threshold", "9999",
                                     "--hash-threshold", "0"])
    assert result.exit_code == 0


def test_archive_creates_zip(tmp_path):
    d = tmp_path / "src_dir"
    d.mkdir()
    (d / "file.txt").write_text("hello")

    out = tmp_path / "out.zip"
    result = runner.invoke(app, ["archive", str(d), "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_archive_integrity(tmp_path):
    """After archiving the ZIP should pass integrity verification."""
    d = tmp_path / "integrity_test"
    d.mkdir()
    (d / "doc.txt").write_text("content")

    out = tmp_path / "verified.zip"
    result = runner.invoke(app, ["archive", str(d), "--output", str(out)])
    assert result.exit_code == 0

    # Manually verify the zip is valid
    with zipfile.ZipFile(str(out)) as zf:
        assert zf.testzip() is None
        assert len(zf.namelist()) > 0
