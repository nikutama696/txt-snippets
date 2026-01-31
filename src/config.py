"""Configuration management for txt-snippets."""

import json
import os
from pathlib import Path


class Config:
    """Manages application configuration stored in config.json."""

    DEFAULT_CONFIG = {
        "library_path": "",
        "launch_at_login": False,
    }

    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            # Default to user's home directory
            config_dir = Path.home() / ".txt-snippets"
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self._config = self._load()

    def _load(self) -> dict:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle missing keys
                    return {**self.DEFAULT_CONFIG, **loaded}
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    @property
    def library_path(self) -> str:
        """Get the path to the snippet library file."""
        return self._config.get("library_path", "")

    @library_path.setter
    def library_path(self, value: str) -> None:
        """Set the path to the snippet library file."""
        self._config["library_path"] = value
        self.save()

    @property
    def launch_at_login(self) -> bool:
        """Get the launch at login setting."""
        return self._config.get("launch_at_login", False)

    @launch_at_login.setter
    def launch_at_login(self, value: bool) -> None:
        """Set the launch at login setting."""
        self._config["launch_at_login"] = value
        self.save()
