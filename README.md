# 📀 ReFoldr: Album Folder Renamer

This Python script renames music album folders into a consistent format:

```
YYYY - Album Title
```

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
- Standard library only (no external dependencies)

---

## 🚀 Usage

Download the script somewhere on your computer.

Make sure the script is executable:

```bash
chmod +x /path/to/refoldr.py
```

Run the script from the root of your music library or from inside an artist folder:

```bash
cd Music
/path/to/refoldr.py [options]
```


---

## 📌 Options

### **Dry Run**
Show what would be renamed without making changes:

```bash
./refoldr.py -d
```

### **Edge Cases**
By default, the script skips "edge cases" (remasters, deluxe editions, multi-year anthologies, etc.).  
You can force processing with the `-e/--edge` option:

- `r` → remasters
- `d` → deluxe editions
- `m` → multi-year anthologies

```bash
# Process remasters only
./refoldr.py -e r

# Process remasters + deluxe
./refoldr.py -e r,d

# Process all edge cases
./refoldr.py -e r,d,m
```

### **Levels**
Control which folder levels are processed.  
Default: `1,2` (Artist folders at level 1, Album folders at level 2)

```bash
# Rename albums inside Music/Artist/Album
./refoldr.py -l 1,2

# Run inside an Artist folder
cd Music/Artist
./refoldr.py -l 0,1

# Run inside a single Album folder (no band detection)
cd Music/Artist/Album
./refoldr.py -l -1,0
```

---

## 📜 Logs

The script creates two log files in the current directory:

- `renamed.log` → all folders that were renamed (or would be renamed in dry-run mode)
- `skipped.log` → all folders skipped (edge cases, already formatted, unchanged, etc.)

Paths are written **relative** to the folder where the script is executed.

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
./refoldr.py -d
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
