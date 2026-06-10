"""Global settings loading and saving using platform-specific directories."""

import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field
from platformdirs import user_config_dir

from unimem.config.constants import (
    CONFIG_FILE_NAME,
    DEFAULT_SUMMARIZER,
    DEFAULT_WATCH_ENABLED,
    DEFAULT_AUTO_SNAPSHOT,
)

class Settings(BaseModel):
    """Global configuration settings for Unimem."""
    default_summarizer: str = Field(default=DEFAULT_SUMMARIZER, description="The default summarization engine to use.")
    watch_enabled: bool = Field(default=DEFAULT_WATCH_ENABLED, description="Whether the file watcher is enabled by default.")
    auto_snapshot: bool = Field(default=DEFAULT_AUTO_SNAPSHOT, description="Whether to take snapshots automatically on events.")

def get_global_config_dir() -> Path:
    """Get the platform-specific global configuration directory."""
    return Path(user_config_dir("unimem", appauthor=False))

def get_global_config_path() -> Path:
    """Get the path to the global configuration file."""
    return get_global_config_dir() / CONFIG_FILE_NAME

def load_settings() -> Settings:
    """Load settings from the global config file, or return defaults if not present."""
    config_path = get_global_config_path()
    if not config_path.exists():
        return Settings()
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return Settings(**data)
    except Exception:
        # Fallback to default if there is a parsing error
        return Settings()

def save_settings(settings: Settings) -> None:
    """Save the settings to the global configuration file."""
    config_path = get_global_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # We serialize using pydantic
    data = settings.model_dump()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
    except Exception as e:
        raise IOError(f"Failed to save settings: {e}") from e
