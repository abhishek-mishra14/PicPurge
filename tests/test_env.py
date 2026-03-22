import shutil
import pytest

def test_system_dependencies():
    """Verify that FFmpeg and FFprobe are available on the user's PATH."""
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    
    assert ffmpeg_path is not None, "ffmpeg is not installed (Required for video hashing)"
    assert ffprobe_path is not None, "ffprobe is not installed (Required for video metadata)"
