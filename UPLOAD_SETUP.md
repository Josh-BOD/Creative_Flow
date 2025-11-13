# Creative Flow Upload System - Setup Guide

## Current Progress

✅ **Phase 1 - PARTIALLY COMPLETE**
- [x] Core folder structure created
- [x] Authentication module adapted from TJ tool
- [x] Upload manager CLI skeleton created
- [x] TJ uploader module created with Creative ID extraction
- [x] File validation implemented
- [x] Logging system set up
- [x] Configuration template created
- [ ] Dependencies installation (needs manual step)

---

## Setup Instructions

### Step 1: Install Dependencies

Run the setup script to install Playwright and other dependencies:

```bash
cd "/Users/joshb/Desktop/Dev/Creative Flow"
chmod +x setup_upload.sh
./setup_upload.sh
```

This will:
- Install `playwright`, `python-dotenv`, and `colorama`
- Install Chromium browser for Playwright
- Upgrade pip to latest version

### Step 2: Configure Credentials

1. Copy the environment template:
```bash
cp config/env_template.txt config/.env
```

2. Edit `config/.env` and add your TrafficJunky credentials:
```bash
TJ_USERNAME=your_actual_username
TJ_PASSWORD=your_actual_password
```

3. Adjust other settings as needed:
- `DRY_RUN=True` (keep True for testing, set False for live uploads)
- `HEADLESS_MODE=False` (keep False to see browser, True to hide)
- `TAKE_SCREENSHOTS=True` (useful for debugging)

**IMPORTANT**: The `config/.env` file is gitignored for security. Never commit it!

**Note**: This uses the same `.env` pattern as the TJ tool for consistency.

### Step 3: Test the Setup

Test that everything is working with a dry-run:

```bash
cd "/Users/joshb/Desktop/Dev/Creative Flow"
source venv/bin/activate
python3 scripts/upload_manager.py --session --verbose
```

You should see:
- Configuration loaded message
- Browser launches (if not headless)
- Login prompt (for first time)
- Files loaded from session CSV
- Dry-run simulated upload

---

## File Structure Created

```
Creative Flow/
├── scripts/
│   ├── upload_manager.py        # Main upload CLI tool
│   └── uploaders/
│       ├── __init__.py
│       ├── tj_auth.py          # TrafficJunky authentication
│       └── tj_uploader.py       # Creative upload handler
│
├── config/
│   ├── env_template.txt         # Template (copy to .env)
│   ├── .env                    # Your actual config (gitignored)
│   └── .gitignore              # Protects sensitive files
│
├── data/
│   └── session/                # Browser session storage
│
├── archive/                     # Uploaded files archive (future)
│
├── screenshots/                 # Upload screenshots (future)
│
├── setup_upload.sh             # Dependency installation script
│
└── requirements.txt            # Updated with new dependencies
```

---

## Usage Examples

### Dry-Run (Safe Testing)
```bash
# Test upload without actually uploading
python3 scripts/upload_manager.py --session
```

### Live Upload
```bash
# Actually upload files to TrafficJunky
python3 scripts/upload_manager.py --session --live
```

### Headless Mode
```bash
# Run without showing browser window
python3 scripts/upload_manager.py --session --live --headless
```

### Force Re-upload
```bash
# Re-upload files even if Creative ID already exists
python3 scripts/upload_manager.py --session --live --force
```

### Verbose Logging
```bash
# See detailed debug information
python3 scripts/upload_manager.py --session --verbose
```

---

## What's Implemented (Phase 1)

### ✅ upload_manager.py
- Command-line argument parsing
- Configuration loading from file
- Browser session management
- File loading from session CSV
- File validation (checks existence, skips ORG_ files)
- Logging to file and console
- TJ authentication integration

### ✅ tj_uploader.py
- Navigate to creative library
- Click "Add Creative" button
- Upload file via file input
- Extract Creative ID from `<span class="bannerId">` element
- Screenshot capture at each step
- Error handling and fallback Creative ID extraction

### ✅ tj_auth.py (from TJ tool)
- Manual login with reCAPTCHA handling
- Session persistence (saves/loads browser session)
- Auto-click LOGIN button when reCAPTCHA solved
- Session validation

---

## What's Next (Remaining Phases)

### Phase 2: Complete TJ Upload Flow
- [ ] Implement actual file upload loop in upload_manager.py
- [ ] Add upload status CSV tracking
- [ ] Test Creative ID extraction with real uploads
- [ ] Add retry logic for failed uploads

### Phase 3: Native Pair Upload
- [ ] Handle native video/image pair uploads
- [ ] Link pairs using native_pair_id
- [ ] Upload video and image separately

### Phase 4: Integration
- [ ] Add --upload flag to creative_processor.py
- [ ] Update master CSV with tj_creative_id column
- [ ] Implement archive functionality
- [ ] Move uploaded files to batch folders

### Phase 5: Polish
- [ ] Complete --files option for individual file uploads
- [ ] Add duplicate detection (check if Creative ID exists)
- [ ] Generate upload reports (summary, errors)
- [ ] Test with real creative files

---

## Troubleshooting

### "ERROR: Playwright not installed"
Run: `./setup_upload.sh` or manually install:
```bash
source venv/bin/activate
python -m pip install playwright python-dotenv colorama
playwright install chromium
```

### "ERROR: TrafficJunky credentials not configured!"
1. Copy `config/env_template.txt` to `config/.env`
2. Edit `config/.env` with your credentials

### "Session expired" or Login Issues
- Delete old session: `rm -f data/session/tj_session.json`
- Run again and complete manual login

### Browser Doesn't Open
- Check if `HEADLESS_MODE = False` in config
- Or remove `--headless` flag from command

---

## Next Steps for User

1. **Run setup_upload.sh** to install dependencies
2. **Create config/config.py** with your TJ credentials
3. **Test with dry-run**: `python3 scripts/upload_manager.py --session --verbose`
4. **Review logs** in `tracking/upload_log_*.txt`
5. **Report any issues** for further development

---

## Security Notes

🔒 **Protected Files (Gitignored):**
- `config/.env` - Contains credentials (same pattern as TJ tool)
- `data/session/*.json` - Browser sessions
- `screenshots/*.png` - May contain sensitive campaign data
- `tracking/upload_log_*.txt` - Contains upload details

⚠️ **Never commit these files to Git!**

---

## Questions or Issues?

If you encounter any issues during setup:
1. Check logs in `tracking/upload_log_*.txt`
2. Run with `--verbose` flag for detailed output
3. Check screenshots in `screenshots/` folder
4. Review error messages carefully

Ready to proceed? Run `./setup_upload.sh` first, then test with a dry-run!

