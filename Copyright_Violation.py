#!/usr/bin/env python3
"""
Tube-MP3 Downloader + Demucs Stem Splitter (4- or 6-stem, resume‐safe, GPU auto-detect)
© 2025 Copyright_Violation – professional refactor with GPU auto-detection
"""

import argparse
import logging
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

try:
    import torch
    HAS_CUDA = torch.cuda.is_available()
except ImportError:
    HAS_CUDA = False

from yt_dlp import YoutubeDL, DownloadError

# ── STEM DEFINITIONS ────────────────────────────────────────────────────────────
STEMS_6 = [
    "vocals.mp3",
    "drums.mp3",
    "bass.mp3",
    "guitar.mp3",
    "piano.mp3",
    "other.mp3",
]
STEMS_4 = [
    "vocals.mp3",
    "drums.mp3",
    "bass.mp3",
    "other.mp3",
]


def setup_logging() -> None:
    """Configure logging format and level"""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def find_executable(name: str) -> Optional[Path]:
    """Locate an executable in PATH"""
    path = shutil.which(name)
    if path:
        return Path(path)
    logging.warning("%s not found in PATH", name)
    return None


def run_subprocess(cmd: List[str]) -> None:
    """Run a subprocess command and handle errors"""
    logging.debug("Running command: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def open_folder(path: Path) -> None:
    """Open a folder in the system file explorer"""
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer.exe", str(path)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def run_demucs(
    mp3_files: List[Path],
    out_dir: Path,
    demucs_cmd: List[str],
    device: str,
    model_name: str
) -> None:
    """Separate stems using Demucs CLI or fallback module"""
    logging.info("Demucs: Processing %d file(s) with model %s on %s", len(mp3_files), model_name, device)
    for mp3 in mp3_files:
        logging.info(" - %s", mp3.name)
        cmd = [
            *demucs_cmd,
            str(mp3),
            "--device", device,
            "--segment", "7",
            "-n", model_name,
            "--mp3",
            "--filename", "{track}/{stem}.{ext}",
            "--out", str(out_dir)
        ]
        try:
            run_subprocess(cmd)
        except subprocess.CalledProcessError as e:
            logging.error("Demucs failed for %s: %s", mp3, e)


def sweep_directories(
    base: Path,
    demucs_cmd: List[str],
    device: str,
    stems: List[str],
    model_name: str
) -> None:
    """
    Scan subdirectories for unsplit MP3s and run Demucs on missing stems.
    (Example: ./downloads/MyFolder/*.mp3 → check ./downloads/MyFolder/<model_name>/<track>/)
    """
    for folder in base.iterdir():
        if not folder.is_dir():
            continue
        mp3s = list(folder.glob("*.mp3"))
        if not mp3s:
            continue

        pending = []
        for mp3 in mp3s:
            target_dir = folder / model_name / mp3.stem
            # If folder doesn't exist or is missing any expected stem, add to pending
            if not target_dir.exists() or not all((target_dir / s).exists() for s in stems):
                pending.append(mp3)

        if pending:
            logging.info("Folder %s: %d files to split", folder.name, len(pending))
            run_demucs(pending, folder, demucs_cmd, device, model_name)
        else:
            logging.info("Folder %s: all stems present", folder.name)


def download_audio(
    urls: List[str],
    out_dir: Path,
    ffmpeg_path: Optional[Path]
) -> List[Path]:
    """Download audio from YouTube URLs and return list of downloaded mp3 paths"""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"},
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata"},
        ],
        "ffmpeg_location": str(ffmpeg_path.parent) if ffmpeg_path else None,
        "quiet": False,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)
    return list(out_dir.glob("*.mp3"))


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="Tube-MP3 Downloader + Demucs Stem Splitter")
    parser.add_argument("urls", nargs="+", help="YouTube video URLs to download and process")
    parser.add_argument("--sweep", action="store_true", help="Sweep existing directories for MP3s missing stems")
    parser.add_argument("--split", action="store_true", help="Split newly downloaded MP3s into stems")
    parser.add_argument("--cpu", action="store_true", help="Force Demucs to run on CPU")
    # ── NEW: --stems flag ───────────────────────────────────────────────────────
    parser.add_argument(
        "--stems",
        type=int,
        choices=[4, 6],
        default=6,
        help="Number of stems to split: 4 or 6 (default: 6)"
    )
    args = parser.parse_args()

    base = Path.cwd()
    ffmpeg_path = find_executable("ffmpeg")
    if not ffmpeg_path:
        logging.error("ffmpeg is required. Please install ffmpeg.")
        sys.exit(1)

    demucs_path = find_executable("demucs")
    if demucs_path:
        demucs_cmd = [str(demucs_path)]
    else:
        demucs_cmd = [sys.executable, "-m", "demucs"]
        logging.info("Using fallback for Demucs: %s", " ".join(demucs_cmd))

    # Determine device automatically, unless forced
    device = "cpu" if args.cpu or not HAS_CUDA else "cuda"
    if device == "cuda":
        logging.info("CUDA available: using GPU for Demucs")
    else:
        logging.info("CUDA unavailable or forced CPU: using CPU for Demucs")

    # ── NEW: choose between 4‐stem or 6‐stem model ───────────────────────────────
    if args.stems == 6:
        stems = STEMS_6
        model_name = "htdemucs_6s"
    else:
        stems = STEMS_4
        model_name = "htdemucs"

    # If --sweep was passed, scan subfolders and split only missing stems
    if args.sweep:
        sweep_directories(base, demucs_cmd, device, stems, model_name)

    # Ensure downloads folder exists
    download_dir = base / "downloads"
    download_dir.mkdir(exist_ok=True)

    # Download any new MP3s
    mp3_list = download_audio(args.urls, download_dir, ffmpeg_path)

    # ── NEW “only‐split‐if‐missing” logic ─────────────────────────────────────────
    if args.split and mp3_list:
        to_split = []
        for mp3 in mp3_list:
            target_dir = download_dir / model_name / mp3.stem
            # Queue it if the folder doesn't exist or is missing any expected file
            if not target_dir.exists() or not all((target_dir / s).exists() for s in stems):
                to_split.append(mp3)
            else:
                logging.info("Skipping %s (all %d stems already present)", mp3.name, len(stems))

        if to_split:
            run_demucs(to_split, download_dir, demucs_cmd, device, model_name)

    # Open the folder after processing
    if mp3_list:
        open_folder(mp3_list[0].parent)

    logging.info("Processing complete.")


if __name__ == "__main__":
    main()
