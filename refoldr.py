#!/usr/bin/env python3
from dotenv import load_dotenv
import requests
import os
import re
import sys
import argparse
from pathlib import Path
import time
import unicodedata

if getattr(sys, 'frozen', False):  # Running as PyInstaller exe
    base_path = Path(sys.executable).parent
else:  # Running as script
    base_path = Path(__file__).parent

env_path = base_path / "config.env"
load_dotenv(env_path)
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

# Version 1.2.3

# ----------------------------
# Argument parser
# ----------------------------
parser = argparse.ArgumentParser(description="Rename album folders in 'YYYY - Album' format")
parser.add_argument("-d", "--dry-run", action="store_true", help="Show changes without renaming")
parser.add_argument("-e", "--edge", type=str, default="", help="Edge cases to process: r/remaster, d/delux, m/multiyears, comma-separated")
parser.add_argument("-l", "--level", type=str, default="1,2", help="Levels to process: start_level,end_level. Default 1,2")
parser.add_argument("--deflat", action="store_true", help="Split combined 'Artist Album (Year)' folders into Artist/Album before renaming")
args = parser.parse_args()

# ----------------------------
# Edge cases to skip
# ----------------------------
EDGE_CASES = [
    "In Time_ The Best Of R.E.M.",
    "1992–2012 - The Anthology",
    "The Best Of 1980 1990 & B Sides",
    "The Best Of 1990-2000"
]

# ----------------------------
# Edge options mapping
# ----------------------------
EDGE_MAPPING = {"r": "remaster", "d": "delux", "m": "multiyears"}
EDGE_OPTIONS = set()
for opt in args.edge.lower().split(","):
    opt = opt.strip()
    if opt in EDGE_MAPPING:
        EDGE_OPTIONS.add(EDGE_MAPPING[opt])
    elif opt:
        EDGE_OPTIONS.add(opt)

# ----------------------------
# Log files
# ----------------------------
renamed_log = open("renamed.log", "w", encoding="utf-8")
skipped_log = open("skipped.log", "w", encoding="utf-8")
not_found_log = open("not_found.log", "w", encoding="utf-8")
deflat_log = open("deflat.log", "w", encoding="utf-8")

# ----------------------------
# Functions
# ----------------------------
def normalize_title(title: str) -> str:
    """
    Normalize title for Discogs search:
    - Remove accents
    - Remove quotes, underscores, dashes
    - Remove content inside parentheses or brackets
    - Collapse multiple spaces
    """
    # Normalize accented characters to ASCII
    title = unicodedata.normalize('NFKD', title)
    title = title.encode('ascii', 'ignore').decode('ascii')
    
    # Remove parentheses/brackets and their content
    title = re.sub(r"[\(\[].*?[\)\]]", "", title)
    
    # Remove quotes, underscores, dashes, and other punctuation except letters/numbers/spaces
    title = re.sub(r"[\"'_\-–—]", " ", title)
    
    # Collapse multiple spaces
    title = re.sub(r"\s+", " ", title).strip()
    
    return title

def get_year_from_discogs(band_name: str, album_title: str) -> str | None:
    """Query Discogs API for the official release year of an album."""
    
    print(f"[DISCOGS] search albums for \"{band_name} {album_title}\"...")
    if not DISCOGS_TOKEN:
        print("[DISCOGS][ERROR] Token not found in the ReFoldr root")
        return None
    
    url = "https://api.discogs.com/database/search"
    params = {
        "artist": normalize_title(band_name),
        "release_title": normalize_title(album_title),
        "token": DISCOGS_TOKEN,
        "type": "master"  # search for the master release
    }

    time.sleep(1.1)
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            msg = f"[DISCOGS][NOT-FOUND] Discogs API not found for {band_name}/{album_title}"
            print(msg)
            not_found_log.write(msg + "\n")
            return None

        # pick the first master result with a year
        for r in results:
            year = r.get("year")
            if year:
                print(f"[DISCOGS] year {year} found")
                return str(year)
       
        msg = f"[NOT-FOUND] Discogs API not found for {band_name}/{album_title}"
        print(msg)
        not_found_log.write(msg + "\n")
        return None

    except Exception as e:
        msg = f"[ERROR] Discogs API failed for {band_name}/{album_title}: {e}"
        print(msg)
        not_found_log.write(msg + "\n")
        return None


def sanitize(name: str) -> str:
    name = name.replace("@", "").replace("~", "")
    # name = re.sub(r"[\[]", "(", name)
    # name = re.sub(r"[\]]", ")", name)
    name = re.sub(r"[\{]", "", name)
    name = re.sub(r"[\}]", "", name)
    name = re.sub(r"[–—−]", "-", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"[-\s]+$", "", name)
    name = re.sub(r"(?<!\()(?<!\w)((?:cd|disc)(\d+))(?!\))", lambda m: f"(Disc {m.group(2)})", name, flags=re.IGNORECASE)
    return name

def remove_band_name(album_title: str, band_name: str) -> str:
    """
    Remove the band name from the beginning of album_title, including 
    an optional apostrophe+s or space immediately after the band name.
    """
    # pattern: band_name followed optionally by 's or space
    pattern = re.compile(rf"^{re.escape(band_name)}(['\s]?s)?\b", re.IGNORECASE)
    return pattern.sub("", album_title).lstrip(" -")

def move_year_in_front(album_title: str) -> str:
    match = re.search(r"\b(\d{4})\b", album_title)
    if not match:
        return album_title
    year = match.group(1)
    title = album_title.replace(year, "").strip(" -")
    title = re.sub(r"\(\s*\)", "", title).strip()
    return f"{year} - {title}" if title else year

def is_edge_case(path: Path) -> bool:
    base = str(path).lower()
    if "remaster" in base and "remaster" not in EDGE_OPTIONS:
        return True
    if "delux" in base and "delux" not in EDGE_OPTIONS:
        return True
    if re.search(r"\b\d{4}\s*[-–]\s*\d{4}\b", base) and "multiyears" not in EDGE_OPTIONS:
        return True
    for pattern in EDGE_CASES:
        if pattern.lower() in base:
            return True
    return False

def rename_album_folder(path: Path):
    album_title = path.name
    parent = path.parent
    band_name = parent.name
    rel_path = path.relative_to(Path.cwd())

    album_title = remove_band_name(album_title, band_name)
    album_title = sanitize(album_title)

    if is_edge_case(path):
        msg = f"[SKIP] Edge case: {rel_path}"
        print(msg)
        skipped_log.write(msg + "\n")
        pass
    else:
        album_title = move_year_in_front(album_title)
        # If it does not start with a year, try Discogs
        if not re.match(r"^\d{4} - ", album_title):
            year = get_year_from_discogs(band_name, album_title)
            if year:
                album_title = f"{year} - {album_title}"


    if not album_title:
        msg = f"[UNCHANGED] Empty title after sanitization: {rel_path}"
        print(msg)
        skipped_log.write(msg + "\n")
        return

    new_path = parent / album_title

    if new_path == path:
        # msg = f"[SKIP] Already formatted: {rel_path}"
        # print(msg)
        # skipped_log.write(msg + "\n")
        return

    msg = f"{'[DRY-RUN] ' if args.dry_run else ''}[RENAME]: {rel_path} -> {new_path}"
    print(msg)
    renamed_log.write(msg + "\n")

    if not args.dry_run:
        path.rename(new_path)


def contains_music_files(path: Path) -> bool:
    MUSIC_EXTS = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac"}
    return any(f.suffix.lower() in MUSIC_EXTS for f in path.iterdir() if f.is_file())

def is_flatten_dir_contains_music(path: Path) -> bool:
    # check if there are subfolders that contain music files
    if path.is_dir() and contains_music_files(path) and path.parent == root:
        return True
    return False

def deflat_dir(path: Path):
    """
    For flatten folders split the artist and move the folder inside an artist folder.
    From 'Music-Root/Artist - Album/' to 'Music-Root/Artist/Artist - Album/'
    """   
    parts = path.name.split(" - ", 1)
    if len(parts) < 2:
        msg = f"[DEFLAT][FAIL] Not found artist album {path}/"
    else:
        artist_name = parts[0].strip()
        album_name = parts[1].strip()
        artist_folder = path.parent / artist_name
        album_folder = artist_folder / album_name
        if not args.dry_run:
            artist_folder.mkdir(exist_ok=True)
            path.rename(album_folder)
            msg = f"[DEFLAT] {path.resolve()} -> {album_folder.resolve()}/"
        else:
            msg = f"[DRY-RUN][DEFLAT] {path.resolve()} -> {album_folder.resolve()}"
    
    print(msg)
    deflat_log.write(msg + "\n")

# ----------------------------
# Parse levels
# ----------------------------
try:
    start_level, end_level = map(int, args.level.split(","))
except Exception:
    print("Invalid -level format. Use start,end")
    exit(1)

root = Path.cwd()

# ----------------------------
# Deflat only on first level
# ----------------------------
if args.deflat:
    for folder in root.iterdir():
        if is_flatten_dir_contains_music(folder):
            deflat_dir(folder)

root_level = len(root.parts)
# ----------------------------
# Recursive loop for specified levels
# ----------------------------
for dirpath, dirnames, _ in os.walk(root, topdown=True):
    path = Path(dirpath)
    level = len(path.parts) - root_level

    if level < start_level:
        continue
    if level > end_level:
        dirnames.clear()
        continue

    # album renaming
    if level == end_level:
        rename_album_folder(path)
        dirnames.clear()

# ----------------------------
# Close log files
# ----------------------------
renamed_log.close()
skipped_log.close()
not_found_log.close()
deflat_log.close()