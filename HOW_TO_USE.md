# How to Use the Creative Asset Processor

## Quick Start

### 1. Add Files to Process
Place your videos and images in `source_files/` organized by category folders:
```
source_files/
├── Hentai/
│   ├── video-abc123.mp4
│   └── EN_Hentai_NSFW_Scene1_Seras.mp4
├── Anime/
├── Ahegao/
└── ... (other categories)
```

### 2. Run the Processor

**Dry Run (Preview Only):**
```bash
python3 scripts/creative_processor.py --dry-run
```

**Full Processing:**
```bash
python3 scripts/creative_processor.py
```

## Two Ways to Handle Metadata

### Option 1: CSV File (Bulk Setup) ✅ RECOMMENDED

Edit `tracking/metadata_defaults.csv` to add defaults for your folders:

```csv
folder_path,creator_name,language,content_type,creative_description
Hentai,Seras,EN,NSFW,Generic
Anime,Pedro,EN,SFW,Anime-Special
Solo-Female,Maria,ES,NSFW,Solo
```

**When to use:**
- Setting up multiple folders at once
- You know the folder structure in advance
- Quick bulk configuration

**How to edit:**
- Open in Excel, Google Sheets, Numbers, or any text editor
- Add a new row for each folder
- Save the file

See `tracking/metadata_defaults_TEMPLATE.csv` for detailed instructions and examples.

### Option 2: Interactive Mode (On-the-Fly)

When processing files, if a folder is NOT in the CSV, the script will prompt you:

```
⚠️  NEW FOLDER DETECTED: 'NewCategory'
================================================================================
This folder is not in metadata_defaults.csv.
Please provide default values for files in this folder:

Creator Name (e.g., Seras, Pedro, Maria): Alex
Language Code (e.g., EN, ES, FR, JP): EN
Content Type (SFW or NSFW): NSFW
Creative Description (default: Generic): Special

✓ Saved defaults for 'NewCategory' folder
```

The script will automatically save these answers to `metadata_defaults.csv` for future use!

**When to use:**
- You forgot to add a folder to the CSV
- Processing a new category for the first time
- Quick one-time setup

**To disable interactive mode:**
```bash
python3 scripts/creative_processor.py --no-interactive
```

## File Naming Patterns

The script handles two naming patterns:

### Pattern 1: Structured (All info in filename)
```
EN_Anime_SFW_Anime-Abby_Pedro.mp4
│  │     │   │          │
│  │     │   │          └─ Creator Name
│  │     │   └─ Creative Name
│  │     └─ Content Type (SFW/NSFW)
│  └─ Category
└─ Language Code
```

**Result:** All metadata extracted from filename, no defaults needed.

### Pattern 2: Simple (Uses folder defaults)
```
video-4cce10ea.mp4  (in folder: Hentai/)
```

**Result:** 
- Category: From folder name (Hentai)
- Other metadata: From `metadata_defaults.csv` or interactive prompt

## Output

**Processed files moved to:** `uploaded/`
- New filename: `EN_Hentai_NSFW_Generic_Seras_5sec_ID-1A2B3C4D.mp4`

**Two CSV Inventory Files:**

1. **Session CSV** (Current Run Only): `tracking/creative_inventory_session.csv`
   - Contains ONLY files processed in the current run
   - Gets overwritten each time you run the processor
   - Perfect for reviewing what just happened
   - Use this to upload/import only new files

2. **Master CSV** (All Time Cumulative): `tracking/creative_inventory.csv`
   - Contains ALL files ever processed
   - Gets appended to with each run
   - Historical record of your entire creative library
   - Use this for complete inventory management

**Why two files?**
- **Session CSV**: Quick reference for what you just processed - import only new files to your system
- **Master CSV**: Complete inventory - track your entire creative library over time

**Both include:**
- All metadata (creator, language, category, content_type)
- Technical specs (duration, dimensions, file size, aspect ratio)
- Processing notes and unique IDs
- Native pair tracking (for native ad creatives)
- Import into Google Sheets, Excel, or any spreadsheet software

**Unique IDs tracked in:** `tracking/processed_ids.json`
- Ensures no duplicate IDs across all files

**Automatic cleanup:** 
- Empty folders in `source_files/` are automatically removed after processing
- Keeps your workspace clean and organized

## Command Options

```bash
# Preview without making changes
python3 scripts/creative_processor.py --dry-run

# Full processing with interactive prompts (skips already-processed files)
python3 scripts/creative_processor.py

# Full processing WITHOUT interactive prompts
python3 scripts/creative_processor.py --no-interactive

# Force reprocess all files (even if already processed)
python3 scripts/creative_processor.py --force-reprocess

# Combine flags
python3 scripts/creative_processor.py --dry-run --force-reprocess

# Use custom base path
python3 scripts/creative_processor.py --path /path/to/folder
```

## Duplicate Detection

**By default, the script prevents reprocessing files:**
- Checks existing `creative_inventory.csv` for already-processed files
- Skips files that were previously processed
- Tracks by `source_path` (handles same filename in different folders)

**Example output:**
```
Found 20 media file(s)
  - 14 already processed (will skip)
  - 6 new file(s) to process

💡 Use --force-reprocess to reprocess all files
```

**When to use `--force-reprocess`:**
- Need to regenerate metadata for files
- Updated your metadata_defaults.csv and want to apply new values
- Fixed an issue and want to reprocess with corrections
- Migrating to new naming convention

## Native Creative Processing

Process videos for TrafficJunky native ads (640x360 video + thumbnail pairs):

### What is Native Processing?

Native processing converts videos into TrafficJunky-compatible native ad creatives:
- **Video**: 640x360 resolution, maximum 4 seconds
- **Image**: 640x360 PNG thumbnail (first frame)
- **Naming**: Automatic VID_/IMG_ prefixes with matching IDs

### How to Use

**Option 1: Use --native flag**
```bash
python3 scripts/creative_processor.py --native
```
Processes ALL videos in source_files/ for native format.

**Option 2: Place files in native subfolder**
```bash
source_files/
└── native/
    ├── video1.mp4
    └── video2.mp4
```
Automatically detects and processes only files in the native folder.

### Output Structure

```
uploaded/
├── Regular files (if processing non-native)
├── Native/
│   ├── Video/
│   │   └── VID_EN_Ahegao_NSFW_Generic_Seras_4sec_ID-ABC123-VID.mp4
│   └── Image/
│       └── IMG_EN_Ahegao_NSFW_Generic_Seras_ID-ABC123-IMG.png
```

### Naming Convention

**Native Video:**
```
VID_EN_Ahegao_NSFW_Generic_Seras_4sec_ID-0AE9FF9D-VID.mp4
 │   │   │     │    │       │       │    │           │
 │   │   │     │    │       │       │    │           └─ Suffix (-VID)
 │   │   │     │    │       │       │    └─ Unique ID
 │   │   │     │    │       │       └─ Duration (max 4 sec)
 │   │   │     │    │       └─ Creator Name
 │   │   │     │    └─ Creative Description
 │   │   │     └─ Content Type (SFW/NSFW)
 │   │   └─ Category
 │   └─ Language Code
 └─ Prefix (VID)
```

**Native Image:**
```
IMG_EN_Ahegao_NSFW_Generic_Seras_ID-0AE9FF9D-IMG.png
 │   │   │     │    │       │       │           │
 │   │   │     │    │       │       │           └─ Suffix (-IMG)
 │   │   │     │    │       │       └─ Unique ID (matches video)
 │   │   │     │    │       └─ Creator Name
 │   │   │     │    └─ Creative Description
 │   │   │     └─ Content Type
 │   │   └─ Category
 │   └─ Language Code
 └─ Prefix (IMG)
```

### Video + Image Pairs

- Each video generates a matching video/image pair
- Both share the same base ID for easy matching
- Video gets -VID suffix, image gets -IMG suffix
- CSV tracks pairs with `native_pair_id` column

### Example Commands

```bash
# Dry run with native processing
python3 scripts/creative_processor.py --native --dry-run

# Process native files only (from native folder)
python3 scripts/creative_processor.py

# Process with force reprocess
python3 scripts/creative_processor.py --native --force-reprocess

# Mix native and regular processing
# Put native files in source_files/native/
# Put regular files in source_files/other_folder/
python3 scripts/creative_processor.py
```

### CSV Output

Native files appear in the CSV with:
- `creative_type`: `native_video` or `native_image`
- `native_pair_id`: Shared ID linking video and image
- `width_px`: 640
- `height_px`: 360
- `aspect_ratio`: 16:9

## Tips

1. **Always test with --dry-run first** to preview what will happen
2. **Use the CSV for bulk setup** when you know your folder structure
3. **Use interactive mode as a safety net** for forgotten folders
4. **Keep metadata_defaults.csv updated** as you add new categories
5. **Check the summary at the end** to see which files need manual review
6. **For native processing**: Use the native subfolder method to separate native from regular files

## Troubleshooting

**"Files needing manual review":**
- These files don't match either naming pattern
- Their folder isn't in metadata_defaults.csv (and interactive was disabled)
- Add their folder to the CSV or run with interactive mode

**"Metadata defaults loaded: 0 folders":**
- Check that `tracking/metadata_defaults.csv` exists and has entries
- Make sure the CSV isn't corrupted or empty

**"Source directory does not exist":**
- Create the `source_files/` folder
- Add files organized in category subfolders

