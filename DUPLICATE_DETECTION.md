# Duplicate Creative Detection

## Problem Discovered

When TrafficJunky detects a duplicate filename, it **does not create a new Creative ID**. Instead, it silently rejects the duplicate file. However, our previous code would extract whatever Creative IDs were visible on the page, which could be:
- Old IDs from previous uploads
- IDs from different files
- Completely unrelated Creative IDs

This resulted in **incorrect Creative IDs being stored in the CSV**, polluting the database with wrong data.

## Real-World Example

**Scenario:**
- First upload: `VID_EN_Cumshot_NSFW_Generic_Seras_4sec_ID-75BC7B51-VID.mp4` → Creative ID: `1032530471`
- Second upload (same file): `VID_EN_Cumshot_NSFW_Generic_Seras_4sec_ID-75BC7B51-VID.mp4` → **No new Creative ID**

**Old behavior:**
- Would extract any visible Creative IDs (e.g., `1032530361`, `1032530351`)
- Store these wrong IDs in `creative_inventory.csv`
- Generate incorrect TJ_tool CSVs with mismatched Creative IDs

**New behavior:**
- Detects that no **NEW** Creative ID was created
- Logs a warning: "⚠ No new Creative IDs - files may already exist on TJ"
- Marks files as `duplicate` status
- Does **NOT** store incorrect Creative IDs

## How It Works

### Step 1: Capture Existing Creative IDs (Before Upload)

```python
existing_ids = self._get_existing_creative_ids(page)
```

This captures all current Creative IDs from the Media Library page by extracting the `data-id` attribute from `.creativeContainer` elements:

```html
<div class="creativeContainer" data-id="1032530511">
```

### Step 2: Upload Files

Files are uploaded as a batch via the Dropzone interface.

### Step 3: Wait for Upload Completion

The system monitors Dropzone states (`dz-success dz-complete`) to ensure all files finish processing.

### Step 4: Extract NEW Creative IDs (After Upload)

```python
creative_ids = self._extract_new_creative_ids(page, uploaded_file_names, existing_ids)
```

This:
1. Gets all **current** Creative IDs from the page
2. Compares with `existing_ids` to find **NEW** IDs: `new_ids = current_ids - existing_ids`
3. For each NEW ID, extracts its filename from the `.creativeName` label
4. Matches filenames with our uploaded files to ensure correct pairing
5. Returns Creative IDs in the same order as uploaded files

### Step 5: Validate and Log

- **If NEW IDs found:** Status = `success`, store Creative IDs in CSV
- **If NO new IDs found:** Status = `duplicate`, log warning, skip CSV update

## HTML Element Structure

```html
<div class="creativeContainer globalCreativeContainer" 
     data-id="1032530511" 
     data-review-status="pending">
    
    <label class="creativeName checkboxLabel mb-0" 
           title="VID_EN_Cumshot_NSFW_Generic_Seras_4sec_ID-75BC7B51-VID">
        VID_EN_Cumshot_NSFW_Generic_Seras_4sec_ID-75BC7B51-VID
    </label>
    
    <span class="bannerId">1032530511</span>
</div>
```

**Key elements used:**
- `data-id` attribute: The Creative ID (most reliable)
- `.creativeName` label: The filename for matching
- `.bannerId` span: Alternative Creative ID source (fallback)

## Upload Status Types

| Status | Meaning | CSV Updated? | TJ_tool CSV? |
|--------|---------|--------------|--------------|
| `success` | New Creative IDs extracted | ✅ Yes | ✅ Yes |
| `duplicate` | No new IDs (file exists on TJ) | ❌ No | ❌ No |
| `failed` | Upload error or timeout | ❌ No | ❌ No |
| `dry_run_success` | Dry-run completed | ❌ No | ❌ No |

## Benefits

1. **Accuracy:** Only stores Creative IDs that were actually created during this upload
2. **Validation:** Matches Creative IDs to filenames to ensure correct pairing
3. **Duplicate Detection:** Identifies when files already exist on TJ
4. **Clean Data:** Prevents CSV pollution with incorrect Creative IDs
5. **Debugging:** Screenshots and detailed logs for troubleshooting

## Handling Duplicates

If you see duplicate warnings:

**Option 1: Use `--force` flag**
```bash
python3 scripts/upload_manager.py --session --live --force
```
This re-uploads files even if they have existing Creative IDs in the CSV. However, if TJ rejects them (same filename), they'll still be marked as duplicates.

**Option 2: Rename the files**
Change the filename in the `uploaded/` folder to avoid TJ's duplicate detection:
```bash
# Old name (duplicate):
VID_EN_Cumshot_NSFW_Generic_Seras_4sec_ID-75BC7B51-VID.mp4

# New name (unique):
VID_EN_Cumshot_NSFW_Generic_Seras_4sec_ID-75BC7B51-VID_v2.mp4
```

**Option 3: Delete from TJ Media Library**
Manually delete the creative from TJ's Media Library, then re-upload.

## Implementation Files

- **`scripts/uploaders/tj_uploader.py`**
  - `_get_existing_creative_ids()`: Captures IDs before upload
  - `_extract_new_creative_ids()`: Extracts only NEW IDs after upload
  - `upload_creative_batch()`: Orchestrates the validation flow

- **`scripts/upload_manager.py`**
  - Handles `duplicate` status in upload result processing
  - Logs duplicate warnings
  - Skips CSV updates for duplicates

## Logging Example

```
[2025-11-13 12:15:23] Found 42 existing creatives on page before upload
[2025-11-13 12:15:35] Extracting NEW Creative IDs (excluding 42 existing)...
[2025-11-13 12:15:36] Found 46 total creatives on page after upload
[2025-11-13 12:15:36]   ✓ NEW Creative: VID_EN_Cumshot_NSFW_Generic_Seras_4sec_ID-75BC7B51-VID → ID: 1032530511
[2025-11-13 12:15:36]   ✓ NEW Creative: IMG_EN_Cumshot_NSFW_Generic_Seras_ID-75BC7B51-IMG → ID: 1032530512
[2025-11-13 12:15:36] Found 4 NEW Creative IDs
[2025-11-13 12:15:36] ✓ Successfully uploaded 4 NEW creatives
```

Or, if duplicates detected:

```
[2025-11-13 12:20:45] Found 46 existing creatives on page before upload
[2025-11-13 12:20:58] Extracting NEW Creative IDs (excluding 46 existing)...
[2025-11-13 12:20:58] Found 46 total creatives on page after upload
[2025-11-13 12:20:58] ⚠ No new Creative IDs found - all files may be duplicates
[2025-11-13 12:20:58] 
⚠ No new Creative IDs - files may already exist on TJ:
  - VID_EN_Cumshot_NSFW_Generic_Seras_4sec_ID-75BC7B51-VID.mp4 (duplicate or already uploaded)
  - IMG_EN_Cumshot_NSFW_Generic_Seras_ID-75BC7B51-IMG.png (duplicate or already uploaded)
```

## Future Enhancements

1. **Creative ID lookup:** Query TJ API/page to find existing Creative IDs for duplicate files
2. **Automatic renaming:** Add suffix/version number to duplicates before upload
3. **Checksum validation:** Compare file hashes to detect true duplicates vs. renamed files
4. **Bulk duplicate check:** Pre-scan filenames before starting upload to warn user

