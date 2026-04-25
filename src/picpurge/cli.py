import os
import shutil
import zipfile
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import analyzer, core, metadata, ui

app = typer.Typer(
    name="picpurge",
    help="Image & Video Deduplicator for S3 Backups.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()

__version__ = "0.1.0"


def check_dependencies():
    """Verify system-level dependencies are available."""
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        console.print(f"[red]Error: Missing system dependencies: {', '.join(missing)}[/red]")
        console.print("[yellow]Install via: brew install ffmpeg[/yellow]")
        raise typer.Exit(code=1)


def version_callback(value: bool):
    if value:
        console.print(f"PicPurge version: [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = None,
):
    """
    PicPurge: A high-performance media deduplicator.
    """
    check_dependencies()


def process_file(path: str, blur_threshold: float):
    """Worker: returns (path, skip_reason|None, hash|None)."""
    kind = analyzer.classify_file(path)

    if kind == "video":
        hashes = analyzer.get_video_hashes(path)
        return path, None, hashes[0] if hashes else None

    if kind == "image":
        score = analyzer.get_blur_score(path)
        if 0.0 < score < blur_threshold:
            return path, "blurry", None

        if analyzer.is_screenshot(path):
            return path, "screenshot", None

        h = analyzer.get_image_hash(path)
        return path, None, h if h else None

    return path, "unknown_format", None


@app.command()
def process(
    folder: Annotated[
        str,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            help="Folder to scan for duplicates and blurry media.",
        ),
    ],
    blur_threshold: Annotated[
        float,
        typer.Option(help="Laplacian variance below this → blurry"),
    ] = 10.0,
    hash_threshold: Annotated[
        int,
        typer.Option(help="Max Hamming distance for near-duplicates"),
    ] = 2,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview skips without moving files"),
    ] = False,
):
    """
    Scan a folder: deduplicate, remove blurry/screenshots, and move rejects to skipped/.
    """
    all_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(folder)
        if "skipped" not in root.split(os.sep)
        for f in files if not f.startswith(".")
    ]

    console.print(f"Found [bold]{len(all_files)}[/bold] files in [bold]{folder}[/bold]")

    if not all_files:
        console.print("[green]Nothing to process.[/green]")
        return

    hashes_dict: dict[str, str] = {}
    auto_skipped: list[tuple[str, str]] = []  # (path, reason)

    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing", total=len(all_files))
        try:
            with ThreadPoolExecutor() as pool:
                futures = {pool.submit(process_file, f, blur_threshold): f for f in all_files}
                for future in as_completed(futures):
                    path, reason, file_hash = future.result()
                    if reason:
                        auto_skipped.append((path, reason))
                    elif file_hash:
                        hashes_dict[path] = file_hash
                    progress.advance(task)
        except Exception as e:
            console.print(f"\n[red]CRITICAL ERROR during processing:[/red] [bold]{e}[/bold]")
            console.print("[yellow]The process failed fast to prevent inconsistent state.[/yellow]")
            raise typer.Exit(code=1)

    # Rejection confirmation (blurry/screenshots)
    confirmed_skipped: list[str] = []
    skip_all = False
    for path, reason in auto_skipped:
        if skip_all:
            confirmed_skipped.append(path)
            continue

        choice = ui.prompt_rejection_confirmation(path, reason, is_dry_run=dry_run)
        if choice == "skip":
            confirmed_skipped.append(path)
        elif choice == "skip_all":
            confirmed_skipped.append(path)
            skip_all = True
        # if 'keep', we do nothing and the file stays in place

    # Duplicate grouping
    groups = core.group_identical_or_near(hashes_dict, hash_threshold)

    dup_skipped: list[str] = []
    for group in groups:
        ranked = metadata.rank_duplicates(group)
        # Always trigger the UI, but let it know if it's a dry run
        keep = ui.prompt_duplicate_resolution(ranked, is_dry_run=dry_run)
        dup_skipped.extend(f for f in ranked if f not in keep)

    all_skipped_paths = confirmed_skipped + dup_skipped

    if dry_run:
        console.print("\n[bold yellow]── Dry Run Report ──[/bold yellow]")
        for p in confirmed_skipped:
            # find the original reason from auto_skipped
            reason = next(r for path, r in auto_skipped if path == p)
            console.print(f"  [red]SKIP[/red] ({reason}) {os.path.basename(p)}")
        for p in dup_skipped:
            console.print(f"  [red]SKIP[/red] (duplicate) {os.path.basename(p)}")
        console.print(f"\n[bold]{len(all_skipped_paths)}[/bold] files would be moved to skipped/")
    else:
        if all_skipped_paths:
            console.print(f"Moving [bold]{len(all_skipped_paths)}[/bold] files to skipped/")
            core.move_to_skipped(all_skipped_paths, folder)
            ui.prompt_skipped_files(all_skipped_paths)
        else:
            console.print("No files skipped!")

    console.print("[green]Processing complete![/green]")


import threading

INCOMPRESSIBLE_EXTS = {
    # Images
    '.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.gif', '.avif', '.jp2',
    # Videos
    '.mp4', '.mov', '.mkv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', '.wmv', '.flv',
    # Audio
    '.mp3', '.m4a', '.aac', '.ogg', '.flac',
    # Docs
    '.pdf', '.docx', '.xlsx', '.pptx'
}

@app.command()
def archive(
    folder: Annotated[
        str,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            help="Folder to archive.",
        ),
    ],
    output: Annotated[
        str,
        typer.Option("--output", "-o", help="Output ZIP path"),
    ] = "collection.zip",
):
    """
    Losslessly archive the folder into a ZIP with integrity check.
    Uses smart format-specific compression logic.
    """
    output_path = os.path.abspath(output)
    base = output_path[:-4] if output_path.endswith(".zip") else output_path
    zip_path = f"{base}.zip"

    all_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(folder)
        if "skipped" not in root.split(os.sep)
        for f in files if not f.startswith(".")
    ]

    console.print(f"Archiving [bold]{len(all_files)}[/bold] files from [bold]{folder}[/bold]...")

    lock = threading.Lock()

    def archive_worker(file_path: str, zf: zipfile.ZipFile):
        ext = os.path.splitext(file_path)[1].lower()
        rel_path = os.path.relpath(file_path, folder)
        
        # Use STORED for already-compressed media to save CPU, DEFLATED for everything else
        compress_type = zipfile.ZIP_STORED if ext in INCOMPRESSIBLE_EXTS else zipfile.ZIP_DEFLATED
        
        with lock:
            zf.write(file_path, rel_path, compress_type=compress_type)

    with zipfile.ZipFile(zip_path, 'w', allowZip64=True) as zf:
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("{task.completed}/{task.total} files"),
            console=console,
        ) as progress:
            task = progress.add_task("Zipping", total=len(all_files))
            
            with ThreadPoolExecutor() as pool:
                futures = [pool.submit(archive_worker, f, zf) for f in all_files]
                for future in as_completed(futures):
                    future.result()
                    progress.advance(task)

    console.print("Verifying archive integrity...")
    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        count = len(zf.namelist())

    if bad:
        console.print(f"[red]Integrity check FAILED on: {bad}[/red]")
    else:
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        console.print(
            f"[green]✓ Archive verified — {count} files, {size_mb:.1f} MB → {zip_path}[/green]"
        )


if __name__ == "__main__":
    app()
