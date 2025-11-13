# Migration to .env Configuration

## What Changed?

We've switched from Python `config.py` files to `.env` files (using python-dotenv) to match the **TJ tool pattern**.

## Why?

1. ✅ **Consistency** - Same pattern as TJ tool
2. ✅ **Security** - Environment variables, not Python imports
3. ✅ **Standard** - Industry best practice
4. ✅ **Simpler** - Easier to edit (no Python syntax)
5. ✅ **Deployment-friendly** - Works with Docker, cloud platforms, etc.

## Migration Steps

If you already created `config/config.py`:

### Option 1: Use the Template
```bash
cp config/env_template.txt config/.env
# Edit config/.env with your credentials
```

### Option 2: Migrate Your Existing config.py
If you have `config/config.py` with your credentials, convert it to `.env`:

**OLD (config.py):**
```python
TJ_USERNAME = "myusername"
TJ_PASSWORD = "mypassword"
DRY_RUN = True
HEADLESS_MODE = False
```

**NEW (config/.env):**
```bash
TJ_USERNAME=myusername
TJ_PASSWORD=mypassword
DRY_RUN=True
HEADLESS_MODE=False
```

**Note**: No quotes needed in .env files (unless value contains spaces)

### Clean Up (Optional)
```bash
# Remove old config file (already gitignored)
rm config/config.py
rm config/config_template.py
```

## What the System Checks (in order)

1. **config/.env file** - Loads with python-dotenv
2. **Environment variables** - System/shell environment
3. **Command-line flags** - `--tj-username` and `--tj-password`

Command-line flags always override .env settings.

## Example .env File

```bash
# TrafficJunky Credentials
TJ_USERNAME=josh@example.com
TJ_PASSWORD=SecurePassword123!

# Upload Settings
DRY_RUN=True
HEADLESS_MODE=False
TAKE_SCREENSHOTS=True

# Browser Settings
TIMEOUT=30000
SLOW_MO=100

# Logging
LOG_LEVEL=INFO
LOG_TO_CONSOLE=True
LOG_TO_FILE=True
```

## Testing

After creating `.env`, test it:

```bash
source venv/bin/activate
python3 scripts/upload_manager.py --session --verbose
```

You should see: `✓ Loaded configuration from config/.env`

## Questions?

This change makes the Creative Flow upload system consistent with the TJ tool you already use! 🎉

