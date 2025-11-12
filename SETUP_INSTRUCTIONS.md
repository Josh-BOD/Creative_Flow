# Setup Instructions

## Step 1: Install ffmpeg

ffmpeg is required for video metadata extraction.

### Option A: Using Homebrew (macOS)
```bash
brew install ffmpeg
```

### Option B: Direct Download (if you don't have Homebrew)
1. Download from: https://ffmpeg.org/download.html
2. For macOS: https://evermeet.cx/ffmpeg/ (easier static builds)
3. Extract and add to your PATH, or place in `/usr/local/bin/`

### Option C: Using MacPorts
```bash
sudo port install ffmpeg
```

### Verify Installation
After installation, verify it's working:
```bash
ffmpeg -version
ffprobe -version
```

## Step 2: Create Python Virtual Environment

**IMPORTANT**: Always use a virtual environment to avoid conflicts with system Python packages.

```bash
cd "/Users/joshb/Creative Flow"

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your terminal prompt now
```

## Step 3: Install Python Dependencies

With your virtual environment activated, install the required packages:

```bash
# Make sure you're in the Creative Flow directory with venv activated
pip install -r requirements.txt
```

This will install:
- `ffmpeg-python` - Python wrapper for ffmpeg (NOT the same as ffmpeg itself)
- `Pillow` - Image processing library
- `pandas` - CSV handling

**Note**: `pip install` is for Python packages. The `ffmpeg` from Step 1 is a system tool, not a Python package.

## Step 4: Configure Metadata Defaults

The file `tracking/metadata_defaults.csv` has been created with example data:

```csv
folder_path,creator_name,language,content_type,creative_description
Hentai,Seras,EN,NSFW,Generic
Anime,Seras,EN,NSFW,Generic
Solo-Female,Seras,EN,NSFW,Generic
Cumshot-Cannons,Seras,EN,NSFW,Generic
```

**Edit this file to match your actual folders and creators.** For example:

```csv
folder_path,creator_name,language,content_type,creative_description
Hentai,Seras,EN,NSFW,Generic
Anime,John,EN,NSFW,Anime-Style
Solo-Female,Maria,ES,NSFW,Solo
Lesbian,Alex,EN,SFW,Couples
```

## Step 5: Add Files to Process

Download your files from Google Drive and organize them in the `source_files/` directory:

```
source_files/
├── Hentai/           # Files here get Hentai category
│   ├── video-97551c12.mp4
│   └── video-abc12345.mp4
├── Anime/            # Files here get Anime category
│   ├── video-def67890.mp4
│   └── EN_Anime_SFW_Test_Pedro.mp4  # Structured filename
└── Solo-Female/      # Files here get Solo-Female category
    └── image-12345678.jpg
```

**Important**: Folder names should match the `folder_path` column in `metadata_defaults.csv`.

## Step 6: Run Dry Run Test

Before processing, always run a dry run to preview what will happen:

```bash
cd "/Users/joshb/Creative Flow"

# Activate virtual environment (if not already activated)
source venv/bin/activate

# Run dry run
python3 scripts/creative_processor.py --dry-run
```

This will:
- Show you what files were found
- Display what metadata would be extracted
- Preview new filenames
- Show processing summary
- **NOT make any changes**

Review the output carefully!

## Step 7: Process Files

If the dry run looks good, run the actual processing:

```bash
# Make sure venv is activated
source venv/bin/activate

# Process files
python3 scripts/creative_processor.py
```

This will:
- Generate unique IDs for each file
- Extract metadata (duration, resolution, aspect ratio)
- Rename files with standardized format
- Move files to `uploaded/` folder
- Create `tracking/creative_inventory.csv`

## Step 8: Review Results

After processing:

1. **Check the CSV**: Open `tracking/creative_inventory.csv`
   - Can be opened in Excel, Numbers, or imported to Google Sheets
   - Verify all metadata is correct

2. **Check uploaded files**: Look in `uploaded/` folder
   - Files should have new standardized names
   - Original names are preserved in CSV

3. **Look for issues**: Check console output for:
   - Files that needed manual review
   - Any errors or warnings

## Testing with Sample Files

If you want to test before processing your real files:

1. Create a test folder structure:
```bash
mkdir -p "/Users/joshb/Creative Flow/source_files/Test"
```

2. Copy a few test files:
```bash
# Copy some videos or images to test with
cp /path/to/test/video.mp4 "/Users/joshb/Creative Flow/source_files/Test/"
```

3. Add Test folder to metadata_defaults.csv:
```csv
folder_path,creator_name,language,content_type,creative_description
Test,TestUser,EN,SFW,TestFile
```

4. Run dry run:
```bash
python3 scripts/creative_processor.py --dry-run
```

## Common Issues & Solutions

### Issue: "ffprobe not found"
**Solution**: Install ffmpeg: `brew install ffmpeg`

### Issue: "Required packages not installed"
**Solution**: Install dependencies: `pip install -r requirements.txt`

### Issue: No files being processed
**Check**:
- Files are in `source_files/` directory (or subdirectories)
- Files have supported extensions (.mp4, .mov, .jpg, .png, etc.)
- Files aren't hidden (don't start with `.`)

### Issue: Wrong metadata applied
**Check**:
- Folder names in `source_files/` match `folder_path` in `metadata_defaults.csv`
- Folder names are case-sensitive
- No typos in metadata_defaults.csv

### Issue: "NEEDS MANUAL REVIEW" in notes
**Reason**: File doesn't match either naming pattern AND no defaults found for its folder

**Solution**: Either:
- Add the folder to `metadata_defaults.csv`, or
- Rename the file to use structured format: `Lang_Category_Type_Name_Creator.ext`

## Next Steps

1. Install ffmpeg (Step 1)
2. Create Python virtual environment (Step 2)
3. Install Python packages in venv (Step 3)
4. Update metadata_defaults.csv with your actual folders/creators (Step 4)
5. Download files from Google Drive to source_files/ (Step 5)
6. Run dry run test (Step 6)
7. Process files (Step 7)
8. Import CSV to Google Sheets (Step 8)

## Important Notes

### About Virtual Environments
Always activate your virtual environment before running the script:
```bash
source venv/bin/activate
```

To deactivate when done:
```bash
deactivate
```

### About Package Managers
- **pnpm/npm/yarn**: For JavaScript/Node.js packages only
- **pip**: For Python packages (what we need)
- **brew/port**: For system tools like ffmpeg

The `pnpm` command won't help with Python or ffmpeg installation. You need:
- `pip` for Python packages (ffmpeg-python, Pillow, pandas)
- Direct download or MacPorts for ffmpeg system tool

## Questions?

- See `README.md` for usage documentation
- See `TODO/plan.md` for detailed implementation plan
- See `TODO/Questions.md` for the original requirements

