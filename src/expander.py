"""Text expansion engine for txt-snippets."""

import time
import threading
import subprocess
import sys
from collections import deque
from datetime import datetime
from pynput import keyboard
from pynput.keyboard import Key, Controller

from .library import Library, Snippet
from .utils import is_macos


class Expander:
    """
    Core text expansion engine.

    Monitors keyboard input using a circular buffer and expands
    triggers when detected.
    """

    BUFFER_SIZE = 30  # Max characters to track

    # Dynamic variables
    DYNAMIC_VARS = {
        "$DATE_YYYYMMDD$": lambda: datetime.now().strftime("%Y%m%d"),
        "$DATE_YYYY/MM/DD$": lambda: datetime.now().strftime("%Y/%m/%d"),
        "$DATE_YYYY年M月D日$": lambda: datetime.now().strftime("%Y年%-m月%-d日") if not sys.platform.startswith("win") else datetime.now().strftime("%Y年%#m月%#d日"),
        "$TIME_HHMMSS$": lambda: datetime.now().strftime("%H%M%S"),
        "$TIME_HH:MM:SS$": lambda: datetime.now().strftime("%H:%M:%S"),
        "$DATETIME$": lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    def __init__(self, library: Library):
        self.library = library
        self.buffer: deque[str] = deque(maxlen=self.BUFFER_SIZE)
        self.controller = Controller()
        self.listener: keyboard.Listener | None = None
        self._suppressed = False  # Flag to prevent recursive triggering
        self._running = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the keyboard listener."""
        if self._running:
            return

        self._running = True
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self.listener.start()

    def stop(self) -> None:
        """Stop the keyboard listener."""
        self._running = False
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_press(self, key) -> None:
        """Handle key press events."""
        pass  # We primarily use on_release for character detection

    def _on_release(self, key) -> None:
        """Handle key release events."""
        if self._suppressed:
            return

        # Convert key to character
        char = self._key_to_char(key)
        if char is None:
            # Handle special keys that should clear or modify buffer
            if key == Key.space:
                self.buffer.append(" ")
            elif key == Key.enter or key == Key.tab:
                self.buffer.clear()
            elif key == Key.backspace:
                if self.buffer:
                    self.buffer.pop()
            elif key in (Key.left, Key.right, Key.up, Key.down, Key.home, Key.end):
                # Arrow keys and navigation - clear buffer
                self.buffer.clear()
            return

        # Add character to buffer
        self.buffer.append(char)

        # Check for trigger match
        buffer_str = "".join(self.buffer)
        snippet = self.library.match_suffix(buffer_str)

        if snippet:
            self._expand(snippet)

    def _key_to_char(self, key) -> str | None:
        """Convert a pynput key to a character string."""
        try:
            # Regular characters
            if hasattr(key, "char") and key.char is not None:
                return key.char
        except AttributeError:
            pass
        return None

    def _expand(self, snippet: Snippet) -> None:
        """Execute the text expansion."""
        with self._lock:
            self._suppressed = True
            try:
                # Calculate how many backspaces to send
                trigger_len = len(snippet.trigger)

                # Send backspaces to delete the trigger
                for _ in range(trigger_len):
                    self.controller.press(Key.backspace)
                    self.controller.release(Key.backspace)
                    time.sleep(0.01)  # Small delay for reliability

                time.sleep(0.05)  # Wait before pasting

                # Process and type the replacement
                self._type_replacement(snippet)

                # Clear the buffer after expansion
                self.buffer.clear()

            finally:
                self._suppressed = False

    def _process_dynamic_vars(self, text: str) -> str:
        """Replace dynamic variables in text."""
        result = text
        for var, func in self.DYNAMIC_VARS.items():
            if var in result:
                result = result.replace(var, func())
        return result

    def _type_replacement(self, snippet: Snippet) -> None:
        """Type the replacement text using clipboard for reliability."""
        replacement = snippet.replacement

        # Process dynamic variables
        replacement = self._process_dynamic_vars(replacement)

        # Handle escape sequences - convert to actual characters
        replacement = replacement.replace("\\n", "\n").replace("\\t", "\t")

        # For cursor positioning, split into parts
        if snippet.cursor_position is not None and snippet.cursor_position > 0:
            # Calculate where to split
            split_pos = len(replacement) - snippet.cursor_position
            part_a = replacement[:split_pos]
            part_b = replacement[split_pos:]

            # Paste first part
            self._paste_text(part_a)
            time.sleep(0.05)

            # Paste second part
            self._paste_text(part_b)
            time.sleep(0.05)

            # Move cursor back
            for _ in range(len(part_b)):
                self.controller.press(Key.left)
                self.controller.release(Key.left)
                time.sleep(0.01)
        else:
            # Paste entire text
            self._paste_text(replacement)

    def _paste_text(self, text: str) -> None:
        """Paste text using clipboard (handles Unicode/emoji properly)."""
        if not text:
            return

        try:
            import pyperclip

            # Save current clipboard
            try:
                old_clipboard = pyperclip.paste()
            except Exception:
                old_clipboard = ""

            # Set new text and paste
            pyperclip.copy(text)
            time.sleep(0.02)

            # Paste using Cmd+V (macOS) or Ctrl+V (Windows/Linux)
            if is_macos():
                self.controller.press(Key.cmd)
                self.controller.press("v")
                self.controller.release("v")
                self.controller.release(Key.cmd)
            else:
                self.controller.press(Key.ctrl)
                self.controller.press("v")
                self.controller.release("v")
                self.controller.release(Key.ctrl)

            time.sleep(0.05)

            # Restore old clipboard
            try:
                pyperclip.copy(old_clipboard)
            except Exception:
                pass

        except ImportError:
            # Fallback to direct typing if pyperclip not available
            self.controller.type(text)

    def reload_library(self) -> None:
        """Reload the snippet library."""
        self.library.reload()
        self.buffer.clear()
