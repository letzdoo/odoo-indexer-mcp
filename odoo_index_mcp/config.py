"""Configuration management for Odoo Index MCP."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Required settings
ODOO_PATH = Path(os.getenv('ODOO_PATH', ''))
if not ODOO_PATH or not ODOO_PATH.exists():
    raise ValueError(
        "ODOO_PATH must be set in environment and must exist. "
        "Please create a .env file with ODOO_PATH=/path/to/odoo"
    )

# Optional settings
SQLITE_DB_PATH = Path(os.getenv('SQLITE_DB_PATH', './odoo_index.db'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MAX_CONCURRENT_MODULES = int(os.getenv('MAX_CONCURRENT_MODULES', '4'))
MAX_WORKER_PROCESSES = int(os.getenv('MAX_WORKER_PROCESSES', '0'))  # 0 = use CPU count
