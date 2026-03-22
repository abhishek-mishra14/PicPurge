# Image & Video Deduplicator

A high-performance, parallelized media deduplicator for Python 3.14 (GIL-free). Safely clean up your trip photos before packing them for S3.

## 🚀 Features
- **Format Support**: JPEG, PNG, HEIC, HEIF, WebP, DNG, TIFF | MP4, MOV, MKV, AVI, 3GP, WebM
- **Blur Detection**: Laplacian variance with PIL fallback for HEIC
- **Screenshot Detection**: Heuristic-based phone screenshot filtering
- **Perceptual Deduplication**: `imagehash` (pHash) for images; FFmpeg keyframe extraction for videos (HDR/Dolby Vision safe)
- **EXIF-Aware Ranking**: Duplicates sorted by resolution → file size → date before display
- **Rich Progress Bar**: Live progress during parallel analysis
- **Dry-Run Mode**: Preview what would be skipped without moving files
- **Configurable Thresholds**: `--blur-threshold` and `--hash-threshold` CLI options
- **Lossless Archiving**: ZIP with integrity verification
- **33 Automated Tests**: Run in parallel via `pytest-xdist`

## 🛠 Prerequisites
```bash
brew install ffmpeg
```

## 📦 Setup
```bash
uv sync
```

## 🎮 Usage

### Process Media
```bash
# Standard run
uv run picpurge process /path/to/images_videos

# Dry-run (preview only)
uv run picpurge process /path/to/images_videos --dry-run

# Custom thresholds
uv run picpurge process /path/to/images_videos --blur-threshold 80 --hash-threshold 3
```

### Archive for S3
```bash
uv run picpurge archive /path/to/images_videos --output collection.zip
```

## 🧪 Testing
```bash
uv run python -m pytest tests/ -v
```

## 🏗 Architecture
- `src/dedup/cli.py` — Modern Typer CLI with Rich progress
- `src/dedup/analyzer.py` — Blur scoring, hashing, screenshot detection, format classification
- `src/dedup/metadata.py` — EXIF extraction and duplicate ranking
- `src/dedup/core.py` — Hash grouping and file movement
- `src/dedup/ui.py` — Tkinter comparison UI
- `main.py` — Thin shim for local development (`uv run main.py`)
