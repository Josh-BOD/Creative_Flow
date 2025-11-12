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

**Tracking spreadsheet:** `tracking/creative_inventory.csv`
- Includes all metadata, technical specs, and processing notes
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

## Tips

1. **Always test with --dry-run first** to preview what will happen
2. **Use the CSV for bulk setup** when you know your folder structure
3. **Use interactive mode as a safety net** for forgotten folders
4. **Keep metadata_defaults.csv updated** as you add new categories
5. **Check the summary at the end** to see which files need manual review

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

