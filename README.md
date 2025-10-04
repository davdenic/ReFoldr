# 📀 ReFoldr: Album Folder Renamer

This Python script renames music album folders without the year into a consistent format:

```
YYYY - Album Title
```

It can grab the year from Discogs

It can run in dry-mode and preserve Remaster and Deluxe versions that are tipically released in a different year

---

An album folder that is inside "Band Name" folder is named "Band Name Something (2011) cd1"

It will be renamed "2011 - Something (Disc 1)"

From

```
Music/
├── Band Name/
│   ├── Band Name Something (2011) cd1/
```

To 

```
Music/
├── Band Name/
│   ├── 2011 - Something (Disc 1)/
```

---

It is designed to work with a typical music library structure:

```
Music/
├── Artist1/
│   ├── 1991 - Album Name/
│   └── Album Without Year/
├── Artist2/
│   └── Album (2002 Remastered)/
```

After running the script, folders will be renamed consistently, while respecting edge cases (like remastered editions, multi-year compilations, or deluxe versions).

---

## ⚙️ Requirements

- Python **3.7+**
- External dependencies:
    - requests
    - python-dotenv
---

## 🚀 Setup & Usage

Download somewhere on your computer.
```
git clone https://github.com/davdenic/ReFoldr
```


Make sure the script is executable:
```bash
chmod +x /path/to/refoldr.sh
```

# run script

```
# From the root of your music library
/path/to/refoldr.sh [options]
```


Run the script from the root of your music library or from inside an artist folder:

```bash
cd Music
/path/to/refoldr.sh [options]
```

**Use the dry-run option the first time and check the log files**

---

You can add your personal Discogs token to .env file to fetch the year from Discogs

---

## 📌 Options

### **Dry Run**
Show what would be renamed without making changes:

```bash
/path/to/refoldr.sh -d
```

### **Edge Cases**
By default, the script skips "edge cases" (remasters, deluxe editions, multi-year anthologies, etc.).  

```
Music/
└── Queen/
    ├── Greatest Hits (1980–1990)/
    └── Queen Greatest Hits (2011 Remaster)/
```

```
[SKIP] Edge case: Queen/Greatest Hits (1980–1990)
[SKIP] Edge case: Queen/Queen Greatest Hits (2011 Remaster)
```

You can force processing with the `-e/--edge` option:

- `r` → remasters
- `d` → deluxe editions
- `m` → multi-year anthologies

```bash
# Process remasters only
/path/to/refoldr.sh -e r

# Process remasters + deluxe
/path/to/refoldr.sh -e r,d

# Process all edge cases
/path/to/refoldr.sh -e r,d,m
```

### **Levels**
Control which folder levels are processed.  
Default: `1,2` (Artist folders at level 1, Album folders at level 2)

```bash
# Rename albums inside Music/Artist/Album
/path/to/refoldr.sh -l 1,2

# Run inside an Artist folder
cd Music/Artist
/path/to/refoldr.sh -l 0,1

# Run inside a single Album folder (no band detection)
cd Music/Artist/Album
/path/to/refoldr.sh -l -1,0
```

### Deflat (Flattened Folders)

Split combined Artist - Album folders into Artist/Album structure before renaming.
Use the --deflat flag to enable this behavior:

```
# Move "Artist - Album" folders into "Artist/Album"
/path/to/refoldr.sh --deflat
```

This is applied only at the first level inside your music root, so already correctly structured folders are not affected.

---

## 📜 Logs

The script creates two log files in the current directory:

- `renamed.log` → all folders that were renamed (or would be renamed in dry-run mode)
- `skipped.log` → all folders skipped (edge cases, already formatted, unchanged, etc.)
- `not_found.log` → albums not found via Discogs API when attempting to fetch the year
- `deflat.log` → folders that were moved or would be moved when using the --deflat option

Logs are written **relative** to the folder where the script is executed (your Music folder).

---

## 🔍 Example

Before:

```
Music/
└── Queen/
    ├── Queen Greatest Hits (2011 Remaster)/
    └── A Night at the Opera (1975)/
```

Command:

```bash
/path/to/refoldr.sh -d
```

Output:

```
[SKIP] Edge case: Queen/Queen Greatest Hits (2011 Remaster)
[DRY-RUN] Rename: Queen/A Night at the Opera (1975) -> Queen/1975 - A Night at the Opera
```

After running without `-d`:

```
Music/
└── Queen/
    ├── Queen Greatest Hits (2011 Remaster)/   # unchanged (edge case)
    └── 1975 - A Night at the Opera/
```

---

## ✅ Features

- Normalizes special characters (`@`, `~`, brackets → parentheses, multiple spaces)
- Removes trailing dashes/spaces
- Removes artist name from album folders (`Queen Greatest Hits` → `Greatest Hits`)
- Detects years and moves them to the beginning
- Handles apostrophes correctly (`John Mellencamp's Greatest Hits` → `Greatest Hits`)
- Supports dry-run and logging

---

## 📌 TODO (Future Improvements)

- Optional integration with **Discogs** or **MusicBrainz Picard** to fetch missing release years
- More advanced handling of multi-disc albums
