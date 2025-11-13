"""
DEPRECATED: This file is no longer used.

We've switched to .env files (like the TJ tool uses).

Instead of this file, use:
1. Copy config/env_template.txt to config/.env
2. Edit config/.env with your credentials

See config/MIGRATION_TO_DOTENV.md for details.
"""

# TrafficJunky Credentials
TJ_USERNAME = "your_username_here"
TJ_PASSWORD = "your_password_here"

# Upload Settings
DRY_RUN = True                    # Set to False for live uploads
HEADLESS_MODE = False             # Set to True to hide browser window
TAKE_SCREENSHOTS = True           # Set to False to disable screenshots

# Browser Settings
TIMEOUT = 30000                   # Page load timeout in milliseconds
SLOW_MO = 100                     # Delay between actions in milliseconds (0 for no delay)

# Logging
LOG_LEVEL = "INFO"                # DEBUG, INFO, WARNING, ERROR
LOG_TO_CONSOLE = True
LOG_TO_FILE = True

