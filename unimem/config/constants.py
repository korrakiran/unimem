"""Constants used across the Unimem application."""

import os

# Project Local Directory Name
MEM_DIR_NAME = ".unimem"

# Subfolders under .unimem/
EVENTS_DIR_NAME = "events"
SESSIONS_DIR_NAME = "sessions"
SNAPSHOTS_DIR_NAME = "snapshots"
DECISIONS_DIR_NAME = "decisions"

# State and Memory Document Files
STATE_FILE_NAME = "state.json"
MEMORY_MD_NAME = "memory.md"

# Global Config File Name
CONFIG_FILE_NAME = "config.yaml"

# Default settings
DEFAULT_WATCH_ENABLED = True
DEFAULT_AUTO_SNAPSHOT = True
DEFAULT_SUMMARIZER = "local"
