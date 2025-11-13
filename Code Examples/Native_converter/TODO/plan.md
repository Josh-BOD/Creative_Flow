# Implementation Plan: TJ Creative Upload Integration

## Overview

Integrate TrafficJunky creative upload functionality into `video_processor.py` so that processed videos and thumbnails are automatically uploaded to TJ Media Library, with creative IDs saved to a CSV file for use with the `native_main.py` tool.

## User Requirements Summary

Based on Questions.md responses:

1. **Current Upload Method**: Manual through TJ web interface
2. **Desired Workflow**: 
   - Phase 1: Save files locally AND automatically upload to TJ Media Library → get creative IDs
   - Phase 2 (V2): Automatically generate Native campaign CSV
3. **Upload Info**: Just video/image files (no metadata)
4. **Target Processor**: `video_processor.py` (640x360 with PNG thumbnails)
5. **Upload Method**: Playwright automation (like existing TJ_tool)
6. **Output Format**: CSV file with creative IDs ready for use with `native_main.py`

---

## Architecture

### High-Level Flow

```
INPUT/
├── video1.mp4
├── video2.mp4
└── video3.mp4
        ↓
[video_processor.py processes videos]
        ↓
OUTPUT/
├── video1.png (640x360 thumbnail)
├── video2.png
└── videos/
    ├── video1.mp4 (640x360, 4sec)
    └── video2.mp4
        ↓
[NEW: creative_uploader.py uploads to TJ]
        ↓
OUTPUT/
└── creative_ids.csv
    (columns: filename, video_creative_id, thumbnail_creative_id, upload_timestamp, status)
```

---

## Implementation Plan

### Phase 1: Core Creative Upload Functionality

#### 1. Create New Module: `creative_uploader.py`

**Location**: `/Users/joshb/Desktop/Dev/Native_converter/src/creative_uploader.py`

**Purpose**: Handle uploading video/image files to TJ Media Library using Playwright automation

**Key Components**:

```python
class TJCreativeUploader:
    """Handles uploading creative files to TrafficJunky Media Library."""
    
    def __init__(self, dry_run=True, take_screenshots=True):
        """Initialize uploader with dry-run mode and screenshot settings."""
        
    def upload_creative(self, page, file_path, creative_type='video'):
        """
        Upload a single creative file to TJ.
        
        Args:
            page: Playwright page object (already authenticated)
            file_path: Path to video/image file
            creative_type: 'video' or 'image'
            
        Returns:
            Dict with {
                'status': 'success'|'failed',
                'creative_id': str,
                'filename': str,
                'error': str (if failed)
            }
        """
        
    def _navigate_to_media_library(self, page):
        """Navigate to TJ Media Library / Creative upload page."""
        
    def _upload_file(self, page, file_path, creative_type):
        """Handle the file upload interaction."""
        
    def _get_creative_id_from_page(self, page):
        """Extract the creative ID after successful upload."""
        
    def _take_screenshot(self, page, name, screenshot_dir):
        """Take screenshot if enabled."""
```

**Key Challenges**:
- Need to investigate TJ web interface to find:
  - URL for creative/media library upload page
  - File upload input selector
  - Where creative ID appears after upload
  - Whether video/image uploads have different workflows

**Pattern to Follow**: 
- Reuse patterns from `/Users/joshb/Desktop/Dev/Native_converter/Example_Code/TJ_tool/src/native_uploader.py`
- Similar error handling and logging
- Similar screenshot functionality

---

#### 2. Create Upload Manager: `upload_manager.py`

**Location**: `/Users/joshb/Desktop/Dev/Native_converter/src/upload_manager.py`

**Purpose**: Orchestrate batch uploads and CSV generation

**Key Components**:

```python
class CreativeUploadManager:
    """Manages batch creative uploads and result tracking."""
    
    def __init__(self, output_dir):
        """Initialize with output directory for CSV."""
        
    def process_output_folder(self, output_dir):
        """
        Scan OUTPUT folder for processed videos/thumbnails.
        Returns list of (video_path, thumbnail_path) tuples.
        """
        
    def upload_batch(self, page, creative_pairs, uploader):
        """
        Upload all creative pairs (video + thumbnail).
        
        Args:
            page: Playwright page (authenticated)
            creative_pairs: List of (video_path, thumbnail_path)
            uploader: TJCreativeUploader instance
            
        Returns:
            List of upload results
        """
        
    def save_results_to_csv(self, results, output_path):
        """
        Save upload results to CSV.
        
        CSV Format:
        - filename (base name without extension)
        - video_file_path
        - thumbnail_file_path
        - video_creative_id
        - thumbnail_creative_id
        - upload_status (success/failed)
        - upload_timestamp
        - error_message (if any)
        """
        
    def generate_native_campaign_csv(self, creative_ids_csv, output_path):
        """
        [PHASE 2] Generate Native campaign CSV from creative IDs.
        
        Output columns:
        - Ad Name
        - Target URL
        - Video Creative ID
        - Thumbnail Creative ID
        - Headline
        - Brand Name
        """
```

---

#### 3. Integrate with `video_processor.py`

**Location**: `/Users/joshb/Desktop/Dev/Native_converter/video_processor.py`

**Changes Needed**:

Add new main function for video processing + upload workflow:

```python
def process_and_upload():
    """
    Complete workflow:
    1. Process videos (existing functionality)
    2. Upload creatives to TJ
    3. Save creative IDs to CSV
    """
    
    # Step 1: Process videos (existing code)
    print("Step 1: Processing videos...")
    process_videos()
    
    # Step 2: Upload to TJ (new functionality)
    print("\nStep 2: Uploading creatives to TrafficJunky...")
    
    # Import upload modules
    from src.upload_manager import CreativeUploadManager
    from src.creative_uploader import TJCreativeUploader
    from Example_Code.TJ_tool.src.auth import TJAuthenticator
    from Example_Code.TJ_tool.config import Config
    from playwright.sync_api import sync_playwright
    
    # Initialize upload manager
    manager = CreativeUploadManager(output_dir=Path("OUTPUT"))
    
    # Get creative pairs from output folder
    creative_pairs = manager.process_output_folder(Path("OUTPUT"))
    
    if not creative_pairs:
        print("No creatives found to upload")
        return
    
    print(f"Found {len(creative_pairs)} creative pairs to upload")
    
    # Start browser automation
    with sync_playwright() as p:
        # Launch browser (reuse TJ_tool patterns)
        browser = p.chromium.launch(headless=False, slow_mo=500)
        
        # Authenticate (reuse TJ_tool auth)
        authenticator = TJAuthenticator(Config.TJ_USERNAME, Config.TJ_PASSWORD)
        context = authenticator.load_session(browser)
        
        if not context:
            # Manual login if no session
            context = browser.new_context()
            page = context.new_page()
            if not authenticator.manual_login(page):
                print("Authentication failed")
                return
            authenticator.save_session(context)
        else:
            page = context.new_page()
        
        # Initialize uploader
        uploader = TJCreativeUploader(dry_run=False, take_screenshots=True)
        
        # Upload batch
        results = manager.upload_batch(page, creative_pairs, uploader)
        
        # Save results to CSV
        csv_path = Path("OUTPUT") / f"creative_ids_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        manager.save_results_to_csv(results, csv_path)
        
        print(f"\nCreative IDs saved to: {csv_path}")
        
        browser.close()

# Update main() to offer choice
def main():
    """Main function with workflow options."""
    import sys
    
    print("Video Processing Tool")
    print("=" * 50)
    print("Options:")
    print("  1. Process videos only")
    print("  2. Process videos + Upload to TJ")
    print("  3. Upload existing OUTPUT files to TJ")
    
    # Check for command line args
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Select option [1/2/3]: ").strip()
    
    if choice == "1":
        process_videos()
    elif choice == "2":
        process_and_upload()
    elif choice == "3":
        upload_only()
    else:
        print("Invalid option")
```

---

#### 4. Create Standalone Upload Script: `upload_creatives.py`

**Location**: `/Users/joshb/Desktop/Dev/Native_converter/upload_creatives.py`

**Purpose**: Standalone script to upload existing processed files without reprocessing

**Key Features**:
- Scan OUTPUT folder for existing videos/thumbnails
- Upload to TJ
- Generate creative IDs CSV
- Command line arguments for dry-run, headless mode, etc.

**Similar to**: `/Users/joshb/Desktop/Dev/Native_converter/Example_Code/TJ_tool/native_main.py`

```python
#!/usr/bin/env python3
"""
Upload processed creatives to TrafficJunky Media Library.
"""

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Upload creatives to TrafficJunky Media Library'
    )
    parser.add_argument('--live', action='store_true', 
                       help='Disable dry-run mode')
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode')
    parser.add_argument('--input-dir', default='OUTPUT',
                       help='Directory containing processed creatives')
    # ... more arguments
    return parser.parse_args()

def main():
    """Main execution."""
    # Similar structure to native_main.py
    # 1. Setup logging
    # 2. Initialize components
    # 3. Authenticate to TJ
    # 4. Scan for creatives
    # 5. Upload batch
    # 6. Save CSV
    # 7. Generate report
```

---

### Phase 2: Enhanced Features (V2)

#### 5. Auto-Generate Native Campaign CSV

**Feature**: Automatically create CSV file ready for `native_main.py`

**Location**: Add to `upload_manager.py`

**CSV Template**:
```csv
Ad Name,Target URL,Video Creative ID,Thumbnail Creative ID,Headline,Brand Name
```

**Implementation**:
- Read creative IDs from Phase 1 output
- Generate ad names based on filename
- Prompt user for default values (Target URL, Headline, Brand Name)
- Save to `/Users/joshb/Desktop/Dev/Native_converter/Example_Code/TJ_tool/data/input/`

---

## File Structure

```
/Users/joshb/Desktop/Dev/Native_converter/
├── INPUT/                          # Source videos
├── OUTPUT/                         # Processed videos + thumbnails
│   ├── videos/                    # Processed MP4 files
│   ├── *.png                      # Thumbnails
│   └── creative_ids_*.csv         # NEW: Upload results
├── src/                           # NEW: Shared modules
│   ├── __init__.py
│   ├── creative_uploader.py       # Core upload logic
│   └── upload_manager.py          # Batch processing & CSV
├── logs/                          # NEW: Upload logs
│   └── creative_upload_*.log
├── screenshots/                   # NEW: Debug screenshots
│   └── creative_upload_*.png
├── video_processor.py             # MODIFIED: Add upload integration
├── upload_creatives.py            # NEW: Standalone upload script
├── requirements.txt               # MODIFIED: Add dependencies
└── TODO/
    ├── Questions.md
    └── plan.md                    # This file
```

---

## Dependencies

**New dependencies to add to `requirements.txt`**:

```
playwright==1.40.0
pandas==2.1.3
python-dotenv==1.0.0
```

**Reuse from TJ_tool**:
- Playwright browser automation
- Authentication module (`Example_Code/TJ_tool/src/auth.py`)
- Config module (for TJ credentials from `.env`)

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```
TJ_USERNAME=your_username
TJ_PASSWORD=your_password
DRY_RUN=true
HEADLESS_MODE=false
```

### Config Module

Option 1: Reuse `Example_Code/TJ_tool/config/config.py` (symlink or import)
Option 2: Create simplified config for this project

---

## Investigation Required

Before implementation can begin, need to research TJ web interface:

### Questions to Answer:

1. **Where is the creative upload page?**
   - URL for uploading videos/images
   - Is it under Media Library, Creatives, or Campaign creation?

2. **What is the upload workflow?**
   - Single file upload vs batch upload?
   - Separate pages for video vs image?
   - File input selector ID/class

3. **How are creative IDs displayed?**
   - Where does the creative ID appear after upload?
   - Is it in the URL, in a table, or in a success message?
   - Format of creative ID (numeric like campaign IDs?)

4. **Are there upload restrictions?**
   - File size limits
   - File format requirements (confirmed: MP4 for video, PNG for images)
   - Resolution requirements
   - Upload rate limiting

5. **Does the upload require metadata?**
   - Creative name field?
   - Tags or categories?
   - Any required fields besides the file itself?

### Investigation Method:

1. Manually log into TJ advertiser account
2. Navigate through the interface to find creative upload
3. Test upload a single video + image
4. Document the complete workflow
5. Use browser dev tools to inspect:
   - Network requests (any API calls?)
   - HTML structure (selectors for file input, buttons, etc.)
   - JavaScript events
6. Take screenshots at each step
7. Document findings in `TODO/tj_interface_research.md`

---

## Implementation Steps

### Step 1: Research TJ Interface (Manual Task)

- [ ] Log into TJ advertiser account
- [ ] Find creative upload page
- [ ] Test upload workflow
- [ ] Document selectors and workflow
- [ ] Create `TODO/tj_interface_research.md` with findings

### Step 2: Set Up Project Structure

- [ ] Create `src/` directory
- [ ] Create `logs/` directory
- [ ] Create `screenshots/` directory
- [ ] Create `.env` file with TJ credentials
- [ ] Update `requirements.txt` with new dependencies
- [ ] Run `pip install -r requirements.txt`
- [ ] Install Playwright browsers: `playwright install chromium`

### Step 3: Implement Core Upload Module

- [ ] Create `src/creative_uploader.py`
- [ ] Implement `TJCreativeUploader` class
- [ ] Implement navigation to upload page
- [ ] Implement file upload logic
- [ ] Implement creative ID extraction
- [ ] Add error handling and logging
- [ ] Add screenshot functionality

### Step 4: Implement Upload Manager

- [ ] Create `src/upload_manager.py`
- [ ] Implement `CreativeUploadManager` class
- [ ] Implement output folder scanning
- [ ] Implement batch upload orchestration
- [ ] Implement CSV generation
- [ ] Add progress tracking

### Step 5: Create Standalone Upload Script

- [ ] Create `upload_creatives.py`
- [ ] Implement argument parsing
- [ ] Implement main workflow
- [ ] Add logging setup
- [ ] Add error handling
- [ ] Test with dry-run mode

### Step 6: Integrate with Video Processor

- [ ] Modify `video_processor.py`
- [ ] Add `process_and_upload()` function
- [ ] Update `main()` with options
- [ ] Add command line arguments
- [ ] Test integrated workflow

### Step 7: Testing

- [ ] Test upload single video + thumbnail (dry-run)
- [ ] Test upload single video + thumbnail (live)
- [ ] Test upload multiple creatives (dry-run)
- [ ] Test upload multiple creatives (live)
- [ ] Test error handling (invalid file, network error, etc.)
- [ ] Test CSV output format
- [ ] Verify creative IDs work with `native_main.py`

### Step 8: Phase 2 Features (V2)

- [ ] Implement `generate_native_campaign_csv()` in upload manager
- [ ] Add command line option to auto-generate campaign CSV
- [ ] Test generated CSV with `native_main.py`
- [ ] Add user prompts for campaign metadata

### Step 9: Documentation

- [ ] Create README for upload functionality
- [ ] Document command line options
- [ ] Add example workflows
- [ ] Document CSV formats
- [ ] Create troubleshooting guide

---

## Risk Mitigation

### Potential Issues:

1. **Creative upload interface is complex**
   - Mitigation: Detailed investigation before implementation
   - Screenshot each step for reference

2. **Creative IDs are hard to extract**
   - Mitigation: Multiple extraction strategies (URL, table, API response)
   - Add logging to capture all possible locations

3. **Upload rate limiting**
   - Mitigation: Add delays between uploads
   - Implement retry logic with exponential backoff

4. **File format requirements**
   - Mitigation: Validate files before upload
   - Add pre-processing if needed (re-encode video, convert image format)

5. **Session management issues**
   - Mitigation: Reuse TJ_tool's proven authentication module
   - Save sessions after successful login

---

## Success Criteria

### Phase 1:
- [ ] Can automatically upload processed videos to TJ
- [ ] Can automatically upload processed thumbnails to TJ
- [ ] Creative IDs are correctly extracted and saved
- [ ] CSV output is correctly formatted
- [ ] Error handling works properly
- [ ] Dry-run mode works (simulates without uploading)
- [ ] Screenshots are captured for debugging

### Phase 2 (V2):
- [ ] Auto-generated Native campaign CSV is valid
- [ ] Generated CSV works with `native_main.py`
- [ ] User can customize campaign metadata

---

## Questions for User

Before implementation begins:

1. **TJ Credentials**: Do you have TJ advertiser account credentials in `.env` already from the TJ_tool project?

2. **Manual Investigation**: Are you able to manually test uploading a creative to TJ and document the workflow? Or should we do this together during implementation?

3. **File Naming**: How should ad names be generated in the Phase 2 CSV?
   - Use original filename?
   - Use a naming pattern?
   - Prompt user for each?

4. **Error Handling**: If a video upload succeeds but thumbnail fails (or vice versa), what should happen?
   - Skip the pair entirely?
   - Use partial upload?
   - Retry failed file?

5. **Batch Size**: How many creatives typically need to be uploaded at once?
   - This affects whether we need progress bars, pause/resume, etc.

---

## Timeline Estimate

**Phase 1**:
- Research: 1-2 hours (manual investigation of TJ interface)
- Implementation: 4-6 hours (core modules + integration)
- Testing: 2-3 hours
- **Total: 7-11 hours**

**Phase 2 (V2)**:
- Implementation: 2-3 hours
- Testing: 1 hour
- **Total: 3-4 hours**

**Overall Total: 10-15 hours**

---

## Next Steps

1. **User Review**: Review this plan and answer questions above
2. **Begin Investigation**: Manually test TJ creative upload workflow
3. **Document Findings**: Create `TODO/tj_interface_research.md`
4. **Start Implementation**: Begin with Step 2 (project structure)

---

## Notes

- Reuse as much as possible from `Example_Code/TJ_tool` (auth, config, patterns)
- Keep code simple and readable (junior dev friendly)
- Add extensive logging for debugging
- Follow existing code patterns from `native_uploader.py`
- Use dry-run mode by default to prevent accidental uploads during development

