#!/usr/bin/env python3
"""
txt-snippets - A cross-platform text expansion tool.

Main entry point for the application.
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path

# Add src to path for relative imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.library import Library
from src.expander import Expander
from src.ui import TrayApp


class FileWatcher:
    """Watches a file for changes and triggers a callback on modification."""

    def __init__(self, callback, interval: float = 2.0):
        self.callback = callback
        self.interval = interval
        self._path: str | None = None
        self._last_mtime: float = 0
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self, path: str) -> None:
        """Start watching the specified file."""
        self._path = path
        self._last_mtime = self._get_mtime()
        self._running = True
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop watching."""
        self._running = False

    def update_path(self, path: str) -> None:
        """Update the watched file path."""
        self._path = path
        self._last_mtime = self._get_mtime()

    def _get_mtime(self) -> float:
        """Get the file's last modification time."""
        try:
            if self._path and os.path.exists(self._path):
                return os.path.getmtime(self._path)
        except OSError:
            pass
        return 0

    def _watch(self) -> None:
        """Watch loop running in background thread."""
        while self._running:
            time.sleep(self.interval)
            if not self._path:
                continue
            current_mtime = self._get_mtime()
            if current_mtime > self._last_mtime:
                self._last_mtime = current_mtime
                print(f"[Auto-Reload] File changed: {self._path}")
                self.callback()


class Application:
    """Main application controller."""

    def __init__(self):
        self.config = Config()
        self.library = Library()
        self.expander: Expander | None = None
        self.tray: TrayApp | None = None
        self.watcher = FileWatcher(callback=self._on_reload)

        # Load library if path is configured
        self._load_library()

    def _load_library(self) -> None:
        """Load the snippet library from configured path."""
        path = self.config.library_path
        if path and Path(path).exists():
            self.library.set_path(path)
            print(f"Loaded {len(self.library.snippets)} snippets from {path}")
        else:
            print("No library file configured or file does not exist.")

    def _on_reload(self) -> None:
        """Handle reload request (thread-safe)."""
        self._load_library()
        if self.expander:
            self.expander.reload_library()
        print(f"Reloaded {len(self.library.snippets)} snippets.")

    def _on_restart(self) -> None:
        """Restart the application by spawning a new process."""
        print("Restarting...")
        # Spawn a new process
        subprocess.Popen(
            [sys.executable] + sys.argv,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        # Clean up and exit current process
        self._on_exit()

    def _on_exit(self) -> None:
        """Handle exit request."""
        print("Exiting...")
        self.watcher.stop()
        if self.expander:
            self.expander.stop()
        if self.tray:
            self.tray.stop()

    def run(self) -> None:
        """Run the application."""
        print("Starting txt-snippets...")

        # Initialize and start the expander
        self.expander = Expander(self.library)
        self.expander.start()
        print("Keyboard listener started.")

        # Start file watcher
        if self.config.library_path:
            self.watcher.start(self.config.library_path)
            print("File watcher started (auto-reload on save).")

        # Run the tray app (this blocks)
        self.tray = TrayApp(
            config=self.config,
            on_reload=self._on_reload,
            on_restart=self._on_restart,
            on_exit=self._on_exit,
        )

        try:
            self.tray.run()
        except KeyboardInterrupt:
            pass
        finally:
            self.watcher.stop()
            if self.expander:
                self.expander.stop()
            print("txt-snippets stopped.")


def main():
    """Entry point."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
