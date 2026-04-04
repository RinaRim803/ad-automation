"""
config.py

Central config loader for the AD Automation project.
All modules import from here instead of hardcoding paths or values.

Real-world equivalent:
    Azure AD / M365 admin settings, Group Policy, or environment config
    managed centrally and referenced across automation scripts.

Usage:
    from config import cfg, ROOT_DIR
    db_path = ROOT_DIR / cfg["database"]["path"]

    # Path to database file
    DB_PATH = ROOT_DIR / cfg["database"]["path"]

    # Settings for stale account detection
    STALE_DAYS = cfg["accounts"]["stale_threshold_days"]  # 90 days

    # Mapping of departments to groups
    dept_map = cfg["groups"]["department_group_map"]
    group = dept_map.get("Sales")  # "Sales-Team"
"""

import json
import os
from pathlib import Path

# Project root = directory that contains this file
ROOT_DIR = Path(__file__).parent.resolve()

_CONFIG_PATH = ROOT_DIR / "config.json"


def _load_config() -> dict:
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(f"[Config] config.json not found at {_CONFIG_PATH}")
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


cfg = _load_config()