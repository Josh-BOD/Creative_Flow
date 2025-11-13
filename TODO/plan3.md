# Creative Flow Upload System - Implementation Plan

## Overview
Implement automated upload system to TrafficJunky using Playwright browser automation, based on the existing TJ tool pattern.

---

## System Architecture

### Components

1. **Upload Manager** (`scripts/upload_manager.py`)
   - Main orchestrator
   - Handles file staging and batch management
   - Coordinates with uploader modules
   - Tracks upload status

2. **TJ Uploader** (`scripts/uploaders/tj_uploader.py`)
   - Browser automation for TrafficJunky
   - File upload via web interface
   - Creative ID extraction
   - Error handling and retry logic

3. **Authentication** (`scripts/uploaders/tj_auth.py`)
   - Session management (reuse from TJ tool)
   - Manual login with reCAPTCHA handling
   - Session persistence

4. **Tracking System**
   - Upload status CSV: `tracking/upload_status_{date}-{time}.csv`
   - Master CSV update: Add platform Creative IDs
   - Upload log: Detailed operation log

---

## Technical Stack

### Dependencies (to add to requirements.txt)
```
playwright==1.48.0
python-dotenv==1.0.1
colorama==0.4.6
```

### Configuration (new file: `config/.env`)
```env
TJ_USERNAME=your_username
TJ_PASSWORD=your_password
HEADLESS_MODE=False
DRY_RUN=True
```

---

## Upload Workflow

### Step 1: File Preparation
1. Identify files to upload from session CSV
2. Validate file existence
3. Skip `ORG_` prefixed files
4. Group by type (regular video, regular image, native pairs)

### Step 2: Browser Initialization
1. Launch Playwright browser
2. Attempt to load saved session
3. If no session, perform manual login
   - User solves reCAPTCHA
   - Script auto-clicks LOGIN when enabled
4. Save session for future use

### Step 3: Campaign Selection
- **Manual Step (for now)**: User navigates to campaign
- **Future**: Script accepts campaign ID parameter

### Step 4: File Upload Loop

#### For Regular Files (Video/Image):
1. Navigate to creative library
2. Click "Add Creative" or equivalent
3. Upload file via file input
4. Wait for upload to complete
5. Extract Creative ID from page
6. Screenshot for verification
7. Log result

#### For Native Pairs (Video + Image):
1. Navigate to native campaign ad settings
2. Both files are uploaded separately
3. Link manually in campaign (or extract linking logic)
4. Extract both Creative IDs
5. Log results with shared `native_pair_id`

### Step 5: Status Tracking
1. Update `tracking/upload_status_{date}-{time}.csv` with:
   - File path
   - Upload timestamp
   - Platform Creative ID
   - Status (success/failed/pending)
   - Error message (if failed)
   - Batch ID

2. Update `tracking/creative_inventory.csv` with:
   - Add column: `tj_creative_id`
   - Match by `unique_id`

3. Write to upload log file

### Step 6: File Archiving
1. After successful upload, move file to archive
2. Archive structure: `archive/batch_{ID}-{date}/`
3. Maintain folder structure (Native/Video, Native/Image, etc.)

### Step 7: Report Generation
1. Summary report: Total uploaded, failed, skipped
2. Error report: List of failed uploads with reasons
3. Batch manifest: List of all files in batch

---

## File Structure

```
Creative Flow/
├── scripts/
│   ├── creative_processor.py (existing)
│   ├── native_converter.py (existing)
│   ├── upload_manager.py (NEW)
│   └── uploaders/
│       ├── __init__.py (NEW)
│       ├── tj_auth.py (NEW - adapted from TJ tool)
│       ├── tj_uploader.py (NEW - adapted from TJ tool)
│       └── exo_uploader.py (FUTURE)
│
├── config/
│   └── .env (NEW - gitignored)
│
├── tracking/
│   ├── creative_inventory.csv (existing)
│   ├── creative_inventory_session.csv (existing)
│   ├── upload_status_{date}-{time}.csv (NEW)
│   └── upload_log_{date}-{time}.txt (NEW)
│
├── archive/
│   └── batch_{ID}-{date}/
│       ├── Native/
│       │   ├── Video/
│       │   └── Image/
│       ├── Video/
│       └── Image/
│
├── uploaded/ (staging area before archive)
│   └── (files ready for upload)
│
└── data/
    └── session/
        └── tj_session.json (saved browser session)
```

---

## Command Line Interface

### Main Creative Processor (updated)
```bash
# Process files normally (no upload)
python3 scripts/creative_processor.py

# Process files and upload immediately
python3 scripts/creative_processor.py --upload

# Process files, upload to specific platform
python3 scripts/creative_processor.py --upload --platform tj

# Dry run for upload (process but don't actually upload)
python3 scripts/creative_processor.py --upload --dry-run
```

### Standalone Upload Tool (for on-demand uploads)
```bash
# Upload files from session CSV
python3 scripts/upload_manager.py --session

# Upload specific files
python3 scripts/upload_manager.py --files "file1.mp4,file2.jpg"

# Upload to specific campaign
python3 scripts/upload_manager.py --campaign 1234567890 --session

# Dry run
python3 scripts/upload_manager.py --session --dry-run

# Live mode (default is dry-run)
python3 scripts/upload_manager.py --session --live

# Headless mode (no browser window)
python3 scripts/upload_manager.py --session --headless
```

---

## Upload Status CSV Structure

File: `tracking/upload_status_{date}-{time}.csv`

| Column | Description | Example |
|--------|-------------|---------|
| unique_id | Creative unique ID | ID-F40623FA |
| file_path | Path to uploaded file | uploaded/Native/Video/VID_EN_... |
| file_name | Filename | VID_EN_Ahegao_NSFW_Generic_Seras_4sec_ID-F40623FA-VID.mp4 |
| upload_date | Date of upload | 2025-11-12 |
| upload_time | Time of upload | 14:32:15 |
| platform | Upload platform | TrafficJunky |
| campaign_id | Campaign ID (if applicable) | 1234567890 |
| tj_creative_id | TJ Creative ID | 9876543210 |
| status | Upload status | success |
| error_message | Error if failed | (empty or error text) |
| batch_id | Batch identifier | batch_001 |
| native_pair_id | Shared ID for native pairs | ID-F40623FA |
| retries | Number of retry attempts | 0 |

---

## Master CSV Updates

### New Columns for `tracking/creative_inventory.csv`:

| Column | Description | Example |
|--------|-------------|---------|
| tj_creative_id | TrafficJunky Creative ID | 9876543210 |
| tj_upload_date | TJ upload date | 2025-11-12 |
| tj_campaign_id | TJ campaign ID | 1234567890 |
| exo_creative_id | Exoclick Creative ID (future) | - |
| exo_upload_date | Exoclick upload date (future) | - |
| upload_status | Overall upload status | uploaded |

---

## Error Handling Strategy

### 1. Upload Failures
- **Issue**: File upload fails
- **Action**: 
  - Log error with screenshot
  - Mark as failed in status CSV
  - Continue with next file
  - Add to retry queue (future enhancement)

### 2. Creative ID Extraction Failure
- **Issue**: Can't find Creative ID on page
- **Action**:
  - Take screenshot
  - Mark as "unknown_id" status
  - Require manual ID entry (future: OCR or better selectors)

### 3. Network/Timeout Issues
- **Issue**: Page doesn't load or times out
- **Action**:
  - Wait and retry (3 attempts)
  - If still fails, mark as failed
  - Log timeout details

### 4. Authentication Expiry
- **Issue**: Session expires mid-upload
- **Action**:
  - Detect login redirect
  - Re-authenticate
  - Resume from last successful upload

### 5. File Not Found
- **Issue**: File path in CSV doesn't exist
- **Action**:
  - Skip file
  - Log warning
  - Mark as "file_not_found" status

---

## Implementation Phases

### Phase 1: Core Upload Infrastructure (Week 1)
**Priority: CRITICAL**
- [ ] Set up Playwright
- [ ] Adapt TJ auth module
- [ ] Create upload_manager.py skeleton
- [ ] Implement file validation
- [ ] Create upload status CSV structure
- [ ] Basic logging

### Phase 2: TrafficJunky Regular Upload (Week 1-2)
**Priority: CRITICAL**
- [ ] TJ regular creative upload automation
- [ ] Creative ID extraction
- [ ] Error handling and retry
- [ ] Screenshot capture
- [ ] Status tracking

### Phase 3: TrafficJunky Native Upload (Week 2)
**Priority: HIGH**
- [ ] Native pair upload logic
- [ ] Separate video/image handling
- [ ] Pair ID linking in tracking
- [ ] Validation for native format

### Phase 4: Integration with Processor (Week 2)
**Priority: HIGH**
- [ ] Add --upload flag to creative_processor.py
- [ ] Automatic upload after processing
- [ ] Master CSV update logic
- [ ] Archive functionality

### Phase 5: Standalone Upload Tool (Week 3)
**Priority: MEDIUM**
- [ ] upload_manager.py CLI implementation
- [ ] Session-based upload
- [ ] File-based upload
- [ ] Campaign parameter support

### Phase 6: Reporting & Archiving (Week 3)
**Priority: MEDIUM**
- [ ] Upload summary reports
- [ ] Error reports
- [ ] Batch manifest generation
- [ ] Archive folder management
- [ ] Cleanup of uploaded files

### Phase 7: Exoclick Support (Future)
**Priority: LOW**
- [ ] Exoclick uploader module
- [ ] Exoclick auth
- [ ] Multi-platform upload orchestration

---

## Testing Strategy

### Unit Tests
- File validation logic
- CSV parsing and updates
- Status tracking functions
- Archive operations

### Integration Tests
- Upload workflow (dry-run mode)
- Error handling scenarios
- Session management
- File movement

### Manual Testing Checklist
- [ ] Dry run upload (no actual uploads)
- [ ] Live upload single file
- [ ] Live upload batch of files
- [ ] Native pair upload
- [ ] Error scenarios (bad file, network issue)
- [ ] Session persistence across runs
- [ ] Archive functionality
- [ ] CSV updates (status and master)

---

## Security Considerations

1. **Credentials**
   - Store in `.env` file (gitignored)
   - Never hardcode in scripts
   - Use environment variables

2. **Session Files**
   - Store in `data/session/` (gitignored)
   - Delete on demand for security
   - Auto-expire after N days

3. **Screenshots**
   - May contain sensitive campaign data
   - Store in gitignored folder
   - Cleanup old screenshots

4. **Logs**
   - Don't log passwords
   - Sanitize Creative IDs in logs
   - Rotate logs regularly

---

## User Experience Flow

### First-Time Setup
1. User runs: `python3 scripts/upload_manager.py --setup`
2. Script prompts for TJ credentials
3. Creates `.env` file
4. Tests login
5. Saves session

### Daily Usage (Automatic)
1. User processes files: `python3 scripts/creative_processor.py --upload`
2. Script detects new files in session CSV
3. Opens browser (headless optional)
4. Uploads files automatically
5. Shows progress bar
6. Displays summary report
7. Archives files

### Daily Usage (Manual/On-Demand)
1. User runs: `python3 scripts/upload_manager.py --session --campaign 1234567890`
2. Browser opens (or runs headless)
3. Script uploads all files from session
4. User reviews upload report
5. Files moved to archive

---

## Success Criteria

✅ **Must Have:**
- Upload regular video/image files to TJ
- Extract Creative IDs automatically
- Track upload status in CSV
- Update master CSV with Creative IDs
- Error logging and screenshots
- Archive uploaded files
- Manual login with reCAPTCHA support

🎯 **Should Have:**
- Upload native pairs correctly
- Retry failed uploads
- Progress bars for batch uploads
- Summary reports
- Session persistence

💡 **Nice to Have:**
- Headless mode
- Multi-platform support (Exoclick)
- Automatic campaign detection
- Scheduling/cron support
- Upload analytics/dashboard

---

## Dependencies on Existing System

### Required Files/Functions:
- `tracking/creative_inventory_session.csv` (from processor)
- File paths from `uploaded/` folder
- Unique IDs format (ID-XXXXXXXX)
- Native pair IDs for linking

### Modifications Needed:
- Add `tj_creative_id` column to master CSV
- Add `--upload` flag to creative_processor.py
- Create archive folder structure
- Add upload status tracking

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| TJ website changes break selectors | HIGH | MEDIUM | Use flexible selectors, regular testing |
| reCAPTCHA blocks automation | HIGH | LOW | Manual login approach (already implemented) |
| Network timeouts during upload | MEDIUM | MEDIUM | Retry logic, longer timeouts |
| Creative ID extraction fails | HIGH | LOW | Screenshot + manual fallback |
| Session expires mid-upload | MEDIUM | MEDIUM | Re-auth logic, session refresh |
| File corruption during archive | HIGH | LOW | Verify before move, keep backups |

---

## Next Steps

1. **Review this plan** - User confirms approach
2. **Create Phase 1 TODOs** - Break down into tasks
3. **Install Playwright** - `pip install playwright && playwright install chromium`
4. **Adapt TJ auth module** - Copy and modify from TJ tool
5. **Build upload_manager skeleton** - CLI and basic structure
6. **Test with dry-run** - Validate workflow without actual uploads

---

## Questions for User

1. ✅ ANSWERED - Upload method confirmed (Playwright automation)
2. ✅ ANSWERED - Platform priority (TrafficJunky first, Exoclick later)
3. ✅ ANSWERED - Upload timing (immediate after processing + on-demand)
4. ✅ ANSWERED - File tracking (separate upload status CSV + master CSV update)
5. ✅ ANSWERED - Native uploads (separate files, manual linking in campaign)
6. ✅ ANSWERED - Error handling (log and continue, skip ORG_ files for native)
7. ✅ ANSWERED - Archive structure (batch ID and date folders)

**NEW QUESTIONS:**

8. **Creative ID Extraction**: Where on the TJ interface does the Creative ID appear after upload?
    - On the screen after upload in the element - <span class="bannerId">1032382001</span>

9. **Campaign Association**: When uploading regular files (not native), do we:
   - Associate later via separate tool (like existing TJ tool)

10. **Upload Progress Visibility**: Do you want:
    - Browser window visible by default (to see what's happening)? - want it the same as how the TJ tool runs.

11. **Batch Size**: Is there a limit to how many files to upload per session?
    - have to workout via testing.

12. **Duplicate Detection**: If a Creative ID already exists in master CSV, should we:
    - Skip upload (already uploaded) but Add --force flag - To re-upload even if Creative ID exists
---

## Estimated Timeline

- **Phase 1-3 (Core + TJ Upload)**: 1-2 weeks
- **Phase 4-5 (Integration + CLI)**: 1 week  
- **Phase 6 (Reporting)**: 3-5 days
- **Testing & Refinement**: 3-5 days

**Total Estimate**: 3-4 weeks for full implementation

---

## References

- Existing TJ Tool: `/Users/joshb/Desktop/Dev/Creative Flow/Code Examples/TJ_tool/`
- Key Files to Reference:
  - `src/auth.py` - Authentication logic
  - `src/uploader.py` - Regular ad upload
  - `src/native_uploader.py` - Native ad upload
  - `native_main.py` - Main orchestration
- Playwright Docs: https://playwright.dev/python/

