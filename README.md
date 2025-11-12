# Creative Asset Management System

A Python-based system to organize, track, and rename creative assets (videos and images) with automated metadata extraction and unique ID generation.

## Features

- **Dual Pattern Support**: Handles both structured filenames and simple naming patterns
- **Automated Metadata Extraction**: Extracts duration, resolution, aspect ratio automatically
- **Unique ID Generation**: Creates unique IDs (ID-XXXXXXXX format) for each asset
- **Flexible Defaults**: Configure metadata defaults per folder for mass processing
- **Google Sheets Ready**: Outputs CSV compatible with Google Sheets (V2 will integrate directly)
- **Dry Run Mode**: Preview changes before processing

## Quick Start

### 1. Install Dependencies

First, install ffmpeg (required for video metadata extraction):
```bash
# Option A: Using Homebrew
brew install ffmpeg

# Option B: Direct download from https://evermeet.cx/ffmpeg/ (if no Homebrew)

# Option C: Using MacPorts
sudo port install ffmpeg
```

Then create a virtual environment and install Python dependencies:
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

**Note**: Always activate your virtual environment (`source venv/bin/activate`) before running the script.

### 2. Configure Metadata Defaults

Edit `tracking/metadata_defaults.csv` to set defaults for your folders:

```csv
folder_path,creator_name,language,content_type,creative_description
Hentai,Seras,EN,NSFW,Generic
Anime,John,EN,NSFW,Generic
Solo-Female,Maria,ES,NSFW,Solo
```

Each row defines defaults for files in that folder.

### 3. Add Files

Place your files in `source_files/` directory. You can organize them in subfolders:

```
source_files/
├── Hentai/
│   ├── video-97551c12.mp4
│   └── video-abc12345.mp4
├── Anime/
│   └── EN_Anime_SFW_Test_Pedro.mp4
└── Solo-Female/
    └── image-12345678.jpg
```

### 4. Run Dry Run (Preview)

Test the processing without making changes:
```bash
python scripts/creative_processor.py --dry-run
```

This will show you what would happen without moving/renaming files.

### 5. Process Files

Run the actual processing:
```bash
python scripts/creative_processor.py
```

Files will be:
- Renamed with unique IDs and standardized format
- Moved to `uploaded/` folder
- Tracked in `tracking/creative_inventory.csv`

## Naming Patterns

### Pattern 1: Structured (All metadata in filename)
```
EN_Anime_SFW_Anime-Abby_Pedro.mp4
├─ Language: EN
├─ Category: Anime
├─ Type: SFW
├─ Name: Anime-Abby
└─ Creator: Pedro

Output: ID-4A7B9C2E_EN_Anime_SFW_Anime-Abby_Pedro.mp4
```

### Pattern 2: Simple (Metadata from folder + defaults)
```
video-97551c12.mp4 (in Hentai/ folder)
├─ Old ID: 97551c12 (discarded)
├─ Category: Hentai (from folder)
└─ Other data: From metadata_defaults.csv

Output: ID-8F3D5A91_EN_Hentai_NSFW_Generic_Seras.mp4
```

## CSV Output

The system generates **two CSV files**:

1. **Session CSV** (`tracking/creative_inventory_session.csv`)
   - Contains ONLY files from current run
   - Overwritten each time
   - Use for importing new files

2. **Master CSV** (`tracking/creative_inventory.csv`)
   - Contains ALL files ever processed
   - Appended to each run
   - Complete historical inventory

**Both CSVs include:**

| Column | Description |
|--------|-------------|
| unique_id | Unique identifier (ID-XXXXXXXX) |
| original_filename | Original file name |
| new_filename | New standardized filename |
| creator_name | Creator/artist name |
| language | Language code (EN, ES, FR, etc.) |
| category | Content category |
| content_type | SFW or NSFW |
| creative_type | video, image, short_video, native_video, native_image |
| duration_seconds | Video duration (0 for images) |
| aspect_ratio | Aspect ratio (e.g., 16:9, 9:16) |
| width_px | Width in pixels |
| height_px | Height in pixels |
| file_size_mb | File size in MB |
| file_format | File format (mp4, jpg, png, etc.) |
| date_processed | Processing date |
| source_path | Original file location |
| notes | Processing notes |
| native_pair_id | Links native video/image pairs |

## Creative Type Classification

- **image**: .jpg, .jpeg, .png, .gif, .webp files
- **short_video**: Videos under 23 seconds with 9:16 aspect ratio
- **video**: All other video files

## Folder Structure

```
Creative Flow/
├── venv/                                    # Virtual environment (gitignored)
├── scripts/
│   ├── creative_processor.py                # Main processing script
│   └── native_converter.py                  # Native ad format converter
├── source_files/                            # Place files here (organized in subfolders)
│   ├── native/                              # Files for native ad conversion (optional)
│   └── [category folders]/                  # Regular creative folders
├── uploaded/                                # Processed files (renamed)
│   ├── Native/                              # Native ad creatives (if processed)
│   │   ├── Video/                           # 640x360 native videos
│   │   └── Image/                           # 640x360 native thumbnails
│   └── [renamed files]                      # Regular processed files
├── tracking/
│   ├── creative_inventory.csv               # Master inventory (all time)
│   ├── creative_inventory_session.csv       # Session inventory (current run)
│   ├── metadata_defaults.csv                # Folder/creator defaults
│   └── processed_ids.json                   # Used IDs (prevents duplicates)
├── TODO/
│   ├── Questions.md
│   └── plan.md
├── requirements.txt
├── .gitignore
└── README.md
```

## Command Line Options

```bash
# Dry run (preview without changes)
python3 scripts/creative_processor.py --dry-run

# Process files
python3 scripts/creative_processor.py

# Use custom path
python3 scripts/creative_processor.py --path "/path/to/project"
```

## Tips

1. **Always run dry-run first** to preview changes
2. **Maintain folder structure** when downloading from Google Drive (folder names = categories)
3. **Update metadata_defaults.csv** before processing new batches
4. **Back up original files** before first run
5. **Check summary output** for files needing manual review

## Troubleshooting

### "ffprobe not found" error
Install ffmpeg: `brew install ffmpeg`

### "Required packages not installed" error
Install dependencies: `pip install -r requirements.txt`

### Files not being processed
- Check file extensions are supported
- Ensure files are in `source_files/` directory
- Look for errors in console output

### Wrong metadata applied
- Check `metadata_defaults.csv` for correct folder paths
- Folder names must match exactly (case-sensitive)

## Future Enhancements (V2)

- Direct Google Sheets integration
- Thumbnail generation
- Duplicate detection
- Web interface
- Batch import from Google Drive

## Questions?

See `TODO/plan.md` for detailed implementation plan.

