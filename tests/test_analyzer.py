import os
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from picpurge import analyzer


# --- Blur Detection ---

def test_blur_score_sharp(image_factory):
    sharp = image_factory("sharp.jpg", mode="sharp")
    assert analyzer.get_blur_score(sharp) > 100.0

def test_blur_score_blurry(image_factory):
    blurry = image_factory("blurry.jpg", mode="blurry")
    assert analyzer.get_blur_score(blurry) < 100.0

def test_blur_score_heic_fallback(image_factory):
    """HEIC images can't be read by cv2.imread — the fallback via PIL must work."""
    # Create a normal JPEG, then rename to .heic to simulate cv2 failure
    img_path = image_factory("test_heic.jpg", mode="sharp")
    heic_path = img_path.replace(".jpg", ".heic")
    os.rename(img_path, heic_path)

    # cv2.imread will return None for .heic, so get_blur_score must use the PIL fallback
    score = analyzer.get_blur_score(heic_path)
    # It must NOT return 0.0 (the old broken behavior)
    assert score > 0.0

def test_blur_score_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        analyzer.get_blur_score("/nonexistent/file.jpg")


# --- Image Hashing ---

def test_image_hash_identical(image_factory):
    img1 = image_factory("img1.jpg", mode="sharp")
    img2 = image_factory("img2.jpg", mode="sharp")
    assert analyzer.get_image_hash(img1) == analyzer.get_image_hash(img2)

def test_image_hash_different(image_factory):
    sharp = image_factory("sharp.jpg", mode="sharp")
    blurry = image_factory("blurry.jpg", mode="blurry")
    assert analyzer.get_image_hash(sharp) != analyzer.get_image_hash(blurry)

def test_image_hash_nonexistent():
    with pytest.raises(FileNotFoundError):
        analyzer.get_image_hash("/nonexistent/file.jpg")


# --- Video Hashing (Mocked) ---

@patch("subprocess.check_output")
@patch("subprocess.run")
@patch("PIL.Image.open")
def test_video_hashes_mocked(mock_img_open, mock_run, mock_check_output, mock_video_file):
    mock_check_output.return_value = b"10.0\n"
    mock_run.return_value = MagicMock(returncode=0)

    mock_img = MagicMock()
    mock_img.__enter__.return_value = mock_img
    mock_img_open.return_value = mock_img

    with patch("imagehash.phash") as mock_phash:
        mock_phash.return_value = "abc123hash"
        hashes = analyzer.get_video_hashes(mock_video_file)
        assert len(hashes) == 3
        assert mock_run.call_count == 3


# --- Video Hashing (Real FFmpeg) ---

def test_video_hashes_real(real_video_file):
    """Runs get_video_hashes against a real tiny video file without mocking."""
    hashes = analyzer.get_video_hashes(real_video_file)
    assert len(hashes) == 3
    # All frames are the same solid red color, so hashes should be identical
    assert hashes[0] == hashes[1] == hashes[2]


# --- Screenshot Detection ---

def test_is_screenshot_positive(image_factory):
    """A 9:16 image with solid bars at top/bottom should be flagged."""
    screenshot = image_factory("screenshot.png", mode="screenshot", format="PNG", size=(90, 160))
    assert analyzer.is_screenshot(screenshot) is True

def test_is_screenshot_negative(image_factory):
    """A normal photo should NOT be flagged as a screenshot."""
    photo = image_factory("photo.jpg", mode="sharp")
    assert analyzer.is_screenshot(photo) is False


# --- Format Classification ---

def test_classify_image_formats():
    assert analyzer.classify_file("photo.jpg") == "image"
    assert analyzer.classify_file("photo.jpeg") == "image"
    assert analyzer.classify_file("photo.png") == "image"
    assert analyzer.classify_file("photo.heic") == "image"
    assert analyzer.classify_file("photo.heif") == "image"
    assert analyzer.classify_file("photo.webp") == "image"
    assert analyzer.classify_file("photo.dng") == "image"
    assert analyzer.classify_file("photo.tiff") == "image"

def test_classify_video_formats():
    assert analyzer.classify_file("clip.mp4") == "video"
    assert analyzer.classify_file("clip.mov") == "video"
    assert analyzer.classify_file("clip.mkv") == "video"
    assert analyzer.classify_file("clip.avi") == "video"
    assert analyzer.classify_file("clip.3gp") == "video"
    assert analyzer.classify_file("clip.webm") == "video"

def test_classify_unknown():
    assert analyzer.classify_file("notes.txt") == "unknown"
    assert analyzer.classify_file("doc.pdf") == "unknown"
