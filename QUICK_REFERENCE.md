# Quick Reference Guide

## Installation (One-Time Setup)

```bash
# Install ffmpeg (choose one method)
brew install ffmpeg                    # Option A: Homebrew
# OR download from https://evermeet.cx/ffmpeg/  # Option B: Direct download
# OR use MacPorts                      # Option C: sudo port install ffmpeg

# Create virtual environment
cd "/Users/joshb/Creative Flow"
python3 -m venv venv
source venv/bin/activate

# Install Python packages (with venv activated)
pip install -r requirements.txt
```

## Basic Usage

```bash
# Activate virtual environment first
source venv/bin/activate

# Preview processing (no changes made)
python3 scripts/creative_processor.py --dry-run

# Process files
python3 scripts/creative_processor.py

# Deactivate when done
deactivate
```

## File Organization

**Add files here:**
```
source_files/
├── Hentai/
├── Anime/
├── Solo-Female/
└── (your category folders)
```

**Processed files go here:**
```
uploaded/
└── ID-XXXXXXXX_EN_Category_Type_Name_Creator.ext
```

**CSV tracking:**
```
tracking/creative_inventory.csv
```

## Metadata Defaults Configuration

Edit `tracking/metadata_defaults.csv`:

```csv
folder_path,creator_name,language,content_type,creative_description
Hentai,Seras,EN,NSFW,Generic
Anime,John,EN,NSFW,Generic
Solo-Female,Maria,ES,NSFW,Solo
```

- **folder_path**: Must match your folder name in source_files/
- **creator_name**: Creator/artist name
- **language**: EN, ES, FR, DE, PT, etc.
- **content_type**: SFW or NSFW
- **creative_description**: Default name (usually "Generic")

## Supported File Types

**Videos:** .mp4, .mov, .avi, .webm, .mkv, .flv, .wmv  
**Images:** .jpg, .jpeg, .png, .gif, .webp, .bmp

## Naming Patterns

### Pattern 1: Structured (has all metadata)
```
EN_Anime_SFW_Anime-Abby_Pedro.mp4
→ ID-4A7B9C2E_EN_Anime_SFW_Anime-Abby_Pedro.mp4
```

### Pattern 2: Simple (uses folder defaults)
```
video-97551c12.mp4 (in Hentai folder)
→ ID-8F3D5A91_EN_Hentai_NSFW_Generic_Seras.mp4
```

## Creative Type Classifications

- **image**: Image files
- **short_video**: Videos < 23 seconds with 9:16 aspect ratio
- **video**: All other videos

## CSV Columns

| Column | Description |
|--------|-------------|
| unique_id | ID-XXXXXXXX (unique identifier) |
| original_filename | Original file name |
| new_filename | New standardized name |
| creator_name | Creator/artist |
| language | Language code |
| category | Content category |
| content_type | SFW/NSFW |
| creative_type | video/image/short_video |
| duration_seconds | Duration (0 for images) |
| aspect_ratio | e.g., 16:9, 9:16 |
| width_px | Width in pixels |
| height_px | Height in pixels |
| file_size_mb | File size |
| file_format | mp4, jpg, etc. |
| date_processed | Processing date |
| source_path | Original location |
| notes | Processing notes |

## Typical Workflow

1. **Edit metadata_defaults.csv** with your folders/creators
2. **Download files** from Google Drive to source_files/
3. **Run dry-run**: `python3 scripts/creative_processor.py --dry-run`
4. **Review output** for any issues
5. **Process files**: `python3 scripts/creative_processor.py`
6. **Check CSV** at tracking/creative_inventory.csv
7. **Import to Google Sheets** (copy/paste or upload CSV)

## Tips

✓ Always run --dry-run first  
✓ Keep folder names consistent with metadata_defaults.csv  
✓ Back up original files before first run  
✓ Files are moved (not copied) to uploaded/ folder  
✓ Original filenames are preserved in CSV

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "ffprobe not found" | Install ffmpeg: `brew install ffmpeg` |
| "Required packages" error | Run: `pip install -r requirements.txt` |
| No files processed | Check files are in source_files/ with correct extensions |
| Wrong metadata | Check folder names match metadata_defaults.csv exactly |
| "NEEDS MANUAL REVIEW" | Add folder to metadata_defaults.csv or use structured filename |

## Help

```bash
python3 scripts/creative_processor.py --help
```

## File Locations

- Script: `scripts/creative_processor.py`
- Config: `tracking/metadata_defaults.csv`
- Output CSV: `tracking/creative_inventory.csv`
- Source files: `source_files/`
- Processed files: `uploaded/`
- Full docs: `README.md`
- Setup guide: `SETUP_INSTRUCTIONS.md`

