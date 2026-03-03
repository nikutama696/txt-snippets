"""Text expansion engine for txt-snippets."""

import time
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
    COOLDOWN_SECONDS = 0.3  # Ignore key events for this long after expansion

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
        self._suppressed = False
        self._last_expand_time: float = 0  # Cooldown timer
        self._running = False
        self._expanding = False

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
        pass

    def _on_release(self, key) -> None:
        """Handle key release events."""
        if self._suppressed:
            return

        # Ignore events during cooldown period after expansion
        if time.time() - self._last_expand_time < self.COOLDOWN_SECONDS:
            return

        # Convert key to character
        char = self._key_to_char(key)
        if char is None:
            if key == Key.space:
                self.buffer.append(" ")
            elif key == Key.enter or key == Key.tab:
                self.buffer.clear()
            elif key == Key.backspace:
                if self.buffer:
                    self.buffer.pop()
            elif key in (Key.left, Key.right, Key.up, Key.down,
                         Key.home, Key.end, Key.cmd, Key.cmd_r,
                         Key.ctrl, Key.ctrl_r, Key.alt, Key.alt_r,
                         Key.shift, Key.shift_r):
                # Modifier keys and navigation - clear buffer
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
            if hasattr(key, "char") and key.char is not None:
                return key.char
        except AttributeError:
            pass
        return None

    def _expand(self, snippet: Snippet) -> None:
        """Execute the text expansion."""
        self._suppressed = True
        self._expanding = True
        try:
            trigger_len = len(snippet.trigger)

            # Delete the trigger
            for _ in range(trigger_len):
                self.controller.press(Key.backspace)
                self.controller.release(Key.backspace)
                time.sleep(0.01)

            time.sleep(0.05)

            # Paste the replacement
            self._type_replacement(snippet)

            # Clear buffer
            self.buffer.clear()

        finally:
            self._expanding = False
            self._suppressed = False
            # Set cooldown timer to ignore residual key events
            self._last_expand_time = time.time()

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

        # Handle escape sequences
        replacement = replacement.replace("\\n", "\n").replace("\\t", "\t")

        # For cursor positioning, split into parts
        if snippet.cursor_position is not None and snippet.cursor_position > 0:
            split_pos = len(replacement) - snippet.cursor_position
            part_a = replacement[:split_pos]
            part_b = replacement[split_pos:]

            self._paste_text(part_a)
            time.sleep(0.05)
            self._paste_text(part_b)
            time.sleep(0.05)

            # Move cursor back
            for _ in range(len(part_b)):
                self.controller.press(Key.left)
                self.controller.release(Key.left)
                time.sleep(0.01)
        else:
            self._paste_text(replacement)

    def _paste_text(self, text: str) -> None:
        """Paste text using clipboard (handles Unicode/emoji properly)."""
        if not text:
            return

        try:
            import pyperclip
            pyperclip.copy(text)
            time.sleep(0.05)

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

            time.sleep(0.1)
        except ImportError:
            self.controller.type(text)

    def reload_library(self) -> None:
        """Reload the snippet library (waits if expansion is in progress)."""
        while self._expanding:
            time.sleep(0.1)
        self.library.reload()
        self.buffer.clear()
