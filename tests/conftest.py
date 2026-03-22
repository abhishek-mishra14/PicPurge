import os
import sys
import pytest
from PIL import Image, ImageFilter

# Allow imports from src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def image_factory(tmp_path):
    def _create_image(filename, mode='sharp', format='JPEG', size=(100, 100)):
        path = tmp_path / filename
        w, h = size
        img = Image.new('RGB', size, color=(255, 0, 0))
        if mode == 'sharp':
            for i in range(int(w * 0.2), int(w * 0.8)):
                for j in range(int(h * 0.2), int(h * 0.8)):
                    img.putpixel((i, j), (255, 255, 255))
            for i in range(int(w * 0.4), int(w * 0.6)):
                for j in range(int(h * 0.4), int(h * 0.6)):
                    img.putpixel((i, j), (0, 0, 0))
        elif mode == 'blurry':
            for i in range(w):
                for j in range(h):
                    c = int(255 * (i / w))
                    img.putpixel((i, j), (c, c, c))
            img = img.filter(ImageFilter.GaussianBlur(15))
        elif mode == 'screenshot':
            # Simulate a phone screenshot: solid status bar at top, content, nav bar at bottom
            bar_h = int(h * 0.15)
            for i in range(w):
                for j in range(bar_h):
                    img.putpixel((i, j), (30, 30, 30))
                for j in range(h - bar_h, h):
                    img.putpixel((i, j), (40, 40, 40))
        save_format = format
        if format == 'PNG':
            path = path.with_suffix('.png')
        img.save(path, format=save_format)
        return str(path)
    return _create_image

@pytest.fixture
def mock_video_file(tmp_path):
    vid_path = tmp_path / "dummy_video.mp4"
    vid_path.write_text("dummy content")
    return str(vid_path)

@pytest.fixture
def real_video_file(tmp_path):
    """Creates a tiny real video file using FFmpeg for non-mocked testing."""
    import subprocess
    vid_path = str(tmp_path / "real_test.mp4")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "color=c=red:s=64x64:d=2", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", vid_path
        ], capture_output=True, check=True)
    except Exception:
        pytest.skip("ffmpeg not available for real video test")
    return vid_path
