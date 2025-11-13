# Plan 3: Upload Process - Questions to Answer

## Overview
Setting up the upload process for processed creative assets to be sent to advertising platforms or storage systems.

---

## Questions to Answer

### 1. Upload Destination
**What are you uploading to?**
- [X] TrafficJunky (native ads) to start then Exoclick later on


---

### 2. File Selection
**What files need to be uploaded?**
- [X] Both native and regular files (go in different sections)
- [x] Only new files from the current session (use session CSV)


**Should we upload original files?**
- [X] No, skip ORG_* files for natives (only upload native conversions)

---

### 3. Upload Method
**How do you upload?**
- [X] Manual upload through web interface by selecting the creative in the upload panel

---

### 4. Upload Tracking
**What information needs to be tracked after upload?**
- [X] Upload status (uploaded/pending/failed)
- [X] Upload date/time
- [X] Platform-specific IDs (creative ID assigned by platform)
- [X] Upload batch ID
- [X] Error messages (if upload failed)

**Where should we store this tracking data?**
- [X] New CSV file (e.g., `tracking/upload_status_(date)-(time).csv`)
- [X] Add columns to existing inventory CSVs only the platform-specific ID under the TJ Creative ID
- [X] Separate upload log file


---

### 5. Upload Workflow
**When should uploads happen?**
- [X] Immediately after processing (automatic) - with adding parameter to script like we have for native -- native so -- native -- upload
- [X] On demand (when you run a command)

**What should happen if upload fails?**
- [x] Log error and continue with other files

---

### 6. File Organization for Upload
**How should files be organized for upload?**
- [x] Keep current structure (separate folders for Native/Video and Native/Image)


---

### 7. Metadata Requirements
**What metadata does the platform need?**
- [X] none cause you upload in the upload panel

**How does the platform receive metadata?**
- [X] none cause you upload in the upload panel

---

### 8. Native Ad Pairs (VID + IMG)
**For native ads, how are video/image pairs handled?**
- [X] Upload separately (platform links them) - we link them when making campaigns by matching the unique IDS

**How does the platform identify pairs?**
- [X] Manual linking after upload in the campaign

---

### 9. Upload Validation
**What validation should we do before uploading?**
- [X] Check file exists

---

### 10. Post-Upload Actions
**What should happen after successful upload?**
- [X] Move files to an "uploaded" archive folder
- [X] Generate upload report/summary

---

## Example Upload Workflow

Based on your answers, we'll create a workflow like:

```
1. Read session CSV (new files from current run)
2. Filter files based on criteria (native only? all files?)
3. Validate each file (size, format, metadata)
4. Login to TJ
5. Go to media library
6. For Native select Native banner for Preroll select In-Stream Video
7. For Native select sub banner of Static banner to upload the images
8. For Nativge select sub banne of Rollover to upload videos
9. click Upload New creatives
10. In the Upload panel select browse your computer
11. Select creative to upload and wait for the to be uploaded.
12. Once all uploaded press close Upload panel
13. Track upload status in [tracking system]
14. Handle failures with [retry strategy]
15. Update all creatives with Creative ID from the platform found next to the Creative ID field on each creative.
16. Generate upload report
17. [Post-upload actions]
```

---

## Additional Clarifying Questions

### 11. Upload Preparation
When you run `--upload`, what should the system do to prepare files?
- No this is just to auto activate the upload once the creative naming is updarted.

---

### 12. Creative ID Entry
After you upload and get Creative IDs from TJ, how do you want to enter them back into the system?
- [X] **Option B**: CSV import - I want you to get them and update the master creative_inventory.csv I don't want to have to do anything manually.

---

### 13. File Organization for Native
For easier manual upload, should we organize native files like this?
```
ready_to_upload/
├── TJ_Native_Videos/          # Rollover - VID_*.mp4 files
├── TJ_Native_Images/          # Static banner - IMG_*.png files
└── TJ_Regular_Videos/         # In-Stream Video - regular .mp4 files (not ORG_) These are the different videos that are not Native not the ORG videos. The ORG vidoes are only there for future reference and never get uploaded.
```
- [X] **Different structure** (describe): See above

---

### 14. Upload Checklist/Guide
Should the script generate a step-by-step checklist for you to follow during upload - No the program is meant to uploade and get the creative IDS and updatre the creative_inventory.csv sheet.
```
UPLOAD CHECKLIST - Batch 2025-11-12_19:30
═══════════════════════════════════════════

NATIVE VIDEOS (Rollover - 8 files)
└─ Folder: ready_to_upload/TJ_Native_Videos/
   Files to upload:
   [ ] VID_EN_Cumshot_NSFW_Generic_Seras_4sec_ID-6BCC9A21-VID.mp4
   [ ] VID_EN_Cumshot_NSFW_Generic_Seras_4sec_ID-F427FB76-VID.mp4
   ...

Creative IDs: _____________________
```
- [ ] **Yes, this would help**
- [x] **No, keep it simple**

---

### 15. Archive Organization
After upload, how should archived files be organized?
- [x] **Option B**: By batch ID and date - `archive/batch_001-2025-11-12/`


---

### 16. Session CSV Filtering
For "only new files", do you want to:
- [X] **Upload everything in session CSV**: All files from current run
- [ ] **Skip certain creative types**: (e.g., skip ORG_ files, only upload VID_/IMG_/regular)
- [ ] **Your preference**: _______________

---

### 17. Upload Status Workflow
When tracking upload status, what states do files go through?

**Option A:**
```
pending → uploading → uploaded → archived
```

---

## Additional Notes/Requirements

Add any other requirements or constraints here:
- 
- 
- 

---

## Priority Level

What's the urgency for this upload system?
- [X] Critical - need ASAP

---

## Current Manual Process (if any)

Describe how you currently upload files (if applicable):
4. Login to TJ
5. Go to media library
6. For Native select Native banner for Preroll select In-Stream Video
7. For Native select sub banner of Static banner to upload the images
8. For Nativge select sub banne of Rollover to upload videos
9. click Upload New creatives
10. In the Upload panel select browse your computer
11. Select creative to upload and wait for the to be uploaded.
12. Once all uploaded press close Upload panel
13. Track upload status in [tracking system]
14. Handle failures with [retry strategy]
15. Update all creatives with Creative ID from the platform found next to the Creative ID field on each creative.
16. Generate upload report
This will help us understand what to automate.

