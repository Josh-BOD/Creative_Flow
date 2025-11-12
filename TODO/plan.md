# Creative Asset Management System - Implementation Plan

## Overview
Create a system to ingest 100+ videos and images from Google Drive, extract metadata, assign unique IDs, enforce naming conventions, and track everything in a spreadsheet.

## Key Requirements Summary
- Files located across multiple Google Drive folders
- Automated metadata extraction (duration, aspect ratio, resolution, file type)
- Unique ID format: ID-XXXXXXXX (random, never duplicated, discard old IDs)
- **Two naming patterns to handle:**
  1. Structured: (Language)_(Category)_(Type)_(Creative-Name)_(Your-Name).ext
  2. Simple: video-XXXXXXXX.mp4 (extract category from folder, use defaults for other fields)
- Short video definition: Under 23 seconds with 9:16 aspect ratio
- Rename files with new convention and move to "uploaded" folder
- Output: Google Sheets compatible CSV
- Support mass updates via metadata defaults file
- No complex folder structure needed

---

## System Architecture

### 1. Folder Structure
```
/Users/joshb/Creative Flow/
├── TODO/
│   ├── Questions.md
│   └── plan.md
├── scripts/
│   └── creative_processor.py          # Main processing script
├── source_files/                       # Where you'll place files from Google Drive
│   ├── Hentai/                        # Example category folder
│   ├── Anime/                         # Example category folder
│   └── ... (other category folders)
├── uploaded/                           # Processed files with new names
└── tracking/
    ├── creative_inventory.csv         # Master tracking spreadsheet
    ├── metadata_defaults.csv          # Defaults for folder/creator mapping
    └── processed_ids.json             # Track used IDs to prevent duplicates
```

### 2. Python Script Components

#### Core Features:
1. **Unique ID Generator**
   - Format: ID-XXXXXXXX (8 random hex characters)
   - Check against processed_ids.json to ensure no duplicates
   - Use secrets library for cryptographic randomness

2. **Metadata Extractor**
   - Video metadata: ffmpeg/ffprobe (duration, resolution, aspect ratio, codec)
   - Image metadata: Pillow (resolution, aspect ratio, format)
   - File system data: file size, creation date, modification date

3. **Filename Parser & Metadata Resolver**
   - **Pattern 1 (Structured)**: Parse (Language)_(Category)_(Type)_(Creative-Name)_(Your-Name).ext
   - **Pattern 2 (Simple)**: Detect video-XXXXXXXX.mp4 format, discard old ID
   - **Folder-based data**: Extract category from parent folder name
   - **Metadata defaults**: Load from metadata_defaults.csv for mass updates
   - **Priority order**: Filename data > metadata_defaults.csv > folder name > flag for manual entry
   - Flag files that don't match either pattern for manual review

4. **Creative Type Classifier**
   - Image: .jpg, .jpeg, .png, .gif, .webp
   - Short Video: duration < 23 seconds AND aspect ratio = 9:16 (0.5625)
   - Video: all other video files (.mp4, .mov, .avi, .webm, etc.)

5. **File Renamer**
   - New format: {UniqueID}_{Language}_{Category}_{Type}_{Creative-Name}_{Creator}.ext
   - Example: ID-4A7B9C2E_EN_Anime_SFW_Anime-Abby_Pedro.mp4
   - Sanitize filenames (remove special characters, limit length)

6. **CSV Generator**
   - Columns:
     - unique_id
     - original_filename
     - new_filename
     - creator_name
     - language
     - category
     - content_type (SFW/NSFW)
     - creative_type (video/image/short_video)
     - duration_seconds
     - aspect_ratio
     - width_px
     - height_px
     - file_size_mb
     - file_format
     - date_processed
     - source_path
     - notes (for flagged/unparseable files)

### 3. Metadata Defaults File (metadata_defaults.csv)

This file allows you to specify default values for files that don't have complete metadata in their filenames. Perfect for the simple naming pattern (video-XXXXXXXX.mp4).

**Format:**
| folder_path | creator_name | language | content_type | creative_description |
|-------------|--------------|----------|--------------|---------------------|
| Hentai | Seras | EN | NSFW | Generic |
| Anime | Seras | EN | NSFW | Generic |
| Solo-Female | Seras | EN | NSFW | Generic |

**Usage:**
- Script checks if file's folder matches any folder_path
- Applies defaults for missing metadata
- Category is always extracted from folder name
- Can be edited/expanded as you process more files

**Example:**
- File: `source_files/Hentai/video-97551c12.mp4`
- Folder match: "Hentai"
- Applied defaults: creator=Seras, language=EN, content_type=NSFW
- Category: Hentai (from folder)
- Result: `ID-4A7B9C2E_EN_Hentai_NSFW_Generic_Seras.mp4`

### 4. Required Python Libraries
```
pip install:
- ffmpeg-python (video metadata)
- Pillow (image metadata)
- pandas (CSV handling)
```

System requirements:
- ffmpeg/ffprobe installed (brew install ffmpeg)

---

## Implementation Steps

### Phase 1: Setup (Day 1)
1. Create folder structure
2. Install Python dependencies
3. Install ffmpeg via Homebrew
4. Create initial processed_ids.json file
5. Create metadata_defaults.csv with known defaults (e.g., Seras/EN/NSFW for Native files)
6. Test script on 5-10 sample files from both naming patterns

### Phase 2: File Collection (Day 1-2)
1. Download files from Google Drive to source_files/ folder
2. **IMPORTANT**: Maintain category folder structure (Hentai, Anime, Solo-Female, etc.)
3. For simple-named files (video-XXXXXXXX.mp4), folder name = category
4. Keep original Google Drive structure for reference

### Phase 3: Initial Processing (Day 2-3)
1. Run script in "dry-run" mode to preview:
   - What metadata can be extracted from both naming patterns
   - Which filenames parse successfully
   - Which Pattern 2 files match metadata_defaults.csv
   - Which files need manual categorization
2. Update metadata_defaults.csv if new folders/patterns discovered
3. Create supplementary spreadsheet for any files missing data
4. Manually fill in missing creator/category/language info (if any)

### Phase 4: Batch Processing (Day 3-4)
1. Run full processing script
2. Generate unique IDs for all files
3. Extract all metadata
4. Rename files with new convention
5. Move to uploaded/ folder
6. Generate creative_inventory.csv

### Phase 5: Verification (Day 4)
1. Verify all files processed correctly
2. Check for duplicate IDs (should be none)
3. Spot-check metadata accuracy
4. Validate CSV data completeness
5. Test opening CSV in Google Sheets

### Phase 6: Future File Handling (Ongoing)
1. Create quick-add script for new files
2. When receiving new creative:
   - Place in source_files/
   - Run script on single file
   - Appends to CSV
   - Moves to uploaded/

---

## Script Workflow

```
1. Load metadata_defaults.csv into memory
2. Scan source_files/ directory recursively
3. For each file:
   a. Generate unique ID (check for duplicates)
   b. Determine file type (video/image)
   c. Extract technical metadata (duration, resolution, aspect ratio)
   d. Detect naming pattern:
      - Pattern 1: Parse structured filename
      - Pattern 2: Detect simple format, extract folder name for category
   e. Resolve metadata:
      - Use filename data if available
      - Otherwise check metadata_defaults.csv for folder match
      - Extract category from folder name
      - Flag if critical data still missing
   f. Classify creative type (video/image/short_video)
   g. Generate new filename: ID-XXXXXXXX_Lang_Category_Type_Name_Creator.ext
   h. Rename and move to uploaded/
   i. Add row to CSV
   j. Save ID to processed_ids.json
4. Export final CSV
5. Generate summary report (counts by pattern, creator, category)
```

---

## Error Handling

### Files That Will Need Manual Review:
- Corrupted video/image files
- Unsupported formats
- Files with unparseable names
- Missing critical metadata

### Script Will:
- Skip corrupted files but log them
- Flag files missing creator/category data
- Create "needs_review" section in CSV
- Continue processing other files

---

## CSV Tracking Spreadsheet Structure

| unique_id | original_filename | new_filename | creator_name | language | category | content_type | creative_type | duration_seconds | aspect_ratio | width_px | height_px | file_size_mb | file_format | date_processed | source_path | notes |
|-----------|-------------------|--------------|--------------|----------|----------|--------------|---------------|------------------|--------------|----------|-----------|--------------|-------------|----------------|-------------|-------|
| ID-4A7B9C2E | EN_Anime_SFW_Anime-abby_Pedro.mp4 | ID-4A7B9C2E_EN_Anime_SFW_Anime-Abby_Pedro.mp4 | Pedro | EN | Anime | SFW | short_video | 15.5 | 9:16 | 1080 | 1920 | 12.4 | mp4 | 2025-11-12 | source_files/batch1/ | Pattern 1 |
| ID-8F3D5A91 | video-97551c12.mp4 | ID-8F3D5A91_EN_Hentai_NSFW_Generic_Seras.mp4 | Seras | EN | Hentai | NSFW | video | 45.2 | 16:9 | 1920 | 1080 | 28.7 | mp4 | 2025-11-12 | source_files/Hentai/ | Pattern 2, defaults applied |

---

## Dual Pattern Handling Examples

### Pattern 1: Structured Filename (All metadata in name)
**Input:** `EN_Anime_SFW_Anime-abby_Pedro.mp4` in folder `source_files/batch1/`

**Processing:**
- Language: EN (from filename)
- Category: Anime (from filename)
- Content Type: SFW (from filename)
- Creative Name: Anime-abby (from filename)
- Creator: Pedro (from filename)
- Generate new ID: ID-4A7B9C2E

**Output:** `ID-4A7B9C2E_EN_Anime_SFW_Anime-Abby_Pedro.mp4` → moved to `uploaded/`

### Pattern 2: Simple Filename (Metadata from folder + defaults)
**Input:** `video-97551c12.mp4` in folder `source_files/Hentai/`

**Processing:**
- Old ID: 97551c12 (discarded)
- Category: Hentai (from folder name)
- Check metadata_defaults.csv for "Hentai" folder match
- Apply defaults from CSV: creator=Seras, language=EN, content_type=NSFW
  - **NOTE**: These values are just an example for ONE creator (Seras)
  - Completely customizable per folder/creator in metadata_defaults.csv
  - Could be different creator, language, type for other folders
- Creative Name: Generic (default)
- Generate new ID: ID-8F3D5A91

**Output:** `ID-8F3D5A91_EN_Hentai_NSFW_Generic_Seras.mp4` → moved to `uploaded/`

### Pattern 2 with Multiple Creators/Defaults
The metadata_defaults.csv is completely flexible - you can have different creators, languages, and types for each folder:

```csv
folder_path,creator_name,language,content_type,creative_description
Hentai,Seras,EN,NSFW,Generic
Anime,John,EN,NSFW,Generic-Anime
Solo-Female,Maria,ES,NSFW,Solo
Cumshot-Cannons,Pedro,FR,NSFW,CC-Special
Lesbian,Alex,EN,SFW,Couples
```

**Example Results:**
- File in `Hentai/` folder → gets Seras as creator, EN language
- File in `Solo-Female/` folder → gets Maria as creator, ES language
- File in `Lesbian/` folder → gets Alex as creator, SFW content type

**This allows mass processing of files from different creators without manual entry for each file!**

---

## Additional Features to Consider

### Nice-to-Have Enhancements:
1. Thumbnail generation for videos
2. Duplicate detection (same file, different name)
3. Web interface for easier processing
4. Automatic Google Drive sync
5. Quality checks (resolution minimums, file size alerts)
6. Backup original filenames in separate log

### Future Workflow Improvements:
1. Google Drive integration (process without downloading)
2. Automated categorization using AI/ML
3. Batch import from multiple sources
4. Version tracking for updated creatives
5. Analytics dashboard for creative performance

---

## Success Criteria

- [ ] All 100+ files processed with unique IDs
- [ ] No duplicate IDs in system
- [ ] Metadata extracted for 95%+ of files
- [ ] Files renamed according to convention
- [ ] All files moved to uploaded/ folder
- [ ] Complete CSV tracking spreadsheet
- [ ] Files flagged for manual review identified
- [ ] Documentation for processing future files

---

## Time Estimate

- Setup & Testing: 2-3 hours
- File Collection: 1-2 hours (depends on download speed)
- Manual Data Entry: 2-4 hours (for files missing info)
- Batch Processing: 1-2 hours
- Verification: 1 hour
- **Total: 7-12 hours spread over 3-4 days**

---

## Key Benefits of This System

1. **Unified Tracking**: Both naming patterns consolidated into one system with unique IDs
2. **No Data Loss**: Old IDs discarded but original filenames preserved in CSV
3. **Mass Updates**: metadata_defaults.csv enables processing hundreds of files without manual entry
4. **Flexible**: Can mix both patterns in same batch
5. **Extensible**: Easy to add new categories/creators to defaults file
6. **Audit Trail**: CSV shows which pattern was used and what defaults were applied
7. **Future-Proof**: New files can follow either pattern and still integrate

## Next Steps

1. Review this plan
2. Confirm approach meets your needs
3. Begin implementation with Phase 1 setup
4. Create initial metadata_defaults.csv with known folders (Hentai, Anime, etc.)
5. Test on small batch (5 files from each pattern) before full processing
6. Process all 100+ files
7. Verify results and CSV completeness

