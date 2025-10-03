#!/usr/bin/env python3
from dotenv import load_dotenv
import requests
import os
import re
import argparse
from pathlib import Path
import time
import unicodedata

load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

# Version 1.1.1

# ----------------------------
# Argument parser
# ----------------------------
parser = argparse.ArgumentParser(description="Rename album folders in 'YYYY - Album' format")
parser.add_argument("-d", "--dry-run", action="store_true", help="Show changes without renaming")
parser.add_argument("-e", "--edge", type=str, default="", help="Edge cases to process: r/remaster, d/delux, m/multiyears, comma-separated")
parser.add_argument("-l", "--level", type=str, default="1,2", help="Levels to process: start_level,end_level. Default 1,2")
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
    if not DISCOGS_TOKEN:
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
            msg = f"[NOT-FOUND] Discogs API not found for {band_name}/{album_title}"
            print(msg)
            not_found_log.write(msg + "\n")
            return None

        # pick the first master result with a year
        for r in results:
            year = r.get("year")
            if year:
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
    else:
        album_title = move_year_in_front(album_title)
        # If it does not start with a year, try Discogs
        if not re.match(r"^\d{4} - ", album_title):
            print(f"search albums \"{album_title}\" year on Discogs")
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
        msg = f"[SKIP] Already formatted: {rel_path}"
        print(msg)
        skipped_log.write(msg + "\n")
        return

    msg = f"{'[DRY-RUN] ' if args.dry_run else ''}Rename: {rel_path} -> {new_path}"
    print(msg)
    renamed_log.write(msg + "\n")

    if not args.dry_run:
        path.rename(new_path)

# ----------------------------
# Parse levels
# ----------------------------
try:
    start_level, end_level = map(int, args.level.split(","))
except Exception:
    print("Invalid -level format. Use start,end")
    exit(1)

root = Path.cwd()
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
    if level == end_level:
        rename_album_folder(path)
        dirnames.clear()

# ----------------------------
# Close log files
# ----------------------------
renamed_log.close()
skipped_log.close()
