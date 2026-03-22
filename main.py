import os
import sys
import shutil
import zipfile
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.dedup import analyzer, core, metadata, ui

app = typer.Typer()
console = Console()


def check_dependencies():
    """Verify system-level dependencies are available."""
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        console.print(f"[red]Error: Missing system dependencies: {', '.join(missing)}[/red]")
        console.print("[yellow]Install via: brew install ffmpeg[/yellow]")
        raise typer.Exit(code=1)


@app.callback()
def main_callback():
    """Image & Video Deduplicator for S3 Backups."""
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
    folder: str,
    blur_threshold: float = typer.Option(50.0, help="Laplacian variance below this → blurry"),
    hash_threshold: int = typer.Option(5, help="Max Hamming distance for near-duplicates"),
    dry_run: bool = typer.Option(False, help="Preview what would be skipped without moving files"),
):
    """Scan a folder: deduplicate, remove blurry/screenshots, move rejects to skipped/."""
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        console.print(f"[red]Folder {folder} does not exist.[/red]")
        raise typer.Exit(code=1)

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
    skipped: list[tuple[str, str]] = []  # (path, reason)

    with Progress(
        SpinnerColumn(), BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("{task.completed}/{task.total}"), console=console
    ) as progress:
        task = progress.add_task("Analyzing", total=len(all_files))
        with ThreadPoolExecutor() as pool:
            futures = {pool.submit(process_file, f, blur_threshold): f for f in all_files}
            for future in as_completed(futures):
                path, reason, file_hash = future.result()
                if reason:
                    skipped.append((path, reason))
                elif file_hash:
                    hashes_dict[path] = file_hash
                progress.advance(task)

    # Duplicate grouping
    groups = core.group_identical_or_near(hashes_dict, hash_threshold)

    dup_skipped: list[str] = []
    for group in groups:
        ranked = metadata.rank_duplicates(group)
        if dry_run:
            dup_skipped.extend(ranked[1:])
        else:
            keep = ui.prompt_duplicate_resolution(ranked)
            dup_skipped.extend(f for f in ranked if f not in keep)

    all_skipped_paths = [p for p, _ in skipped] + dup_skipped

    if dry_run:
        console.print("\n[bold yellow]── Dry Run Report ──[/bold yellow]")
        for p, reason in skipped:
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


@app.command()
def archive(folder: str, output: str = typer.Option("collection.zip", help="Output ZIP path")):
    """Losslessly archive the folder into a ZIP."""
    folder = os.path.abspath(folder)
    output_path = os.path.abspath(output)
    base = output_path[:-4] if output_path.endswith(".zip") else output_path

    console.print(f"Archiving [bold]{folder}[/bold]...")
    shutil.make_archive(base, "zip", folder)

    zip_path = f"{base}.zip"
    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        count = len(zf.namelist())

    if bad:
        console.print(f"[red]Integrity check FAILED on: {bad}[/red]")
    else:
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        console.print(f"[green]✓ Archive verified — {count} files, {size_mb:.1f} MB → {zip_path}[/green]")


if __name__ == "__main__":
    app()
