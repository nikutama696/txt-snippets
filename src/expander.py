"""Text expansion engine for txt-snippets."""

import time
import sys
import platform
import subprocess
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

    @staticmethod
    def _has_non_bmp(text: str) -> bool:
        """Check if text contains non-BMP characters (emojis etc.)."""
        return any(ord(ch) > 0xFFFF for ch in text)

    @staticmethod
    def _split_bmp_segments(text: str) -> list[tuple[bool, str]]:
        """
        Split text into segments of (is_bmp, substring).
        Groups consecutive BMP chars together, and consecutive non-BMP chars together.
        """
        if not text:
            return []
        segments: list[tuple[bool, str]] = []
        current_is_bmp = ord(text[0]) <= 0xFFFF
        current_chars = [text[0]]
        for ch in text[1:]:
            ch_is_bmp = ord(ch) <= 0xFFFF
            if ch_is_bmp == current_is_bmp:
                current_chars.append(ch)
            else:
                segments.append((current_is_bmp, "".join(current_chars)))
                current_is_bmp = ch_is_bmp
                current_chars = [ch]
        segments.append((current_is_bmp, "".join(current_chars)))
        return segments

    def _cg_type_text(self, text: str) -> None:
        """
        Type text using CoreGraphics CGEvent API (macOS only).
        Handles all Unicode characters including emojis by directly
        creating keyboard events with UTF-16 encoded strings.
        """
        import ctypes
        import ctypes.util

        # Load CoreGraphics framework
        cg_path = ctypes.util.find_library("CoreGraphics")
        cg = ctypes.cdll.LoadLibrary(cg_path)

        cf_path = ctypes.util.find_library("CoreFoundation")
        cf = ctypes.cdll.LoadLibrary(cf_path)

        # Set return types
        cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
        cg.CGEventCreateKeyboardEvent.argtypes = [
            ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool
        ]
        cg.CGEventKeyboardSetUnicodeString.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p
        ]
        cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        cf.CFRelease.argtypes = [ctypes.c_void_p]

        kCGHIDEventTap = 0

        # Encode text as UTF-16LE (UniChar array)
        utf16_bytes = text.encode("utf-16-le")
        utf16_len = len(utf16_bytes) // 2
        UniCharArray = ctypes.c_uint16 * utf16_len
        buf = UniCharArray(*[
            int.from_bytes(utf16_bytes[i:i + 2], "little")
            for i in range(0, len(utf16_bytes), 2)
        ])

        # Key down event
        event_down = cg.CGEventCreateKeyboardEvent(None, 0, True)
        cg.CGEventKeyboardSetUnicodeString(event_down, utf16_len, buf)
        cg.CGEventPost(kCGHIDEventTap, event_down)

        time.sleep(0.02)

        # Key up event
        event_up = cg.CGEventCreateKeyboardEvent(None, 0, False)
        cg.CGEventKeyboardSetUnicodeString(event_up, utf16_len, buf)
        cg.CGEventPost(kCGHIDEventTap, event_up)

        # Release CF objects
        cf.CFRelease(event_down)
        cf.CFRelease(event_up)

        time.sleep(0.02)

    def _type_unicode(self, text: str) -> None:
        """
        Output text without using the clipboard.
        On macOS: uses controller.type() for BMP chars,
                  CoreGraphics CGEvent API for non-BMP (emojis).
        On Windows/Linux: uses controller.type() for everything.
        """
        if not text:
            return

        is_mac = platform.system() == "Darwin"

        # Fast path: no non-BMP characters, or not on macOS
        if not is_mac or not self._has_non_bmp(text):
            self.controller.type(text)
            time.sleep(0.01 * len(text))
            return

        # macOS with emojis: split into BMP and non-BMP segments
        for is_bmp, segment in self._split_bmp_segments(text):
            if is_bmp:
                self.controller.type(segment)
                time.sleep(0.01 * len(segment))
            else:
                self._cg_type_text(segment)
                time.sleep(0.05)

    def _paste_text(self, text: str) -> None:
        """Output text using the clipboard-free injection method."""
        if not text:
            return

        # Use the new direct typing logic
        self._type_unicode(text)

        # Still use a small delay and cooldown logic to maintain expander stability
        time.sleep(0.05)

    def reload_library(self) -> None:
        """Reload the snippet library (waits if expansion is in progress)."""
        while self._expanding:
            time.sleep(0.1)
        self.library.reload()
        self.buffer.clear()
