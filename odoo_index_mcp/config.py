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
# Resolve SQLITE_DB_PATH relative to this config file's directory (project root/odoo_index_mcp/)
_default_db_path = Path(__file__).parent / 'odoo_index.db'
SQLITE_DB_PATH = Path(os.getenv('SQLITE_DB_PATH', str(_default_db_path)))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MAX_CONCURRENT_MODULES = int(os.getenv('MAX_CONCURRENT_MODULES', '4'))
MAX_WORKER_PROCESSES = int(os.getenv('MAX_WORKER_PROCESSES', '0'))  # 0 = use CPU count
