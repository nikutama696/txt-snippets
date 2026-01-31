"""Snippet library parser for txt-snippets."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Snippet:
    """Represents a single snippet entry."""

    trigger: str
    replacement: str
    cursor_position: int | None = None  # Position from end where cursor should be

    def __post_init__(self):
        """Parse special tags in the replacement."""
        # Check for $CURSOR$ tag
        if "$CURSOR$" in self.replacement:
            parts = self.replacement.split("$CURSOR$", 1)
            self.replacement = parts[0] + parts[1]
            # cursor_position is how many characters from the end
            self.cursor_position = len(parts[1])


class Library:
    """Manages the snippet library loaded from a .txt file."""

    DELIMITER = "::"

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.snippets: dict[str, Snippet] = {}
        if self.path and self.path.exists():
            self.load()

    def load(self) -> None:
        """Load snippets from the library file."""
        if not self.path or not self.path.exists():
            return

        self.snippets.clear()

        with open(self.path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Skip empty lines and comments

                if self.DELIMITER not in line:
                    continue  # Skip invalid lines

                parts = line.split(self.DELIMITER, 1)
                if len(parts) != 2:
                    continue

                trigger, replacement = parts
                trigger = trigger.strip()
                replacement = replacement.strip()

                if trigger and replacement:
                    self.snippets[trigger] = Snippet(trigger=trigger, replacement=replacement)

    def reload(self) -> None:
        """Reload snippets from the library file."""
        self.load()

    def set_path(self, path: str | Path) -> None:
        """Set a new library path and reload."""
        self.path = Path(path)
        self.load()

    def get(self, trigger: str) -> Snippet | None:
        """Get a snippet by its trigger."""
        return self.snippets.get(trigger)

    def match_suffix(self, buffer: str) -> Snippet | None:
        """Find a snippet whose trigger matches the end of the buffer."""
        for trigger, snippet in self.snippets.items():
            if buffer.endswith(trigger):
                return snippet
        return None

    @property
    def triggers(self) -> list[str]:
        """Get all registered triggers."""
        return list(self.snippets.keys())
