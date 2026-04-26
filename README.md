# PicPurge: Image & Video Deduplicator

A high-performance, parallelized media deduplicator for Python 3.13+. Safely clean up your trip photos before packing them for S3.

## 🚀 Features
- **Format Support**: JPEG, PNG, HEIC, HEIF, WebP, DNG, TIFF | MP4, MOV, MKV, AVI, 3GP, WebM
- **Blur Detection**: Laplacian variance with PIL fallback for HEIC
- **Screenshot Detection**: Heuristic-based phone screenshot filtering
- **Perceptual Deduplication**: `imagehash` (pHash) for images; FFmpeg keyframe extraction for videos (HDR/Dolby Vision safe)
- **EXIF-Aware Ranking**: Duplicates sorted by resolution → file size → date before display
- **Rich Progress Bar**: Live progress during parallel analysis (Multi-threaded)
- **Smart Archiving**: Optimized for S3 with format-specific compression (STORED for media, DEFLATED for text/raw)
- **Cross-Platform UI**: Beautifully centered interactive windows on macOS, Linux, and Windows

## 📥 Installation

### 1. Standalone Binary (Single Click)
Download the latest pre-built binary for your OS from the [Releases](https://github.com/abhishek-mishra14/PicPurge/releases) page. No Python setup required!

### 2. Using `uv` (Recommended for Devs)
```bash
uv tool install picpurge
```

### 3. Using `pip`
```bash
pip install picpurge
```

## 🛠 Prerequisites
```bash
# Required for video processing
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
uv run picpurge process /path/to/media

# Dry-run (preview only)
uv run picpurge process /path/to/media --dry-run

# Custom thresholds
uv run picpurge process /path/to/media --blur-threshold 20 --hash-threshold 3
```

### Archive for S3
```bash
# Creates a ZIP with smart compression (fast & space-efficient)
uv run picpurge archive /path/to/media --output collection.zip
```

## 🛠 CLI Reference

### `picpurge process [FOLDER]`
Scans a directory for duplicates, blurry images, and screenshots.

| Flag | Default | Description |
| :--- | :--- | :--- |
| `--blur-threshold` | `10.0` | Laplacian variance score. Lower = more lenient. |
| `--hash-threshold` | `2` | Max Hamming distance for pHash. `0` = identical, `2-5` = near-dups. |
| `--dry-run` | `false` | Reports what would happen without moving any files. |

### `picpurge archive [FOLDER]`
Creates a verified ZIP archive of the processed media.

| Flag | Default | Description |
| :--- | :--- | :--- |
| `--output`, `-o` | `collection.zip` | The destination path for the ZIP archive. |

## 🧪 Testing
```bash
# Runs 36 automated tests in parallel
uv run pytest tests/ -n auto
```

## 🏗 Architecture
- `src/picpurge/cli.py` — Modern Typer CLI with Rich progress
- `src/picpurge/analyzer.py` — Blur scoring, hashing, screenshot detection, FFmpeg logic
- `src/picpurge/metadata.py` — EXIF extraction and duplicate ranking
- `src/picpurge/core.py` — Hash grouping and file movement
- `src/picpurge/ui.py` — Tkinter comparison UI (Cross-platform centering)
- `main.py` — Thin shim for local development
