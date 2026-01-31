#!/usr/bin/env python3
"""
txt-snippets - A cross-platform text expansion tool.

Main entry point for the application.
"""

import sys
from pathlib import Path

# Add src to path for relative imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.library import Library
from src.expander import Expander
from src.ui import TrayApp


class Application:
    """Main application controller."""

    def __init__(self):
        self.config = Config()
        self.library = Library()
        self.expander: Expander | None = None
        self.tray: TrayApp | None = None

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
        """Handle reload request."""
        print("Reloading library...")
        self._load_library()
        if self.expander:
            self.expander.library = self.library
            self.expander.reload_library()
        print(f"Reloaded {len(self.library.snippets)} snippets.")

    def _on_exit(self) -> None:
        """Handle exit request."""
        print("Exiting...")
        if self.expander:
            self.expander.stop()

    def run(self) -> None:
        """Run the application."""
        print("Starting txt-snippets...")

        # Initialize and start the expander
        self.expander = Expander(self.library)
        self.expander.start()
        print("Keyboard listener started.")

        # Run the tray app (this blocks)
        self.tray = TrayApp(
            config=self.config,
            on_reload=self._on_reload,
            on_exit=self._on_exit,
        )

        try:
            self.tray.run()
        except KeyboardInterrupt:
            pass
        finally:
            if self.expander:
                self.expander.stop()
            print("txt-snippets stopped.")


def main():
    """Entry point."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
