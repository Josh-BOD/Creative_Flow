# Creative Flow - Native Conversion Integration Plan (Plan 2)

## Overview

Integrate native video/image pair generation into the Creative Flow processor for TrafficJunky uploads. Processes videos to create 640x360 4-second clips with matching PNG thumbnails, using shared IDs and VID_/IMG_ prefixes.

## Requirements Summary

**Native Processing Specs:**
- Video: 640x360 resolution, 4-second duration max
- Image: 640x360 PNG thumbnail (first frame)
- Naming: VID_ and IMG_ prefixes with shared ID
- Output: `uploaded/Native/Video/` and `uploaded/Native/Image/`
- Trigger: `--native` flag OR files in `source_files/native/` folder

**Naming Convention Changes:**
- Original: `EN_Ahegao_NSFW_Generic_Seras_5sec_ID-0AE9FF9D.mp4`
- Native Video: `VID_EN_Ahegao_NSFW_Generic_Seras_5sec_ID-0AE9FF9D-VID.mp4`
- Native Image: `IMG_EN_Ahegao_NSFW_Generic_Seras_ID-0AE9FF9D-IMG.png`

## Implementation Status

### ✅ Completed Tasks

1. **Native Conversion Module** - `scripts/native_converter.py`
   - Created NativeConverter class
   - Resizes videos to 640x360 with center-crop
   - Limits duration to 4 seconds max
   - Extracts first frame as PNG thumbnail
   - Uses OpenCV (cv2) for processing

2. **Command-Line Flag** - `scripts/creative_processor.py`
   - Added `--native` argument
   - Enables native processing mode for all files

3. **Native Folder Detection** - `scripts/creative_processor.py`
   - Added `_detect_native_folder()` method
   - Auto-detects `source_files/native/` folder
   - Automatically enables native mode if native files exist

4. **Native Output Directories** - `scripts/creative_processor.py`
   - Created `uploaded/Native/Video/` directory
   - Created `uploaded/Native/Image/` directory
   - Directories created automatically when native mode enabled

5. **Native Filename Generator** - `scripts/creative_processor.py`
   - Added `_generate_native_filename()` method
   - Generates VID_ prefix for videos
   - Generates IMG_ prefix for images
   - Adds -VID/-IMG suffixes to unique IDs
   - Includes duration in video filenames

6. **Native Processing Method** - `scripts/creative_processor.py`
   - Added `_process_native_pair()` method
   - Converts videos using NativeConverter
   - Creates inventory records for both video and image
   - Returns list of records with shared native_pair_id

7. **CSV Schema Updates** - `scripts/creative_processor.py`
   - Added `native_pair_id` column to track video/image pairs
   - Added `native_video` creative type
   - Added `native_image` creative type
   - All records include native_pair_id (empty for non-native)

8. **Dependencies** - `requirements.txt`
   - Added opencv-python==4.8.1.78

9. **Documentation** - `HOW_TO_USE.md`
   - Added comprehensive native processing section
   - Documented both --native flag and folder detection methods
   - Included naming convention examples
   - Added usage examples and tips

## File Changes Summary

**New Files:**
- `scripts/native_converter.py` - Native conversion logic (173 lines)
- `TODO/plan2.md` - This plan document

**Modified Files:**
- `scripts/creative_processor.py` - Added native processing (~150 lines added)
- `requirements.txt` - Added opencv-python dependency
- `HOW_TO_USE.md` - Added native processing documentation (~100 lines added)

## How to Use

### Install Dependencies

```bash
pip install opencv-python==4.8.1.78
# Or install all dependencies:
pip install -r requirements.txt
```

### Process Native Files

**Option 1: Use --native flag**
```bash
python3 scripts/creative_processor.py --native --dry-run
python3 scripts/creative_processor.py --native
```

**Option 2: Use native subfolder** (auto-detected)
```bash
# Place files in source_files/native/
python3 scripts/creative_processor.py --dry-run
python3 scripts/creative_processor.py
```

### Verify Output

Check the following:
- `uploaded/Native/Video/` contains 640x360 MP4 files (VID_ prefix)
- `uploaded/Native/Image/` contains 640x360 PNG files (IMG_ prefix)
- `tracking/creative_inventory.csv` has:
  - `creative_type` = `native_video` or `native_image`
  - `native_pair_id` linking video/image pairs
  - Matching base IDs with -VID/-IMG suffixes

## Testing Checklist

- [x] Created native_converter.py module
- [x] Added --native command-line flag
- [x] Implemented folder detection
- [x] Created output directories
- [x] Implemented native filename generator
- [x] Implemented native processing method
- [x] Updated CSV schema with native fields
- [x] Added opencv dependency
- [x] Updated documentation
- [ ] Test with sample videos (manual verification needed)
- [ ] Verify video/image pairs match correctly
- [ ] Confirm 640x360 output resolution
- [ ] Verify 4-second max duration
- [ ] Test dry-run mode
- [ ] Test with native folder detection
- [ ] Test CSV output format

## Future Enhancements (Not in this plan)

- GIF_ prefix for animated GIFs
- IFRA_ prefix for iframe embeds
- Multiple output sizes (configurable dimensions)
- Direct upload to TrafficJunky Media Library
- Batch processing optimization
- Video quality settings
- Custom crop strategies

## Notes

- Native processing only applies to video files
- Images are not processed for native format (no conversion needed)
- Original files are still moved to `uploaded/` folder
- Native conversions are ADDITIONAL outputs, not replacements
- Each video generates 3 entries in CSV: original + native video + native image

## Integration with Existing Workflow

Native processing integrates seamlessly:
1. Files are processed normally (metadata extraction, renaming, etc.)
2. If native mode enabled + file is video → native pair created
3. Original file moved to `uploaded/`
4. Native video moved to `uploaded/Native/Video/`
5. Native image moved to `uploaded/Native/Image/`
6. All three tracked in single CSV

## Success Criteria

✅ All implementation tasks completed
✅ Documentation updated
✅ Dependencies added
⏳ Manual testing pending (user to verify)

---

**Status**: Implementation Complete - Ready for Testing
**Date**: November 12, 2025

