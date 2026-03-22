import cv2
import numpy as np
import subprocess
import tempfile
from PIL import Image
import imagehash
from pillow_heif import register_heif_opener

register_heif_opener()

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.dng', '.tiff', '.tif'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.mkv', '.avi', '.3gp', '.webm'}

def classify_file(path: str) -> str:
    """Returns 'image', 'video', or 'unknown' based on file extension."""
    import os
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "unknown"

def get_blur_score(image_path: str) -> float:
    """Calculates blur score via Laplacian variance. Falls back to PIL for HEIC."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is not None:
        return cv2.Laplacian(image, cv2.CV_64F).var()
    # Fallback: use PIL (supports HEIC via pillow-heif) and convert to numpy
    try:
        with Image.open(image_path) as img:
            gray = img.convert("L")
            arr = np.array(gray)
            return cv2.Laplacian(arr, cv2.CV_64F).var()
    except Exception:
        return 0.0

def get_image_hash(image_path: str) -> str:
    """Returns the perceptual hash (phash) of an image."""
    try:
        with Image.open(image_path) as img:
            return str(imagehash.phash(img))
    except Exception:
        return ""

def get_video_hashes(video_path: str) -> list[str]:
    """Extracts 3 keyframes (10%, 50%, 90%) via FFmpeg and returns their hashes."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]
        duration = float(subprocess.check_output(cmd).decode().strip())
    except Exception:
        duration = 0.0

    timestamps = [duration * 0.1, duration * 0.5, duration * 0.9] if duration > 0 else [0.1, 1.0, 2.0]
    hashes = []

    for ts in timestamps:
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            try:
                subprocess.run([
                    "ffmpeg", "-y", "-ss", str(ts), "-i", video_path,
                    "-vframes", "1", "-f", "image2", tmp.name
                ], capture_output=True, check=True)
                with Image.open(tmp.name) as img:
                    hashes.append(str(imagehash.phash(img)))
            except Exception:
                continue
    return hashes

def is_screenshot(image_path: str) -> bool:
    """Heuristic: detects phone screenshots by aspect ratio + solid-color bars."""
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            ratio = h / w if w > 0 else 0

            # Phone screenshots are typically ~16:9 portrait (ratio ~1.7-1.8)
            if ratio < 1.5 or ratio > 2.2:
                return False

            arr = np.array(img.convert("RGB"))
            # Check top 15% and bottom 15% for low color variance (solid bars)
            bar_h = int(h * 0.15)
            top_bar = arr[:bar_h]
            bot_bar = arr[h - bar_h:]

            top_var = np.mean([top_bar[:, :, c].var() for c in range(3)])
            bot_var = np.mean([bot_bar[:, :, c].var() for c in range(3)])

            return bool(top_var < 50 and bot_var < 50)
    except Exception:
        return False
